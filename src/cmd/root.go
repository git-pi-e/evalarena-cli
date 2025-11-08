package cmd

import (
    "fmt"
    "os"
    "strings"

    "github.com/spf13/cobra"

    "evalarena-cli/internal/config"
)

var (
    rootCmd = &cobra.Command{
        Use:   "evalarena",
        Short: "EvalArena CLI - Compare and analyze AI model benchmarks",
        Long:  "EvalArena CLI - Compare and analyze AI model benchmarks",
        PersistentPreRunE: func(cmd *cobra.Command, args []string) error {
            // apply flag overrides into config
            cfg := config.Load()
            if baseURLFlag != "" { cfg.BaseURL = baseURLFlag }
            if timeoutFlag > 0 { cfg.TimeoutSeconds = timeoutFlag }
            if noCacheFlag { cfg.CacheEnabled = false }
            if noColorFlag { cfg.NoColor = true }
            if outputFormatFlag != "" { cfg.OutputFormat = strings.ToLower(outputFormatFlag) }
            return nil
        },
    }

    baseURLFlag      string
    timeoutFlag      int
    noCacheFlag      bool
    noColorFlag      bool
    outputFormatFlag string
)

func init() {
    // persistent flags
    rootCmd.PersistentFlags().StringVar(&baseURLFlag, "base-url", "", "Override base URL for API requests")
    rootCmd.PersistentFlags().IntVar(&timeoutFlag, "timeout", 0, "Override request timeout in seconds")
    rootCmd.PersistentFlags().BoolVar(&noCacheFlag, "no-cache", false, "Disable HTTP caching")
    rootCmd.PersistentFlags().BoolVar(&noColorFlag, "no-color", false, "Disable colored output")
    rootCmd.PersistentFlags().StringVar(&outputFormatFlag, "format", "", "Default output format (table, json, yaml)")
}

func Execute() {
    if err := rootCmd.Execute(); err != nil {
        fmt.Fprintln(os.Stderr, err)
        os.Exit(1)
    }
}

func RegisterCommand(cmd *cobra.Command) { rootCmd.AddCommand(cmd) }



