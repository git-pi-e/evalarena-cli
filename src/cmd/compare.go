package cmd

import (
    "context"
    "time"

    "github.com/spf13/cobra"

    "evalarena-cli/internal/config"
    "evalarena-cli/internal/httpclient"
    "evalarena-cli/internal/printing"
    "evalarena-cli/internal/utils"
)

func init() {
    compareCmd := &cobra.Command{
        Use:   "compare <modelA> <modelB> [more...]",
        Short: "Compare multiple models side-by-side",
        Args:  cobra.MinimumNArgs(2),
        RunE: func(cmd *cobra.Command, args []string) error {
            cfg := config.Load()
            mtypeStr, _ := cmd.Flags().GetString("type")
            columns, _ := cmd.Flags().GetString("columns")
            diff, _ := cmd.Flags().GetString("diff")
            modelType := parseModelType(mtypeStr)

            ctx, cancel := context.WithTimeout(context.Background(), time.Duration(cfg.TimeoutSeconds+10)*time.Second)
            defer cancel()
            client := httpclient.New()
            models, err := utils.ResolveModelNames(ctx, client, args, modelType)
            if err != nil { return err }

            var cols []string
            if columns != "" { cols = splitCSV(columns) }
            printing.PrintComparisonTable(models, cols, diff)
            return nil
        },
    }
    compareCmd.Flags().String("type", "all", "Model type: all|small|vlm|chat")
    compareCmd.Flags().String("columns", "", "Comma-separated list of benchmarks to compare")
    compareCmd.Flags().String("diff", "none", "Diff mode: none|absolute|percent")
    RegisterCommand(compareCmd)
}


