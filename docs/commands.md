## Commands

### Global Flags
- `--base-url` override API base URL
- `--timeout` request timeout seconds
- `--no-cache` disable GET cache
- `--no-color` disable colored output
- `--format` table|json|yaml default format

### Auth
```bash
evalarena auth login
evalarena auth logout
```

### Ping
```bash
evalarena ping
```

### Config
```bash
evalarena config show
evalarena config set base_url https://...
evalarena config set chat.default_models gpt-4o,claude-3-5-sonnet
```

### Models
```bash
evalarena models list --type all --limit 20 --evals coding
evalarena models columns --type vlm
evalarena models search "Claude"
```

### Model
```bash
evalarena model show "Claude 3.5 Sonnet (new)"
```

### Compare
```bash
evalarena compare "GPT-4o" "Claude 3.5 Sonnet (new)" --diff percent
```

### Charts
```bash
evalarena charts bar mmlu --type all --top 10
evalarena charts pareto mmlu input_price_per_1M_tokens_USD
```

### Chat
```bash
evalarena chat --list
evalarena chat --set-models gpt-4o,claude-3-5-sonnet
evalarena chat --prompt "Explain quantum computing" --models gpt-4o,claude-3-5-sonnet
```


