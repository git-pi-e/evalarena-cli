package utils

import (
    "context"
    "errors"
    "math"
    "sort"
    "strconv"
    "strings"

    "evalarena-cli/internal/dataaccess"
    "evalarena-cli/internal/httpclient"
    "evalarena-cli/internal/models"
)

func IsNumeric(v any) bool {
    if v == nil { return false }
    if _, ok := v.(float64); ok { return true }
    if _, ok := v.(int); ok { return true }
    if s, ok := v.(string); ok {
        s = strings.TrimSpace(strings.ReplaceAll(s, ",", ""))
        if s == "" { return false }
        _, err := strconv.ParseFloat(s, 64)
        return err == nil
    }
    return false
}

func SafeFloat(v any, def float64) float64 {
    if v == nil { return def }
    switch t := v.(type) {
    case float64:
        return t
    case int:
        return float64(t)
    case string:
        s := strings.TrimSpace(strings.ReplaceAll(t, ",", ""))
        if f, err := strconv.ParseFloat(s, 64); err == nil { return f }
    }
    return def
}

func Normalize(values []float64, method string) []float64 {
    if len(values) == 0 || method == "none" { return values }
    switch method {
    case "zscore":
        mean := 0.0
        for _, v := range values { mean += v }
        mean /= float64(len(values))
        var variance float64
        for _, v := range values { d := v - mean; variance += d * d }
        variance /= float64(len(values))
        std := math.Sqrt(variance)
        if std == 0 { out := make([]float64, len(values)); return out }
        out := make([]float64, len(values))
        for i, v := range values { out[i] = (v - mean) / std }
        return out
    case "minmax":
        minV, maxV := values[0], values[0]
        for _, v := range values { if v < minV { minV = v }; if v > maxV { maxV = v } }
        if minV == maxV { out := make([]float64, len(values)); return out }
        out := make([]float64, len(values))
        for i, v := range values { out[i] = (v - minV) / (maxV - minV) }
        return out
    default:
        return values
    }
}

func ComputeParetoFrontier(points [][2]float64, minimizeX, minimizeY bool) []int {
    if len(points) == 0 { return nil }
    indexed := make([]struct{ idx int; x, y float64 }, len(points))
    for i, p := range points { indexed[i] = struct{ idx int; x, y float64 }{i, p[0], p[1]} }
    sort.Slice(indexed, func(i, j int) bool {
        if minimizeX { return indexed[i].x < indexed[j].x }
        return indexed[i].x > indexed[j].x
    })
    var frontier []int
    var bestY *float64
    for _, it := range indexed {
        if bestY == nil {
            v := it.y; bestY = &v; frontier = append(frontier, it.idx)
            continue
        }
        if minimizeY {
            if it.y < *bestY { v := it.y; bestY = &v; frontier = append(frontier, it.idx) }
        } else {
            if it.y > *bestY { v := it.y; bestY = &v; frontier = append(frontier, it.idx) }
        }
    }
    return frontier
}

// ResolveModelNames resolves provided names/ids to concrete models via search.
func ResolveModelNames(ctx context.Context, client *httpclient.Client, names []string, modelType dataaccess.ModelType) ([]models.FullModel, error) {
    var out []models.FullModel
    for _, name := range names {
        matches, err := dataaccess.SearchModelsByName(ctx, client, name, modelType, false)
        if err != nil { return nil, err }
        if len(matches) == 0 {
            matches, err = dataaccess.SearchModelsByName(ctx, client, name, modelType, true)
            if err != nil { return nil, err }
        }
        if len(matches) == 0 { return nil, errors.New("could not find model: " + name) }
        if len(matches) == 1 { out = append(out, matches[0]); continue }
        // Try exact case-insensitive match
        var exact *models.FullModel
        for _, m := range matches { if strings.EqualFold(m.Name(), name) { mm := m; exact = &mm; break } }
        if exact != nil { out = append(out, *exact); continue }
        // ambiguous
        return nil, errors.New("ambiguous model name: " + name)
    }
    return out, nil
}


