# Backend Environment Setup

## Local development

1. Copy env template:
   - `cp .env.example .env`
2. Update local DB values in `.env` if needed.
3. Bootstrap DB + run migrations:
   - `bash scripts/setup_dev_env.sh`
4. Run backend:
   - `go run ./cmd/server`

In development, the server tries to read `.env` automatically.
The setup script can start docker postgres automatically when `AUTO_DOCKER_UP=true`.

## Production

Do not use `.env` files in production. Pass environment variables from the runtime:

```bash
APP_ENV=production \
HTTP_PORT=8080 \
DB_HOST=127.0.0.1 \
DB_PORT=5432 \
DB_NAME=lingraft \
DB_USER=lingraft \
DB_PASSWORD=secret \
DB_SSLMODE=require \
./server-binary
```

## Environment variables

- `APP_ENV` (default: `development`)
- `HTTP_PORT` (default: `8080`)
- `DB_HOST` (default: `127.0.0.1`)
- `DB_PORT` (default: `5432`)
- `DB_NAME` (default: `lingraft_dev`)
- `DB_USER` (default: `postgres`)
- `DB_PASSWORD` (default: `postgres`)
- `DB_SSLMODE` (default: `disable`)
