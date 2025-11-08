package printing

import (
    "encoding/json"
    "fmt"
    "os"
    "sort"
    "strings"

    "github.com/fatih/color"
    "github.com/jedib0t/go-pretty/v6/table"
    "github.com/jedib0t/go-pretty/v6/text"
    "gopkg.in/yaml.v3"

    "evalarena-cli/internal/models"
)

func PrintJSON(data any) error {
    enc := json.NewEncoder(os.Stdout)
    enc.SetIndent("", "  ")
    return enc.Encode(data)
}

func PrintYAML(data any) error {
    b, err := yaml.Marshal(data)
    if err != nil { return err }
    _, err = os.Stdout.Write(b)
    return err
}

func PrintModelsTable(modelsList []models.FullModel, columns []string, title string) {
    if len(modelsList) == 0 {
        fmt.Println("No models found.")
        return
    }
    t := table.NewWriter()
    t.SetOutputMirror(os.Stdout)
    if title != "" { t.SetTitle(title) }
    t.Style().Title.Align = text.AlignCenter
    // headers
    hdr := make(table.Row, 0, len(columns))
    for _, c := range columns { hdr = append(hdr, ColumnLabel(c)) }
    t.AppendHeader(hdr)

    // find max values for numeric columns
    maxVals := map[string]float64{}
    for _, c := range columns {
        max := 0.0
        has := false
        for _, m := range modelsList {
            if v := valueForColumn(m, c); v != nil {
                if *v > max || !has { max = *v; has = true }
            }
        }
        if has { maxVals[c] = max }
    }

    for _, m := range modelsList {
        row := make(table.Row, 0, len(columns))
        for _, c := range columns {
            switch strings.ToLower(c) {
            case "name":
                row = append(row, m.Name())
            case "creator":
                row = append(row, m.Creator())
            default:
                v := valueForColumn(m, c)
                if v == nil { row = append(row, "—"); continue }
                formatted := formatCell(*v, c)
                if max, ok := maxVals[c]; ok && *v == max {
                    formatted = color.HiGreenString("%s", formatted)
                }
                row = append(row, formatted)
            }
        }
        t.AppendRow(row)
    }
    t.Render()
    fmt.Printf("\nShowing %d models\n", len(modelsList))
}

func ColumnLabel(key string) string {
    labels := map[string]string{
        "active_params_in_billion": "Params (B)",
        "input_price_per_1M_tokens_USD": "Input Price",
        "output_price_per_1M_tokens_USD": "Output Price",
        "max_input_tokens": "Context Window",
        "max_output_tokens": "Max Output",
        // benchmark labels (partial, fallback to title case)
        "mmlu": "MMLU",
        "mmlu_pro": "MMLU Pro",
        "humaneval": "HumanEval",
        "gpqa_diamond": "GPQA Diamond",
    }
    if v, ok := labels[key]; ok { return v }
    return strings.Title(strings.ReplaceAll(key, "_", " "))
}

func valueForColumn(m models.FullModel, col string) *float64 {
    switch col {
    case "active_params_in_billion":
        return models.SafeFloatPtr(m["active_params_in_billion"])
    case "input_price_per_1M_tokens_USD":
        return models.SafeFloatPtr(m["input_price_per_1M_tokens_USD"])
    case "output_price_per_1M_tokens_USD":
        return models.SafeFloatPtr(m["output_price_per_1M_tokens_USD"])
    case "max_input_tokens":
        if i := models.SafeIntPtr(m["max_input_tokens"]); i != nil { f := float64(*i); return &f }
        return nil
    case "max_output_tokens":
        if i := models.SafeIntPtr(m["max_output_tokens"]); i != nil { f := float64(*i); return &f }
        return nil
    default:
        return m.BenchmarkValue(col)
    }
}

func formatCell(val float64, col string) string {
    lower := strings.ToLower(col)
    switch {
    case strings.Contains(lower, "price"):
        if val == 0 { return "Free" }
        if val >= 1 { return fmt.Sprintf("$%.2f", val) }
        return fmt.Sprintf("$%.3f", val)
    case strings.Contains(lower, "tokens"):
        if val >= 1_000_000 { return fmt.Sprintf("%dM", int(val)/1_000_000) }
        if val >= 1_000 { return fmt.Sprintf("%dK", int(val)/1_000) }
        return fmt.Sprintf("%d", int(val))
    default:
        // compact float formatting
        if val == 0 { return "0" }
        if val >= 1000 {
            if val >= 1_000_000 { return fmt.Sprintf("%.1fM", val/1_000_000) }
            return fmt.Sprintf("%.1fK", val/1000)
        }
        if val < 0.01 && val > 0 { return fmt.Sprintf("%.2e", val) }
        return fmt.Sprintf("%.2f", val)
    }
}

// PrintComparisonTable prints a comparison across metrics for multiple models
func PrintComparisonTable(modelsList []models.FullModel, columns []string, diffMode string) {
    if len(modelsList) < 2 {
        fmt.Println("Need at least 2 models for comparison.")
        return
    }
    if len(columns) == 0 {
        set := map[string]struct{}{}
        for _, m := range modelsList { for k := range m.AllBenchmarks() { set[k] = struct{}{} } }
        for k := range set { columns = append(columns, k) }
        sort.Strings(columns)
    }
    t := table.NewWriter()
    t.SetOutputMirror(os.Stdout)
    t.AppendHeader(append(table.Row{"Metric"}, modelNames(modelsList)...))
    addDiff := diffMode != "none" && len(modelsList) == 2
    if addDiff { t.AppendHeader(table.Row{"", "", "", "Diff"}) }
    for _, c := range columns {
        vals := make([]*float64, len(modelsList))
        for i, m := range modelsList { vals[i] = m.BenchmarkValue(c) }
        if allNil(vals) { continue }
        row := make(table.Row, 0, len(modelsList)+2)
        row = append(row, ColumnLabel(c))
        // highlight max
        max := -1.0
        maxIdx := -1
        for i, v := range vals { if v != nil && (*v > max || maxIdx == -1) { max = *v; maxIdx = i } }
        for i, v := range vals {
            if v == nil { row = append(row, "—"); continue }
            s := formatCell(*v, c)
            if i == maxIdx { s = color.HiGreenString("%s", s) }
            row = append(row, s)
        }
        if addDiff {
            d := diffCell(vals[0], vals[1], diffMode)
            row = append(row, d)
        }
        t.AppendRow(row)
    }
    t.Render()
}

func modelNames(ms []models.FullModel) []any {
    out := make([]any, 0, len(ms))
    for _, m := range ms { out = append(out, truncate(m.Name(), 15)) }
    return out
}

func allNil(vals []*float64) bool {
    for _, v := range vals { if v != nil { return false } }
    return true
}

func diffCell(a, b *float64, mode string) string {
    if a == nil || b == nil { return "—" }
    switch mode {
    case "absolute":
        d := *b - *a
        s := fmt.Sprintf("%+.2f", d)
        if d > 0 { return color.HiGreenString(s) }
        if d < 0 { return color.HiRedString(s) }
        return color.YellowString(s)
    case "percent":
        if *a == 0 { return color.YellowString("∞") }
        d := ((*b - *a) / *a) * 100
        s := fmt.Sprintf("%+.1f%%", d)
        if d > 0 { return color.HiGreenString(s) }
        if d < 0 { return color.HiRedString(s) }
        return color.YellowString(s)
    default:
        return "—"
    }
}

func truncate(s string, n int) string {
    if len(s) <= n { return s }
    if n <= 3 { return s[:n] }
    return s[:n-3] + "..."
}


