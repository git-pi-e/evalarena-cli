package models

import (
    "encoding/json"
    "sort"
    "strconv"
    "strings"
)

// FullModel is a flexible model wrapper over raw JSON data.
type FullModel map[string]any

func (m FullModel) raw(key string) any { return m[key] }

func (m FullModel) Name() string { return safeString(m["name"]) }
func (m FullModel) ID() string {
    if v := safeString(m["_id"]); v != "" { return v }
    return safeString(m["id"]) // some endpoints may return id
}
func (m FullModel) Creator() string { return safeString(m["creator"]) }

func (m FullModel) GetPricingInfo() map[string]*float64 {
    return map[string]*float64{
        "input_price_per_1M_tokens_USD":  SafeFloatPtr(m["input_price_per_1M_tokens_USD"]),
        "output_price_per_1M_tokens_USD": SafeFloatPtr(m["output_price_per_1M_tokens_USD"]),
    }
}

func (m FullModel) GetTokenLimits() map[string]*int {
    return map[string]*int{
        "max_input_tokens":  SafeIntPtr(m["max_input_tokens"]),
        "max_output_tokens": SafeIntPtr(m["max_output_tokens"]),
    }
}

func (m FullModel) AllBenchmarks() map[string]float64 {
    res := map[string]float64{}
    for _, key := range benchmarkKeys() {
        if f := SafeFloatPtr(m[key]); f != nil {
            res[key] = *f
        }
    }
    // nested "benchmarks" object
    if b, ok := m["benchmarks"].(map[string]any); ok {
        for _, cat := range []string{
            "math_benchmarks",
            "coding_benchmarks",
            "language_understanding",
            "other_benchmarks",
            "multimodal_reasoning",
            "document_understanding",
            "video",
            "agent",
        } {
            if mm, ok := b[cat].(map[string]any); ok {
                for k, v := range mm {
                    if f := SafeFloatPtr(v); f != nil { res[k] = *f }
                }
            }
        }
    }
    return res
}

func (m FullModel) BenchmarkValue(key string) *float64 {
    if f := SafeFloatPtr(m[key]); f != nil { return f }
    if b, ok := m["benchmarks"].(map[string]any); ok {
        for _, cat := range []string{
            "math_benchmarks",
            "coding_benchmarks",
            "language_understanding",
            "other_benchmarks",
            "multimodal_reasoning",
            "document_understanding",
            "video",
            "agent",
        } {
            if mm, ok := b[cat].(map[string]any); ok {
                if v, ok := mm[key]; ok {
                    return SafeFloatPtr(v)
                }
            }
        }
    }
    return nil
}

func benchmarkKeys() []string {
    keys := []string{
        "aime_2024","aime_2025","math","math500","codeforces","humaneval","swe_bench_verified","live_code_bench_v5","aider_polyglot_diff",
        "mmlu","mmlu_pro","hle","gpqa_diamond","simple_qa","mmmu_val","mathvista_testmini","tau_bench_airline","tau_bench_retail","arc_agi_v2",
        "mmmu","mmmu_pro","mathvista","mmbench_v1_1_en","mm_mt_bench","doc_vqa","chart_qa","blink","longvideobench","video_mme_wo_sub","osworld","webvoyager","screenspot_pro",
    }
    sort.Strings(keys)
    return keys
}

func safeString(v any) string {
    switch t := v.(type) {
    case string:
        return t
    case json.Number:
        return t.String()
    default:
        return ""
    }
}

func SafeFloatPtr(v any) *float64 {
    switch t := v.(type) {
    case float64:
        vv := t
        return &vv
    case float32:
        vv := float64(t)
        return &vv
    case int:
        vv := float64(t)
        return &vv
    case int64:
        vv := float64(t)
        return &vv
    case json.Number:
        if f, err := t.Float64(); err == nil { return &f }
    case string:
        s := strings.TrimSpace(strings.ReplaceAll(t, ",", ""))
        if s == "" { return nil }
        if f, err := strconv.ParseFloat(s, 64); err == nil { return &f }
    }
    return nil
}

func SafeIntPtr(v any) *int {
    switch t := v.(type) {
    case int:
        vv := t
        return &vv
    case int64:
        vv := int(t)
        return &vv
    case float64:
        vv := int(t)
        return &vv
    case json.Number:
        if i, err := strconv.Atoi(t.String()); err == nil { return &i }
    case string:
        s := strings.TrimSpace(strings.ReplaceAll(t, ",", ""))
        if s == "" { return nil }
        if i, err := strconv.Atoi(s); err == nil { return &i }
    }
    return nil
}


