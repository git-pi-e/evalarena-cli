EvalArena CLI (Go)

This is the Go rewrite of the EvalArena CLI. It mirrors the Python tool's features while using a single binary for fast startup and streaming I/O.

### Quick Start

1) Requirements: Go 1.22+

2) Build the CLI from repo root:

```
go build -o bin/evalarena ./src/cmd/evalarena
```

3) Prepare environment (you can also set env variables directly):

```
cp src/env.example .env
```

4) Authenticate (stores token in `.env`):

```
./bin/evalarena auth login
```

5) Check connectivity:

```
./bin/evalarena ping
```

### Configuration

Configuration is loaded from environment variables and `.env` (highest precedence environment overrides `.env`). Key variables:

- `EVALARENA_BASE_URL` (default: https://evalarena-backend-89846023945.us-central1.run.app)
- `EVALARENA_TIMEOUT_S` (default: 15)
- `EVALARENA_TOKEN` (set via `auth login`)
- `EVALARENA_OUTPUT_FORMAT` (table|json|yaml; default: table)
- `EVALARENA_NO_COLOR` (true|false)
- `EVALARENA_DEFAULT_COLUMNS` (CSV)
- `EVALARENA_CACHE_ENABLED` (true|false; default: true)
- `EVALARENA_CACHE_TTL_SECONDS` (default: 3600)
- `EVALARENA_CHART_WIDTH` (default: 100)
- `EVALARENA_CHART_HEIGHT` (default: 30)
- `EVALARENA_CHART_NORMALIZE` (none|zscore|minmax)
- `EVALARENA_CHAT_DEFAULT_MODELS` (CSV of chat model IDs)

### Commands

- `auth login|logout` – Manage API token (stored in `.env`)
- `ping` – Health check
- `config show|set` – View and update configuration
- `models list` – List and filter models
- `models columns` – Show available columns for a model type
- `models search <query>` – Search models by name
- `model show <id|name>` – Show detailed model information
- `compare <modelA> <modelB> [more...]` – Compare models, supports `--columns` and `--diff`
- `charts bar <metric>` – ASCII bar chart for a metric (with `--type`, `--normalize`, `--top`)
- `charts pareto <quality> [cost]` – Pareto frontier for quality vs cost (blended cost default)
- `chat` – Chat with one or more models, supports streaming output


