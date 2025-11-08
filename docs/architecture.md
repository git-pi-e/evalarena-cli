## Architecture

### High-Level
- `go/` – Go CLI module
  - `cmd/` – Cobra commands (auth, config, ping, models, model, compare, charts, chat)
  - `internal/config` – .env + env loader, settings model
  - `internal/httpclient` – HTTP client, caching, streaming, error handling
  - `internal/dataaccess` – Endpoint access and parsing
  - `internal/models` – Flexible model types from JSON
  - `internal/printing` – Tables/formatting
  - `internal/utils` – Numeric helpers, normalization, pareto
- `evalarena_py/` – legacy Python CLI (kept for reference)
- `docs/` – onboarding and reference documentation

### Endpoints
- Models: `/api/models/`, `/api/small-models/`, `/api/vlm-models/`
- Chat models: `/api/chat/models/`
- Chat streaming: `/api/chat/chat/` (POST with streaming response)
- Health: `/api/ping/`

### Config
- `.env` with `EVALARENA_*` keys (see `docs/configuration.md`)
- CLI flags override env at runtime

### Caching
- In-memory GET cache with TTL (per-process)

### Streaming
- Chat uses chunked streaming, concurrently across models; chunks are printed incrementally.


