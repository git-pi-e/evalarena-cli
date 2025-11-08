package httpclient

import (
    "bytes"
    "context"
    "encoding/json"
    "fmt"
    "io"
    "net/http"
    "net/url"
    "strings"
    "sync"
    "time"

    "evalarena-cli/internal/config"
)

type Client struct {
    base    *http.Client
    baseURL string
    // simple in-memory GET cache
    mu    sync.Mutex
    cache map[string]cacheEntry
}

type cacheEntry struct {
    expiresAt time.Time
    data      []byte
}

func New() *Client {
    cfg := config.Load()
    return &Client{
        base: &http.Client{Timeout: time.Duration(cfg.TimeoutSeconds) * time.Second},
        baseURL: cfg.BaseURL,
        cache:   make(map[string]cacheEntry),
    }
}

// WithHeader is a request option to set a header
func WithHeader(key, value string) func(*http.Request) {
    return func(r *http.Request) { r.Header.Set(key, value) }
}

// doRequest performs an HTTP request with optional modifiers
func (c *Client) doRequest(ctx context.Context, method, path string, body io.Reader, opts ...func(*http.Request)) (*http.Response, error) {
    u, err := url.Parse(c.baseURL)
    if err != nil {
        return nil, err
    }
    ref, err := url.Parse(path)
    if err != nil {
        return nil, err
    }
    full := u.ResolveReference(ref)

    req, err := http.NewRequestWithContext(ctx, method, full.String(), body)
    if err != nil {
        return nil, err
    }
    req.Header.Set("User-Agent", "evalarena-cli-go/0.1.0")
    req.Header.Set("Accept", "application/json")
    for _, opt := range opts {
        opt(req)
    }

    resp, err := c.base.Do(req)
    if err != nil {
        return nil, err
    }
    return resp, nil
}

// GetJSON performs a GET request with optional query params and returns decoded JSON into out.
func (c *Client) GetJSON(ctx context.Context, path string, params url.Values, out any) error {
    cfg := config.Load()

    if params != nil {
        if qstr := params.Encode(); qstr != "" {
            if !strings.Contains(path, "?") {
                path += "?" + qstr
            } else {
                path += "&" + qstr
            }
        }
    }

    cacheKey := path
    if cfg.CacheEnabled {
        if b := c.getCache(cacheKey); b != nil {
            return json.Unmarshal(b, out)
        }
    }

    resp, err := c.doRequest(ctx, http.MethodGet, path, nil)
    if err != nil {
        return err
    }
    defer resp.Body.Close()

    if resp.StatusCode == http.StatusUnauthorized {
        return fmt.Errorf("authentication required (401)")
    }
    if resp.StatusCode == http.StatusForbidden {
        return fmt.Errorf("access forbidden (403)")
    }
    if resp.StatusCode == http.StatusNotFound {
        return fmt.Errorf("endpoint not found: %s", path)
    }
    if resp.StatusCode == http.StatusTooManyRequests {
        return fmt.Errorf("rate limit exceeded (429)")
    }
    if resp.StatusCode < 200 || resp.StatusCode >= 300 {
        b, _ := io.ReadAll(io.LimitReader(resp.Body, 2048))
        return fmt.Errorf("API request failed: HTTP %d: %s", resp.StatusCode, string(b))
    }
    data, err := io.ReadAll(resp.Body)
    if err != nil {
        return err
    }
    if cfg.CacheEnabled {
        c.setCache(cacheKey, data, time.Duration(cfg.CacheTTLSeconds)*time.Second)
    }
    return json.Unmarshal(data, out)
}

// GetStatus performs a GET and returns only status code.
func (c *Client) GetStatus(ctx context.Context, path string, opts ...func(*http.Request)) (int, error) {
    resp, err := c.doRequest(ctx, http.MethodGet, path, nil, opts...)
    if err != nil {
        return 0, err
    }
    defer resp.Body.Close()
    io.Copy(io.Discard, resp.Body)
    return resp.StatusCode, nil
}

// PostStream sends POST with JSON body and returns the response body reader for streaming.
func (c *Client) PostStream(ctx context.Context, path string, payload any, opts ...func(*http.Request)) (*http.Response, error) {
    b, err := json.Marshal(payload)
    if err != nil {
        return nil, err
    }
    resp, err := c.doRequest(ctx, http.MethodPost, path, bytes.NewReader(b), append(opts, func(r *http.Request) {
        r.Header.Set("Content-Type", "application/json")
    })...)
    if err != nil {
        return nil, err
    }
    if resp.StatusCode < 200 || resp.StatusCode >= 300 {
        body, _ := io.ReadAll(io.LimitReader(resp.Body, 2048))
        _ = resp.Body.Close()
        return nil, fmt.Errorf("HTTP %d: %s", resp.StatusCode, string(body))
    }
    return resp, nil
}

func (c *Client) getCache(key string) []byte {
    c.mu.Lock()
    defer c.mu.Unlock()
    if e, ok := c.cache[key]; ok {
        if time.Now().Before(e.expiresAt) {
            return e.data
        }
        delete(c.cache, key)
    }
    return nil
}

func (c *Client) setCache(key string, data []byte, ttl time.Duration) {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.cache[key] = cacheEntry{expiresAt: time.Now().Add(ttl), data: data}
}


