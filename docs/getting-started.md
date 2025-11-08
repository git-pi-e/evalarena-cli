## Getting Started

This repo contains both the legacy Python CLI (now under `evalarena_py/`) and the new Go CLI (under `go/`).

### Prerequisites
- Go 1.22+
- Optional: Python 3.10+ if you still need to run the legacy CLI/tests

### Build and Run (Go CLI)
```bash
go build -o bin/evalarena ./src/cmd/evalarena
./bin/evalarena ping
```

### Configure
Copy `src/env.example` to `.env` and edit as needed. You can also set env vars directly.
```bash
cp src/env.example .env
./bin/evalarena auth login
```

### Common Commands
```bash
./bin/evalarena models list --type all --limit 10
./bin/evalarena model show "Claude 3.5 Sonnet (new)"
./bin/evalarena compare "GPT-4o" "Claude 3.5 Sonnet (new)" --diff percent
./bin/evalarena charts bar mmlu --type all --top 10
./bin/evalarena chat --prompt "Explain quantum computing" --models gpt-4o,claude-3-5-sonnet
```


