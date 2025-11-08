package cmd

import (
    "fmt"
    "strings"

    "github.com/spf13/cobra"

    "evalarena-cli/internal/config"
)

func init() {
    cfgCmd := &cobra.Command{Use: "config", Short: "Configuration management"}

    showCmd := &cobra.Command{
        Use:   "show",
        Short: "Show current configuration",
        Run: func(cmd *cobra.Command, args []string) {
            cfg := config.Load()
            fmt.Println("EvalArena CLI Configuration")
            fmt.Println()
            fmt.Printf("Base URL: %s\n", cfg.BaseURL)
            fmt.Printf("Timeout: %ds\n", cfg.TimeoutSeconds)
            fmt.Printf("Output Format: %s\n", cfg.OutputFormat)
            fmt.Printf("No Color: %t\n", cfg.NoColor)
            fmt.Printf("Cache Enabled: %t\n", cfg.CacheEnabled)
            fmt.Printf("Cache TTL: %ds\n", cfg.CacheTTLSeconds)
            fmt.Println()
            fmt.Printf("Default Columns: %s\n", strings.Join(cfg.DefaultColumns, ", "))
            fmt.Println()
            fmt.Println("Chart Settings")
            fmt.Printf("Width: %d\n", cfg.Chart.Width)
            fmt.Printf("Height: %d\n", cfg.Chart.Height)
            fmt.Printf("Normalize: %s\n", cfg.Chart.Normalize)
            fmt.Println()
            fmt.Println("Chat Settings")
            fmt.Printf("Default Models: %s\n", strings.Join(cfg.Chat.DefaultModels, ", "))
        },
    }

    setCmd := &cobra.Command{
        Use:   "set <key> <value>",
        Short: "Set configuration value (writes to .env)",
        Args:  cobra.ExactArgs(2),
        RunE: func(cmd *cobra.Command, args []string) error {
            key := args[0]
            value := args[1]
            // map friendly keys to env keys
            envKey := toEnvKey(key)
            if err := config.SaveEnv(envKey, value); err != nil { return err }
            fmt.Printf("Set %s=%s\n", envKey, value)
            return nil
        },
    }

    cfgCmd.AddCommand(showCmd, setCmd)
    RegisterCommand(cfgCmd)
}

func toEnvKey(k string) string {
    m := map[string]string{
        "base_url": "EVALARENA_BASE_URL",
        "output_format": "EVALARENA_OUTPUT_FORMAT",
        "timeout_s": "EVALARENA_TIMEOUT_S",
        "default_columns": "EVALARENA_DEFAULT_COLUMNS",
        "chart.width": "EVALARENA_CHART_WIDTH",
        "chart.height": "EVALARENA_CHART_HEIGHT",
        "chart.normalize": "EVALARENA_CHART_NORMALIZE",
        "cache.enabled": "EVALARENA_CACHE_ENABLED",
        "cache.ttl": "EVALARENA_CACHE_TTL_SECONDS",
        "chat.default_models": "EVALARENA_CHAT_DEFAULT_MODELS",
        "token": "EVALARENA_TOKEN",
    }
    if v, ok := m[strings.ToLower(k)]; ok { return v }
    if strings.HasPrefix(k, "EVALARENA_") { return k }
    // fallback to uppercase env style
    return "EVALARENA_" + strings.ToUpper(strings.ReplaceAll(k, ".", "_"))
}



