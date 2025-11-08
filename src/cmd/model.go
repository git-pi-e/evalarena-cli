package cmd

import (
    "context"
    "fmt"
    "strings"
    "time"

    "github.com/spf13/cobra"

    "evalarena-cli/internal/config"
    "evalarena-cli/internal/dataaccess"
    "evalarena-cli/internal/httpclient"
    "evalarena-cli/internal/models"
    "evalarena-cli/internal/printing"
)

func init() {
    modelCmd := &cobra.Command{Use: "model", Short: "Show model details"}

    showCmd := &cobra.Command{
        Use:   "show <id|name>",
        Short: "Show detailed information about a model",
        Args:  cobra.ExactArgs(1),
        RunE: func(cmd *cobra.Command, args []string) error {
            cfg := config.Load()
            ident := args[0]
            mtypeStr, _ := cmd.Flags().GetString("type")
            modelType := parseModelType(mtypeStr)
            format, _ := cmd.Flags().GetString("format")

            ctx, cancel := context.WithTimeout(context.Background(), time.Duration(cfg.TimeoutSeconds+5)*time.Second)
            defer cancel()
            client := httpclient.New()
            var model *models.FullModel
            // If looks like an ObjectID
            if len(ident) == 24 && isHex(ident) {
                if m, err := dataaccess.FetchModelByID(ctx, client, modelType, ident); err == nil { model = m }
            }
            if model == nil {
                matches, err := dataaccess.SearchModelsByName(ctx, client, ident, modelType, false)
                if err != nil { return err }
                if len(matches) == 1 {
                    m := matches[0]
                    model = &m
                } else if len(matches) > 1 {
                    fmt.Println("Multiple models match:")
                    for _, m := range matches { fmt.Printf("  • %s (ID: %s)\n", m.Name(), m.ID()) }
                    return nil
                } else {
                    // try fuzzy
                    matches, err = dataaccess.SearchModelsByName(ctx, client, ident, modelType, true)
                    if err != nil { return err }
                    if len(matches) == 1 { m := matches[0]; model = &m }
                }
            }
            if model == nil { return fmt.Errorf("model not found: %s", ident) }

            // For now, print as table always
            printing.PrintModelsTable([]models.FullModel{*model}, []string{"name","creator","release_date","active_params_in_billion","max_input_tokens","max_output_tokens"}, "Model Details")
            _ = format
            return nil
        },
    }
    showCmd.Flags().String("type", "all", "Model type: all|small|vlm|chat")
    showCmd.Flags().String("format", "", "Output format (table, json, yaml)")

    infoCmd := &cobra.Command{
        Use:   "info <id|name>",
        Short: "Alias for show",
        Args:  cobra.ExactArgs(1),
        RunE: func(cmd *cobra.Command, args []string) error { return showCmd.RunE(cmd, args) },
    }

    modelCmd.AddCommand(showCmd, infoCmd)
    RegisterCommand(modelCmd)
}

func isHex(s string) bool {
    for _, r := range strings.ToLower(s) {
        if (r < '0' || r > '9') && (r < 'a' || r > 'f') { return false }
    }
    return true
}


