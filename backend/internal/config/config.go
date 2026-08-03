package config

import (
	"bufio"
	"errors"
	"fmt"
	"os"
	"strconv"
	"strings"
)

// Config contains runtime settings from environment variables.
type Config struct {
	AppEnv   string
	HTTPPort int
	DB       DBConfig
}

// DBConfig contains database connection settings.
type DBConfig struct {
	Host     string
	Port     int
	Name     string
	User     string
	Password string
	SSLMode  string
}

// Load returns app configuration. For local development it can read a .env file.
func Load(dotenvPath string) (Config, error) {
	if err := loadDotEnvIfLocal(dotenvPath); err != nil {
		return Config{}, err
	}

	httpPort, err := readIntEnv("HTTP_PORT", 8080)
	if err != nil {
		return Config{}, err
	}

	dbPort, err := readIntEnv("DB_PORT", 5432)
	if err != nil {
		return Config{}, err
	}

	cfg := Config{
		AppEnv:   readStringEnv("APP_ENV", "development"),
		HTTPPort: httpPort,
		DB: DBConfig{
			Host:     readStringEnv("DB_HOST", "127.0.0.1"),
			Port:     dbPort,
			Name:     readStringEnv("DB_NAME", "lingraft_dev"),
			User:     readStringEnv("DB_USER", "postgres"),
			Password: readStringEnv("DB_PASSWORD", "postgres"),
			SSLMode:  readStringEnv("DB_SSLMODE", "disable"),
		},
	}

	return cfg, nil
}

func (d DBConfig) DSN() string {
	return fmt.Sprintf(
		"host=%s port=%d dbname=%s user=%s password=%s sslmode=%s",
		d.Host,
		d.Port,
		d.Name,
		d.User,
		d.Password,
		d.SSLMode,
	)
}

func loadDotEnvIfLocal(path string) error {
	appEnv := strings.ToLower(strings.TrimSpace(os.Getenv("APP_ENV")))
	if appEnv == "production" || appEnv == "prod" {
		return nil
	}

	f, err := os.Open(path)
	if err != nil {
		if errors.Is(err, os.ErrNotExist) {
			return nil
		}
		return fmt.Errorf("open .env: %w", err)
	}
	defer f.Close()

	scanner := bufio.NewScanner(f)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}

		key, value, ok := strings.Cut(line, "=")
		if !ok {
			continue
		}

		key = strings.TrimSpace(key)
		value = strings.TrimSpace(value)
		value = strings.Trim(value, `"'`)
		if key == "" {
			continue
		}

		// Existing process env vars have higher priority.
		if _, exists := os.LookupEnv(key); !exists {
			_ = os.Setenv(key, value)
		}
	}

	if err := scanner.Err(); err != nil {
		return fmt.Errorf("scan .env: %w", err)
	}

	return nil
}

func readStringEnv(key, fallback string) string {
	value := strings.TrimSpace(os.Getenv(key))
	if value == "" {
		return fallback
	}
	return value
}

func readIntEnv(key string, fallback int) (int, error) {
	value := strings.TrimSpace(os.Getenv(key))
	if value == "" {
		return fallback, nil
	}

	n, err := strconv.Atoi(value)
	if err != nil {
		return 0, fmt.Errorf("%s must be integer: %w", key, err)
	}
	return n, nil
}
