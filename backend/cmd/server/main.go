package main

import (
	"fmt"
	"log"
	"net/http"

	"lingraft/backend/internal/config"
)

func healthHandler(w http.ResponseWriter, _ *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	_, _ = w.Write([]byte(`{"status":"ok"}`))
}

func main() {
	cfg, err := config.Load(".env")
	if err != nil {
		log.Fatalf("config load failed: %v", err)
	}

	mux := http.NewServeMux()
	mux.HandleFunc("/health", healthHandler)

	server := &http.Server{
		Addr:    fmt.Sprintf(":%d", cfg.HTTPPort),
		Handler: mux,
	}

	log.Printf(
		"backend listening on http://localhost:%d (env=%s, db=%s:%d/%s)",
		cfg.HTTPPort,
		cfg.AppEnv,
		cfg.DB.Host,
		cfg.DB.Port,
		cfg.DB.Name,
	)
	if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		log.Fatalf("server failed: %v", err)
	}
}
