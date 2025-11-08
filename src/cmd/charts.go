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
    "evalarena-cli/internal/utils"
)

func init() {
    chartsCmd := &cobra.Command{Use: "charts", Short: "Generate charts"}

    barCmd := &cobra.Command{
        Use:   "bar <metric>",
        Short: "Generate bar chart comparing models on a metric",
        Args:  cobra.ExactArgs(1),
        RunE: func(cmd *cobra.Command, args []string) error {
            metric := args[0]
            cfg := config.Load()
            mtypeStr, _ := cmd.Flags().GetString("type")
            modelType := parseModelType(mtypeStr)
            normalize, _ := cmd.Flags().GetString("normalize")
            top, _ := cmd.Flags().GetInt("top")

            ctx, cancel := context.WithTimeout(context.Background(), time.Duration(cfg.TimeoutSeconds+10)*time.Second)
            defer cancel()
            client := httpclient.New()
            list, err := dataaccess.FetchModels(ctx, client, modelType, "name", "asc", nil, nil, false)
            if err != nil { return err }

            type pair struct { name string; v float64 }
            var pairs []pair
            for _, m := range list {
                if v := m.BenchmarkValue(metric); v != nil && *v > 0 { pairs = append(pairs, pair{name: m.Name(), v: *v}) }
            }
            sort.Slice(pairs, func(i, j int) bool { return pairs[i].v > pairs[j].v })
            if top > 0 && top < len(pairs) { pairs = pairs[:top] }

            vals := make([]float64, len(pairs))
            for i, p := range pairs { vals[i] = p.v }
            if normalize != "none" { vals = utils.Normalize(vals, normalize) }
            fmt.Printf("\n%s Scores (%s)\n\n", strings.Title(strings.ReplaceAll(metric, "_", " ")), normalize)
            maxName := 0
            for _, p := range pairs { if l := len(cleanName(p.name)); l > maxName { maxName = l } }
            if maxName > 40 { maxName = 40 }
            for i, p := range pairs {
                name := cleanName(p.name)
                if len(name) > maxName { name = name[:maxName-3]+"..." }
                barLen := int(50 * vals[i] / maxFloat(vals))
                if barLen < 1 && vals[i] > 0 { barLen = 1 }
                fmt.Printf("%-*s %s %.2f\n", maxName, name, strings.Repeat("█", barLen), vals[i])
            }
            fmt.Println()
            return nil
        },
    }
    barCmd.Flags().String("type", "all", "Model type: all|small|vlm|chat")
    barCmd.Flags().String("normalize", "none", "Normalization method: none|zscore|minmax")
    barCmd.Flags().Int("top", 0, "Show only top N models")

    paretoCmd := &cobra.Command{
        Use:   "pareto <quality-metric> [cost-metric]",
        Short: "Generate Pareto frontier chart",
        Args:  cobra.RangeArgs(1, 2),
        RunE: func(cmd *cobra.Command, args []string) error {
            quality := args[0]
            cost := ""
            if len(args) > 1 { cost = args[1] }
            cfg := config.Load()
            mtypeStr, _ := cmd.Flags().GetString("type")
            modelType := parseModelType(mtypeStr)

            ctx, cancel := context.WithTimeout(context.Background(), time.Duration(cfg.TimeoutSeconds+10)*time.Second)
            defer cancel()
            client := httpclient.New()
            list, err := dataaccess.FetchModels(ctx, client, modelType, "name", "asc", nil, nil, false)
            if err != nil { return err }

            type point struct { name string; cost, quality float64 }
            var points []point
            for _, m := range list {
                q := m.BenchmarkValue(quality)
                var c *float64
                if cost == "" {
                    // blended cost 3:1 input:output
                    pi := m.GetPricingInfo()["input_price_per_1M_tokens_USD"]
                    po := m.GetPricingInfo()["output_price_per_1M_tokens_USD"]
                    if pi != nil && po != nil { v := ((3*(*pi))+(*po))/4; c = &v } else if pi != nil { c = pi } else { c = po }
                } else {
                    c = m.BenchmarkValue(cost)
                }
                if q != nil && c != nil && *c > 0 { points = append(points, point{m.Name(), *c, *q}) }
            }
            if len(points) < 2 { return fmt.Errorf("not enough data for pareto analysis") }
            arr := make([][2]float64, len(points))
            for i, p := range points { arr[i] = [2]float64{p.cost, p.quality} }
            frontier := utils.ComputeParetoFrontier(arr, true, false)
            fmt.Printf("\nPareto Frontier: %s vs %s\n\n", strings.Title(quality), titleForCost(cost))
            fmt.Printf("%-40s  %-12s  %-12s  %-10s  %-10s\n", "Model", titleForCost(cost), strings.Title(quality), "Efficiency", "Status")
            set := map[int]struct{}{}
            for _, i := range frontier { set[i] = struct{}{} }
            for i, p := range points {
                status := "Dominated"
                if _, ok := set[i]; ok { status = "🏆 Frontier" }
                eff := p.quality / p.cost
                fmt.Printf("%-40.40s  %-12.3f  %-12.2f  %-10.3f  %-10s\n", cleanName(p.name), p.cost, p.quality, eff, status)
            }
            fmt.Printf("\nFound %d models on the Pareto frontier out of %d total.\n\n", len(frontier), len(points))
            return nil
        },
    }
    paretoCmd.Flags().String("type", "all", "Model type: all|small|vlm|chat")

    chartsCmd.AddCommand(barCmd, paretoCmd)
    RegisterCommand(chartsCmd)
}

func cleanName(s string) string { return strings.TrimSpace(s) }
func maxFloat(v []float64) float64 { m := v[0]; for _, x := range v { if x > m { m = x } }; return m }
func titleForCost(cost string) string {
    if cost == "" { return "Blended Cost" }
    return strings.Title(strings.ReplaceAll(cost, "_", " "))
}



