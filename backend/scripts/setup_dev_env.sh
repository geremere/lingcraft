#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENV_FILE="${BACKEND_DIR}/.env"
ENV_EXAMPLE_FILE="${BACKEND_DIR}/.env.example"
MIGRATIONS_DIR="${BACKEND_DIR}/migrations"
COMPOSE_FILE="${BACKEND_DIR}/docker-compose.dev.yml"

log() {
  printf '[setup-dev-env] %s\n' "$1"
}

if [[ -f "${ENV_FILE}" ]]; then
  log "loading env from ${ENV_FILE}"
  set -a
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
  set +a
elif [[ -f "${ENV_EXAMPLE_FILE}" ]]; then
  log "no .env found, loading defaults from ${ENV_EXAMPLE_FILE}"
  set -a
  # shellcheck disable=SC1090
  source "${ENV_EXAMPLE_FILE}"
  set +a
else
  log "missing .env and .env.example"
  exit 1
fi

DB_HOST="${DB_HOST:-127.0.0.1}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-lingraft_dev}"
DB_USER="${DB_USER:-postgres}"
DB_PASSWORD="${DB_PASSWORD:-postgres}"

# Admin credentials can differ from application credentials.
DB_ADMIN_USER="${DB_ADMIN_USER:-postgres}"
DB_ADMIN_PASSWORD="${DB_ADMIN_PASSWORD:-${DB_PASSWORD}}"

AUTO_DOCKER_UP="${AUTO_DOCKER_UP:-true}"

if ! command -v psql >/dev/null 2>&1; then
  log "psql is required. Install PostgreSQL client tools."
  exit 1
fi

if [[ ! -d "${MIGRATIONS_DIR}" ]]; then
  log "migrations directory not found: ${MIGRATIONS_DIR}"
  exit 1
fi

check_connection() {
  PGPASSWORD="${DB_ADMIN_PASSWORD}" psql \
    -h "${DB_HOST}" \
    -p "${DB_PORT}" \
    -U "${DB_ADMIN_USER}" \
    -d postgres \
    -v ON_ERROR_STOP=1 \
    -tAc "SELECT 1" >/dev/null
}

maybe_start_docker() {
  if [[ "${AUTO_DOCKER_UP}" != "true" ]]; then
    return 1
  fi

  if [[ ! -f "${COMPOSE_FILE}" ]]; then
    return 1
  fi

  if ! command -v docker >/dev/null 2>&1; then
    return 1
  fi

  log "database is unavailable, attempting docker compose startup"
  docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" up -d
}

if ! check_connection; then
  maybe_start_docker || true
fi

if ! check_connection; then
  log "cannot connect to postgres at ${DB_HOST}:${DB_PORT} as ${DB_ADMIN_USER}"
  log "start postgres locally or docker daemon, then rerun this script"
  exit 1
fi

log "creating/updating database role ${DB_USER}"
PGPASSWORD="${DB_ADMIN_PASSWORD}" psql \
  -h "${DB_HOST}" \
  -p "${DB_PORT}" \
  -U "${DB_ADMIN_USER}" \
  -d postgres \
  -v ON_ERROR_STOP=1 <<SQL
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '${DB_USER}') THEN
    CREATE ROLE "${DB_USER}" LOGIN PASSWORD '${DB_PASSWORD}';
  ELSE
    ALTER ROLE "${DB_USER}" WITH LOGIN PASSWORD '${DB_PASSWORD}';
  END IF;
END
\$\$;
SQL

log "creating database ${DB_NAME} if needed"
PGPASSWORD="${DB_ADMIN_PASSWORD}" psql \
  -h "${DB_HOST}" \
  -p "${DB_PORT}" \
  -U "${DB_ADMIN_USER}" \
  -d postgres \
  -v ON_ERROR_STOP=1 <<SQL
SELECT format('CREATE DATABASE %I OWNER %I', '${DB_NAME}', '${DB_USER}')
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = '${DB_NAME}');
\gexec
SQL

log "ensuring migration tracking table"
PGPASSWORD="${DB_PASSWORD}" psql \
  -h "${DB_HOST}" \
  -p "${DB_PORT}" \
  -U "${DB_USER}" \
  -d "${DB_NAME}" \
  -v ON_ERROR_STOP=1 \
  -c "CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW());"

shopt -s nullglob
migration_files=("${MIGRATIONS_DIR}"/*.up.sql)
shopt -u nullglob

if [[ ${#migration_files[@]} -eq 0 ]]; then
  log "no .up.sql migrations found in ${MIGRATIONS_DIR}"
  exit 1
fi

IFS=$'\n' migration_files=($(printf '%s\n' "${migration_files[@]}" | sort))
unset IFS

for migration_file in "${migration_files[@]}"; do
  version="$(basename "${migration_file}")"
  applied="$(
    PGPASSWORD="${DB_PASSWORD}" psql \
      -h "${DB_HOST}" \
      -p "${DB_PORT}" \
      -U "${DB_USER}" \
      -d "${DB_NAME}" \
      -tAc "SELECT 1 FROM schema_migrations WHERE version = '${version}' LIMIT 1;"
  )"

  if [[ "${applied}" == "1" ]]; then
    log "skip ${version} (already applied)"
    continue
  fi

  log "applying ${version}"
  PGPASSWORD="${DB_PASSWORD}" psql \
    -h "${DB_HOST}" \
    -p "${DB_PORT}" \
    -U "${DB_USER}" \
    -d "${DB_NAME}" \
    -v ON_ERROR_STOP=1 \
    -f "${migration_file}"

  PGPASSWORD="${DB_PASSWORD}" psql \
    -h "${DB_HOST}" \
    -p "${DB_PORT}" \
    -U "${DB_USER}" \
    -d "${DB_NAME}" \
    -v ON_ERROR_STOP=1 \
    -c "INSERT INTO schema_migrations (version) VALUES ('${version}');"
done

log "done: database is ready and migrations are applied"
