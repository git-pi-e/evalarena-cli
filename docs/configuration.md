## Configuration

The CLI reads configuration from environment variables and `.env`.

### Keys
- `EVALARENA_BASE_URL` – API base URL (default: public backend)
- `EVALARENA_TIMEOUT_S` – request timeout seconds (default 15)
- `EVALARENA_TOKEN` – API token (set by `auth login`)
- `EVALARENA_OUTPUT_FORMAT` – table|json|yaml (default table)
- `EVALARENA_NO_COLOR` – true|false
- `EVALARENA_DEFAULT_COLUMNS` – CSV default columns
- `EVALARENA_CACHE_ENABLED` – true|false (default true)
- `EVALARENA_CACHE_TTL_SECONDS` – cache TTL seconds (default 3600)
- `EVALARENA_CHART_WIDTH` – chart width (default 100)
- `EVALARENA_CHART_HEIGHT` – chart height (default 30)
- `EVALARENA_CHART_NORMALIZE` – none|zscore|minmax
- `EVALARENA_CHAT_DEFAULT_MODELS` – default chat model IDs (CSV)

### Managing Config via CLI
```bash
evalarena config show
evalarena config set base_url https://...
evalarena config set chat.default_models gpt-4o,claude-3-5-sonnet
```


