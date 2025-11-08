package auth

import (
    "bufio"
    "context"
    "fmt"
    "net/http"
    "os"
    "strings"
    "time"

    "evalarena-cli/internal/config"
    "evalarena-cli/internal/httpclient"
)

// GetAuthHeader returns the Authorization header map if a token exists.
func GetAuthHeader() http.Header {
    cfg := config.Load()
    h := http.Header{}
    if strings.TrimSpace(cfg.Token) != "" {
        h.Set("Authorization", "Bearer "+cfg.Token)
    }
    return h
}

// Login prompts user to enter a token, validates it against the API, and saves it to .env
func Login() error {
    fmt.Println("\nEvalArena CLI Authentication")
    fmt.Println("Enter your EvalArena API token. Get one from: https://evalarena.ai/account/api-keys")
    fmt.Println()

    reader := bufio.NewReader(os.Stdin)
    fmt.Print("API Token (input hidden not supported here, paste carefully): ")
    token, _ := reader.ReadString('\n')
    token = strings.TrimSpace(token)
    if token == "" {
        return fmt.Errorf("no token provided")
    }

    // Validate token
    fmt.Println("Validating token...")
    ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
    defer cancel()
    client := httpclient.New()
    status, err := client.GetStatus(ctx, "/api/models/?limit=1", httpclient.WithHeader("Authorization", "Bearer "+token))
    if err != nil {
        return fmt.Errorf("failed to validate token: %w", err)
    }
    if status == 401 || status == 403 {
        return fmt.Errorf("invalid token or insufficient permissions (HTTP %d)", status)
    }
    if status < 200 || status >= 300 {
        return fmt.Errorf("unexpected status from API: %d", status)
    }

    if err := config.SaveEnv("EVALARENA_TOKEN", token); err != nil {
        return fmt.Errorf("failed to store token in .env: %w", err)
    }
    fmt.Println("✓ Token saved to .env")
    return nil
}

// Logout removes token from .env
func Logout() error {
    if err := config.RemoveEnv("EVALARENA_TOKEN"); err != nil {
        return err
    }
    fmt.Println("✓ Logged out (token removed from .env)")
    return nil
}


