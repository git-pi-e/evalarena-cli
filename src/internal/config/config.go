package config

import (
    "bufio"
    "errors"
    "fmt"
    "os"
    "path/filepath"
    "strconv"
    "strings"
    "sync"

    "github.com/joho/godotenv"
)

// Config holds all runtime configuration loaded from environment variables and .env
type Config struct {
    BaseURL           string
    TimeoutSeconds    int
    Token             string
    OutputFormat      string // table|json|yaml
    NoColor           bool
    DefaultColumns    []string
    CacheEnabled      bool
    CacheTTLSeconds   int
    Chart             ChartConfig
    Chat              ChatConfig
}

type ChartConfig struct {
    Width     int
    Height    int
    Normalize string // none|zscore|minmax
}

type ChatConfig struct {
    DefaultModels []string
}

var (
    config     *Config
    configOnce sync.Once
)

// getenv returns env var or fallback
func getenv(key, fallback string) string {
    if v := os.Getenv(key); v != "" {
        return v
    }
    return fallback
}

// getcwd returns working directory or current binary directory
func getcwd() string {
    wd, err := os.Getwd()
    if err == nil {
        return wd
    }
    return "."
}

// Load loads the configuration from .env and process environment variables.
func Load() *Config {
    configOnce.Do(func() {
        // Load .env if present
        _ = godotenv.Load()

        cfg := &Config{}
        cfg.BaseURL = getenv("EVALARENA_BASE_URL", "https://evalarena-backend-89846023945.us-central1.run.app")
        cfg.TimeoutSeconds = mustAtoi(getenv("EVALARENA_TIMEOUT_S", "15"), 15)
        cfg.Token = getenv("EVALARENA_TOKEN", "")
        cfg.OutputFormat = strings.ToLower(getenv("EVALARENA_OUTPUT_FORMAT", "table"))
        cfg.NoColor = strings.EqualFold(getenv("EVALARENA_NO_COLOR", "false"), "true")
        cfg.DefaultColumns = splitCSV(getenv("EVALARENA_DEFAULT_COLUMNS", "name,creator,mmlu,mmlu_pro,humaneval,active_params_in_billion,input_price_per_1M_tokens_USD"))
        cfg.CacheEnabled = !strings.EqualFold(getenv("EVALARENA_CACHE_ENABLED", "true"), "false")
        cfg.CacheTTLSeconds = mustAtoi(getenv("EVALARENA_CACHE_TTL_SECONDS", "3600"), 3600)
        cfg.Chart = ChartConfig{
            Width:     mustAtoi(getenv("EVALARENA_CHART_WIDTH", "100"), 100),
            Height:    mustAtoi(getenv("EVALARENA_CHART_HEIGHT", "30"), 30),
            Normalize: strings.ToLower(getenv("EVALARENA_CHART_NORMALIZE", "none")),
        }
        cfg.Chat = ChatConfig{DefaultModels: splitCSV(getenv("EVALARENA_CHAT_DEFAULT_MODELS", ""))}
        config = cfg
    })
    return config
}

func mustAtoi(s string, def int) int {
    if i, err := strconv.Atoi(strings.TrimSpace(s)); err == nil {
        return i
    }
    return def
}

func splitCSV(s string) []string {
    if strings.TrimSpace(s) == "" {
        return []string{}
    }
    parts := strings.Split(s, ",")
    res := make([]string, 0, len(parts))
    for _, p := range parts {
        p = strings.TrimSpace(p)
        if p != "" {
            res = append(res, p)
        }
    }
    return res
}

// SaveEnv updates or creates .env with the given key=value
func SaveEnv(key, value string) error {
    if strings.TrimSpace(key) == "" {
        return errors.New("empty key")
    }
    // Determine .env path
    path := filepath.Join(getcwd(), ".env")

    // Read existing lines if file exists
    var lines []string
    if b, err := os.ReadFile(path); err == nil {
        lines = strings.Split(string(b), "\n")
    }

    // Update if existing
    updated := false
    for i, line := range lines {
        trim := strings.TrimSpace(line)
        if trim == "" || strings.HasPrefix(trim, "#") {
            continue
        }
        if k, _, ok := parseEnvLine(trim); ok && k == key {
            lines[i] = fmt.Sprintf("%s=%s", key, escapeEnvValue(value))
            updated = true
            break
        }
    }
    if !updated {
        lines = append(lines, fmt.Sprintf("%s=%s", key, escapeEnvValue(value)))
    }

    // Normalize trailing newline
    content := strings.Join(lines, "\n")
    if !strings.HasSuffix(content, "\n") {
        content += "\n"
    }

    return os.WriteFile(path, []byte(content), 0644)
}

// RemoveEnv removes a key from .env if present
func RemoveEnv(key string) error {
    path := filepath.Join(getcwd(), ".env")
    if b, err := os.ReadFile(path); err == nil {
        in := strings.Split(string(b), "\n")
        var out []string
        for _, line := range in {
            trim := strings.TrimSpace(line)
            if trim == "" || strings.HasPrefix(trim, "#") {
                out = append(out, line)
                continue
            }
            if k, _, ok := parseEnvLine(trim); ok && k == key {
                // skip
                continue
            }
            out = append(out, line)
        }
        content := strings.Join(out, "\n")
        if !strings.HasSuffix(content, "\n") {
            content += "\n"
        }
        return os.WriteFile(path, []byte(content), 0644)
    }
    return nil
}

func parseEnvLine(line string) (key, value string, ok bool) {
    if i := strings.Index(line, "="); i > 0 {
        k := strings.TrimSpace(line[:i])
        v := strings.TrimSpace(line[i+1:])
        return k, unescapeEnvValue(v), true
    }
    return "", "", false
}

func escapeEnvValue(v string) string {
    if strings.ContainsAny(v, " #\t\"'") || strings.Contains(v, "\n") {
        return strconv.Quote(v)
    }
    return v
}

func unescapeEnvValue(v string) string {
    v = strings.TrimSpace(v)
    if len(v) >= 2 && ((v[0] == '"' && v[len(v)-1] == '"') || (v[0] == '\'' && v[len(v)-1] == '\'')) {
        unq, err := strconv.Unquote(v)
        if err == nil {
            return unq
        }
    }
    return v
}

// Dump writes current config to a .env-like format (for debugging)
func Dump(cfg *Config) string {
    if cfg == nil {
        cfg = Load()
    }
    var b strings.Builder
    w := bufio.NewWriter(&b)
    _, _ = fmt.Fprintf(w, "EVALARENA_BASE_URL=%s\n", cfg.BaseURL)
    _, _ = fmt.Fprintf(w, "EVALARENA_TIMEOUT_S=%d\n", cfg.TimeoutSeconds)
    if cfg.Token != "" {
        _, _ = fmt.Fprintf(w, "EVALARENA_TOKEN=%s\n", cfg.Token)
    }
    _, _ = fmt.Fprintf(w, "EVALARENA_OUTPUT_FORMAT=%s\n", cfg.OutputFormat)
    _, _ = fmt.Fprintf(w, "EVALARENA_NO_COLOR=%t\n", cfg.NoColor)
    _, _ = fmt.Fprintf(w, "EVALARENA_DEFAULT_COLUMNS=%s\n", strings.Join(cfg.DefaultColumns, ","))
    _, _ = fmt.Fprintf(w, "EVALARENA_CACHE_ENABLED=%t\n", cfg.CacheEnabled)
    _, _ = fmt.Fprintf(w, "EVALARENA_CACHE_TTL_SECONDS=%d\n", cfg.CacheTTLSeconds)
    _, _ = fmt.Fprintf(w, "EVALARENA_CHART_WIDTH=%d\n", cfg.Chart.Width)
    _, _ = fmt.Fprintf(w, "EVALARENA_CHART_HEIGHT=%d\n", cfg.Chart.Height)
    _, _ = fmt.Fprintf(w, "EVALARENA_CHART_NORMALIZE=%s\n", cfg.Chart.Normalize)
    _, _ = fmt.Fprintf(w, "EVALARENA_CHAT_DEFAULT_MODELS=%s\n", strings.Join(cfg.Chat.DefaultModels, ","))
    _ = w.Flush()
    return b.String()
}


