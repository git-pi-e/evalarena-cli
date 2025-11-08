package cmd

import (
    "context"
    "fmt"
    "sort"
    "strings"
    "time"

    "github.com/spf13/cobra"

    "evalarena-cli/internal/config"
    "evalarena-cli/internal/dataaccess"
    "evalarena-cli/internal/httpclient"
    "evalarena-cli/internal/printing"
)

func init() {
    modelsCmd := &cobra.Command{Use: "models", Short: "List and search models"}

    listCmd := &cobra.Command{
        Use:   "list",
        Short: "List models",
        RunE: func(cmd *cobra.Command, args []string) error {
            cfg := config.Load()
            mtypeStr, _ := cmd.Flags().GetString("type")
            sortBy, _ := cmd.Flags().GetString("sort-by")
            order, _ := cmd.Flags().GetString("order")
            page, _ := cmd.Flags().GetInt("page")
            limit, _ := cmd.Flags().GetInt("limit")
            columns, _ := cmd.Flags().GetString("columns")
            evals, _ := cmd.Flags().GetString("evals")
            noCache, _ := cmd.Flags().GetBool("no-cache")

            modelType := parseModelType(mtypeStr)
            var pagePtr, limitPtr *int
            if page > 0 { pagePtr = &page }
            if limit > 0 { limitPtr = &limit }

            ctx, cancel := context.WithTimeout(context.Background(), time.Duration(cfg.TimeoutSeconds+5)*time.Second)
            defer cancel()
            client := httpclient.New()
            list, err := dataaccess.FetchModels(ctx, client, modelType, sortBy, order, pagePtr, limitPtr, noCache)
            if err != nil { return err }
            if len(list) == 0 { fmt.Println("No models found."); return nil }

            // columns selection
            var cols []string
            if columns != "" {
                cols = splitCSV(columns)
            } else if evals != "" {
                cols = benchmarkColumnsFor(modelType, evals)
            } else {
                cols = defaultColumnsFor(modelType, cfg.DefaultColumns)
            }

            title := fmt.Sprintf("%s Models", strings.Title(string(modelType)))
            printing.PrintModelsTable(list, cols, title)
            return nil
        },
    }
    listCmd.Flags().String("type", "all", "Model type: all|small|vlm|chat")
    listCmd.Flags().String("sort-by", "name", "Field to sort by")
    listCmd.Flags().String("order", "asc", "Sort order: asc|desc")
    listCmd.Flags().Int("page", 0, "Page number (client-side)")
    listCmd.Flags().Int("limit", 0, "Limit number of models (client-side)")
    listCmd.Flags().String("columns", "", "Comma-separated list of columns to display")
    listCmd.Flags().String("evals", "", "Show benchmark category (e.g., all, math, coding, knowledge, multimodal, document, video, agent)")
    listCmd.Flags().String("format", "", "Output format (table, json, yaml)")
    listCmd.Flags().Bool("no-cache", false, "Bypass cache and fetch fresh data")

    columnsCmd := &cobra.Command{
        Use:   "columns",
        Short: "List available columns for a model type",
        RunE: func(cmd *cobra.Command, args []string) error {
            cfg := config.Load()
            mtypeStr, _ := cmd.Flags().GetString("type")
            modelType := parseModelType(mtypeStr)
            ctx, cancel := context.WithTimeout(context.Background(), time.Duration(cfg.TimeoutSeconds+5)*time.Second)
            defer cancel()
            client := httpclient.New()
            keys, err := dataaccess.GetAllBenchmarkKeys(ctx, client, modelType)
            if err != nil { return err }
            // standard fields
            standard := []string{"name","creator","active_params_in_billion","input_price_per_1M_tokens_USD","output_price_per_1M_tokens_USD","max_input_tokens","max_output_tokens"}
            fmt.Printf("Available columns for %s models:\n\n", mtypeStr)
            fmt.Println("Standard Fields:")
            for _, k := range standard { fmt.Println("  •", k) }
            fmt.Println()
            fmt.Printf("Benchmarks (%d):\n", len(keys))
            sort.Strings(keys)
            for _, k := range keys { fmt.Println("  •", k) }
            return nil
        },
    }
    columnsCmd.Flags().String("type", "all", "Model type: all|small|vlm|chat")

    searchCmd := &cobra.Command{
        Use:   "search <query>",
        Short: "Search for models by name",
        Args:  cobra.ExactArgs(1),
        RunE: func(cmd *cobra.Command, args []string) error {
            cfg := config.Load()
            query := args[0]
            mtypeStr, _ := cmd.Flags().GetString("type")
            modelType := parseModelType(mtypeStr)
            columns, _ := cmd.Flags().GetString("columns")

            ctx, cancel := context.WithTimeout(context.Background(), time.Duration(cfg.TimeoutSeconds+5)*time.Second)
            defer cancel()
            client := httpclient.New()
            list, err := dataaccess.SearchModelsByName(ctx, client, query, modelType, true)
            if err != nil { return err }
            if len(list) == 0 { fmt.Println("No models found."); return nil }

            var cols []string
            if columns != "" { cols = splitCSV(columns) } else { cols = defaultColumnsFor(modelType, cfg.DefaultColumns) }
            printing.PrintModelsTable(list, cols, fmt.Sprintf("Search Results for '%s'", query))
            return nil
        },
    }
    searchCmd.Flags().String("type", "all", "Model type: all|small|vlm|chat")
    searchCmd.Flags().String("columns", "", "Comma-separated list of columns to display")
    searchCmd.Flags().String("format", "", "Output format (table, json, yaml)")

    modelsCmd.AddCommand(listCmd, columnsCmd, searchCmd)
    RegisterCommand(modelsCmd)
}

func parseModelType(s string) dataaccess.ModelType {
    switch strings.ToLower(s) {
    case "all":
        return dataaccess.ModelAll
    case "small":
        return dataaccess.ModelSmall
    case "vlm":
        return dataaccess.ModelVLM
    case "chat":
        return dataaccess.ModelChat
    default:
        return dataaccess.ModelAll
    }
}

func splitCSV(s string) []string {
    parts := strings.Split(s, ",")
    out := make([]string, 0, len(parts))
    for _, p := range parts { if t := strings.TrimSpace(p); t != "" { out = append(out, t) } }
    return out
}

func defaultColumnsFor(t dataaccess.ModelType, fallback []string) []string {
    m := map[dataaccess.ModelType][]string{
        dataaccess.ModelAll:   {"name","creator","release_date","max_input_tokens","description"},
        dataaccess.ModelSmall: {"name","creator","release_date","max_input_tokens","description"},
        dataaccess.ModelVLM:   {"name","creator","release_date","max_input_tokens","description"},
        dataaccess.ModelChat:  {"name","creator","description"},
    }
    if v, ok := m[t]; ok { return v }
    return fallback
}

func benchmarkColumnsFor(t dataaccess.ModelType, cat string) []string {
    // Minimal replication of categories
    cats := map[dataaccess.ModelType]map[string][]string{
        dataaccess.ModelAll: {
            "all": {"name","creator","mmlu","mmlu_pro","humaneval","math","gpqa_diamond","swe_bench_verified"},
            "math": {"name","creator","aime_2024","aime_2025","math","math500"},
            "coding": {"name","creator","humaneval","swe_bench_verified","live_code_bench_v5","codeforces","aider_polyglot_diff"},
            "knowledge": {"name","creator","mmlu","mmlu_pro","gpqa_diamond","simple_qa","hle"},
        },
        dataaccess.ModelSmall: {
            "all": {"name","creator","mmlu","mmlu_pro","humaneval","math","gpqa_diamond","swe_bench_verified"},
        },
        dataaccess.ModelVLM: {
            "all": {"name","creator","mmmu","mathvista","doc_vqa","osworld","blink"},
        },
        dataaccess.ModelChat: {
            "all": {"name","creator","mmlu","humaneval"},
        },
    }
    if mm, ok := cats[t]; ok {
        if v, ok := mm[strings.ToLower(cat)]; ok { return v }
    }
    return []string{"name","creator"}
}



