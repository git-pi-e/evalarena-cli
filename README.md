# EvalArena CLI

A powerful command-line interface for comparing and analyzing AI model benchmarks from [EvalArena](https://evalarena.ai).

## Features

- 📊 **List and filter models** across different categories (all, small, VLM, chat)
- 🔍 **Search models** by name with fuzzy matching
- 📈 **Compare models** side-by-side with diff calculations
- 💬 **Multi-model chat** - Send prompts to multiple models simultaneously
- 📉 **Generate terminal charts** (bar charts and Pareto frontiers)
- 🎨 **Rich terminal UI** with colored output and tables
- ⚡ **Fast HTTP caching** with ETags and conditional requests
- 🔐 **Secure authentication** with keyring storage
- 🛠️ **Extensible architecture** ready for future features

## Installation

### Using pipx (Recommended)

```bash
pipx install evalarena
```

### Using pip

```bash
pip install evalarena
```

### From Source

```bash
git clone https://github.com/evalarena/evalarena-cli.git
cd evalarena-cli
pip install -e .
```

## Tab Completion (Recommended)

EvalArena CLI includes intelligent tab completion for all commands and option values:

```bash
# Install completion for your shell
evalarena --install-completion

# Show completion script (for manual setup)
evalarena --show-completion
```

**Restart your terminal** after installation, then enjoy tab completion:

- `evalarena <TAB>` → All commands (models, model, compare, chat, charts, etc.)
- `evalarena models list --type <TAB>` → Model types (all, small, vlm, chat)
- `evalarena models list --evals <TAB>` → Categories (math, coding, knowledge, multimodal, etc.)
- `evalarena compare model1 model2 --diff <TAB>` → Diff modes (none, absolute, percent)
- `evalarena chat --list` → Show available chat models for easy copy-paste
- `evalarena charts bar --normalize <TAB>` → Normalization modes (none, zscore, minmax)

**Smart completions available for:**
- ✅ All command names and subcommands  
- ✅ Model types: `all`, `small`, `vlm`, `chat`
- ✅ Evaluation categories per model type
- ✅ Output formats: `table`, `json`, `yaml`
- ✅ Benchmark names: `mmlu`, `humaneval`, `math`, etc.
- ✅ Config keys and values

## Quick Start

```bash
# Check connectivity
evalarena ping

# List all models
evalarena models list

# List VLM models with custom columns
evalarena models list --type vlm --columns name,creator,mmmu,mathvista

# Search for models
evalarena models search "gpt-4"

# Show model details
evalarena model show "gpt-4o"

# Compare two models
evalarena compare "gpt-4o" "claude-3.5-sonnet"

# Chat with multiple models
evalarena chat "Explain quantum computing" --models "gpt-4o,claude-3.5-sonnet"

# Generate bar chart
evalarena charts bar --models "gpt-4o,claude-3.5-sonnet" --columns mmlu,humaneval

# Generate Pareto frontier chart
evalarena charts pareto mmlu input_price_per_1M_tokens_USD --table
```

## Commands

### Authentication

```bash
# Login (stores token securely in keyring)
evalarena auth login

# Logout
evalarena auth logout
```

### Configuration

```bash
# Show current configuration
evalarena config show

# Set configuration values
evalarena config set output_format json
evalarena config set chart.width 120
evalarena config set default_columns "name,creator,mmlu,humaneval"
```

### Models

```bash
# List models with options
evalarena models list [OPTIONS]

Options:
  --type [all|small|vlm|chat]     Model type to list
  --sort-by TEXT                  Field to sort by (default: name)
  --order [asc|desc]             Sort order (default: asc)
  --page INTEGER                  Page number for pagination
  --limit INTEGER                 Number of models to show
  --columns TEXT                  Comma-separated columns to display
  --format [table|json|yaml]     Output format
  --no-cache                     Bypass cache

# Examples
evalarena models list --type small --sort-by mmlu --order desc --limit 10
evalarena models list --columns "name,creator,mmlu,humaneval,active_params_in_billion"
evalarena models list --format json > models.json

# Show available columns
evalarena models columns --type vlm

# Search for models
evalarena models search "phi" --type small --fuzzy
```

### Model Details

```bash
# Show detailed model information
evalarena model show <model-name-or-id>

# Examples
evalarena model show "gpt-4o"
evalarena model show "507f1f77bcf86cd799439011"  # By ID
evalarena model show --format json "claude-3.5-sonnet"
```

### Model Comparison

```bash
# Compare models
evalarena compare <model1> <model2> [model3...] [OPTIONS]

Options:
  --type [all|small|vlm|chat]     Model type to search in
  --columns TEXT                  Benchmarks to compare
  --diff [none|absolute|percent]  Show differences (for 2 models)
  --format [table|json|yaml]     Output format

# Examples
evalarena compare "gpt-4o" "claude-3.5-sonnet"
evalarena compare "gpt-4o" "claude-3.5-sonnet" --diff percent
evalarena compare "phi-4" "llama-3.3-70b" --columns mmlu,humaneval,math
evalarena compare "model1" "model2" "model3" --format json
```

### Multi-Model Chat

```bash
# Chat with multiple models simultaneously
evalarena chat --prompt <prompt> [OPTIONS]

Options:
  --prompt, -p TEXT               Prompt to send to chat models
  --models, -m TEXT               Comma-separated model IDs to compare (overrides defaults)
  --set-models TEXT               Persist default chat models (comma-separated)
  --clear-models                  Clear default chat models
  --list                          List available chat models
  --no-progress                   Disable live progress display

# Manage default chat models
evalarena chat --set-models "gpt-4o,claude-3.5-sonnet"
evalarena chat --clear-models

# Use saved defaults with a one-liner prompt
evalarena chat --prompt "Explain quantum computing"

# Override defaults for a one-off run
evalarena chat --prompt "Write a binary search in Python" --models "gpt-4o,gemini-1.5-pro"

# List available models for chat
evalarena chat --list
```

**Features:**
- ✨ **Real-time streaming** from multiple models simultaneously
- 🎨 **Side-by-side display** with live progress indicators  
- 📱 **Clean terminal UI** with model names and creator info
- ⚡ **Async execution** for maximum performance
- 🚫 **Interrupt support** with Ctrl+C
- 📋 **Final summary** with complete responses

### Charts

#### Bar Charts

```bash
evalarena charts bar [OPTIONS]

Options:
  --models TEXT                   Comma-separated model names
  --columns TEXT                  Benchmarks to chart (default: mmlu)
  --type [all|small|vlm|chat]     Model type (if --models not specified)
  --normalize [none|zscore|minmax] Normalization method
  --top INTEGER                   Show only top N models
  --width INTEGER                 Chart width
  --height INTEGER                Chart height

# Examples
evalarena charts bar --models "gpt-4o,claude-3.5-sonnet,gemini-pro" --columns mmlu
evalarena charts bar --type small --top 5 --columns mmlu,humaneval
evalarena charts bar --columns "mmlu,mmlu_pro,humaneval" --normalize zscore
```

#### Pareto Frontier Charts

```bash
evalarena charts pareto <quality-metric> <cost-metric> [OPTIONS]

Options:
  --type [all|small|vlm|chat]     Model type to analyze
  --width INTEGER                 Chart width
  --height INTEGER                Chart height
  --table                        Also show frontier table

# Examples
evalarena charts pareto mmlu input_price_per_1M_tokens_USD --table
evalarena charts pareto humaneval active_params_in_billion --type small
evalarena charts pareto mmmu_val input_price_per_1M_tokens_USD --type vlm
```

## Configuration

The CLI stores configuration in `~/.config/evalarena/config.toml` (or equivalent on Windows/macOS).

### Configuration Options

```toml
# API settings
base_url = "https://evalarena.ai"
timeout_s = 15

# Output settings
output_format = "table"  # table, json, yaml
no_color = false

# Default columns for model listings
default_columns = [
    "name",
    "creator", 
    "mmlu",
    "mmlu_pro",
    "humaneval",
    "active_params_in_billion",
    "input_price_per_1M_tokens_USD"
]

# Cache settings
cache_enabled = true
cache_ttl_seconds = 3600

# Chart settings
[chart]
width = 100
height = 30
normalize = "none"

# Chat settings
[chat]
default_models = []
```

### Environment Variables

All configuration can be overridden with environment variables:

```bash
export EVALARENA_BASE_URL="https://api.evalarena.ai"
export EVALARENA_TOKEN="your-api-token"
export EVALARENA_TIMEOUT_S=30
export EVALARENA_OUTPUT_FORMAT="json"
export EVALARENA_NO_COLOR=true
```

## Available Columns

### Standard Fields
- `name` - Model name
- `creator` - Model creator/organization
- `active_params_in_billion` - Number of parameters (billions)
- `input_price_per_1M_tokens_USD` - Input pricing per 1M tokens
- `output_price_per_1M_tokens_USD` - Output pricing per 1M tokens
- `max_input_tokens` - Maximum input token limit
- `max_output_tokens` - Maximum output token limit

### Benchmark Fields

#### Math & Reasoning
- `aime_2024`, `aime_2025` - AIME (Olympiad-level math)
- `math`, `math500` - MATH competition problems
- `gpqa_diamond` - PhD-level science questions

#### Coding
- `humaneval` - Code generation
- `swe_bench_verified` - GitHub issues/agentic coding
- `live_code_bench_v5` - LiveCodeBench v5
- `codeforces` - Algorithmic/competitive programming
- `aider_polyglot_diff` - Code editing

#### Language & Knowledge  
- `mmlu`, `mmlu_pro` - Language understanding
- `simple_qa` - Factuality benchmark
- `hle` - Humanity's Last Exam

#### Multimodal (VLM)
- `mmmu`, `mmmu_pro` - Multimodal understanding
- `mathvista` - Visual math reasoning  
- `doc_vqa` - Document visual QA
- `chart_qa` - Chart visual QA
- `blink` - Multi-image perception

#### Agent & Interaction
- `osworld` - Computer environment interaction
- `webvoyager` - Browser use
- `screenspot_pro` - GUI grounding
- `tau_bench_airline`, `tau_bench_retail` - Agentic tool use

Use `evalarena models columns --type <type>` to see all available columns for a specific model type.

## Examples

### Find the best small models for coding

```bash
evalarena models list --type small --sort-by humaneval --order desc --limit 5 \
  --columns "name,creator,humaneval,swe_bench_verified,active_params_in_billion"
```

### Compare cost vs performance

```bash
evalarena charts pareto mmlu input_price_per_1M_tokens_USD --table
```

### Export model data for analysis

```bash
evalarena models list --format json --limit 100 > models.json
evalarena models list --type vlm --format yaml > vlm_models.yaml
```

### Find models by capability

```bash
# Best multimodal models
evalarena models list --type vlm --sort-by mmmu --order desc

# Most cost-effective models
evalarena models list --sort-by input_price_per_1M_tokens_USD --order asc

# Search for specific model families
evalarena models search "claude" --fuzzy
evalarena models search "llama" --type small
```

### Generate comparison charts

```bash
# Compare top 3 models across multiple benchmarks
evalarena charts bar --top 3 --columns "mmlu,humaneval,math" --normalize zscore

# Compare specific models
evalarena charts bar --models "gpt-4o,claude-3.5-sonnet,gemini-2.0-flash" \
  --columns "mmlu,mmlu_pro,humaneval,math"
```

### Interactive multi-model chat

```bash
# Compare reasoning across different models
evalarena chat "Explain the difference between supervised and unsupervised learning" \
  --models "gpt-4o,claude-3.5-sonnet,gemini-1.5-pro"

# Test coding capabilities
evalarena chat "Write a Python function to implement binary search" \
  --models "gpt-4o,claude-3.5-sonnet"

# Compare problem-solving approaches
evalarena chat "How would you approach optimizing a slow database query?" \
  --models "gpt-4o,claude-3.5-haiku,llama-3.1-70b"
```

## Cache Management

```bash
# Clear HTTP cache
evalarena clear-cache

# Bypass cache for fresh data
evalarena models list --no-cache

# Check cache statistics
evalarena config show  # Shows cache stats
```

## Output Formats

### Table (Default)
Rich formatted tables with colors and alignment.

### JSON
Machine-readable JSON output for scripting:

```bash
evalarena models list --format json | jq '.[] | select(.mmlu > 80)'
```

### YAML  
Human-readable YAML output:

```bash
evalarena model show "gpt-4o" --format yaml
```

## Global Options

Available on all commands:

- `--base-url TEXT` - Override API base URL
- `--timeout INTEGER` - Override request timeout
- `--no-cache` - Disable HTTP caching
- `--no-color` - Disable colored output
- `--verbose` - Enable verbose output

## Error Handling

The CLI provides helpful error messages and suggestions:

```bash
# Unknown model
$ evalarena model show "unknown-model"
Error: Model not found: unknown-model

# Ambiguous model name
$ evalarena model show "gpt"
Error: Ambiguous model name 'gpt'. Did you mean one of: gpt-4o, gpt-4-turbo, gpt-3.5-turbo

# Invalid benchmark
$ evalarena models list --columns "invalid_benchmark" 
Error: Unknown benchmark key 'invalid_benchmark'. Similar keys: humaneval, mmlu, mmlu_pro
```

## Future Features

- 🧪 **Prompt evaluation** - Run prompts against multiple models (planned)
- 📊 **Custom benchmarks** - Upload and compare custom evaluation results
- 🔄 **Model tracking** - Track model updates and version changes
- 📱 **Mobile-friendly output** - Optimized display for smaller terminals

## Development

### Setup

```bash
git clone https://github.com/evalarena/evalarena-cli.git
cd evalarena-cli
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
pytest --cov=evalarena  # With coverage
```

### Code Quality

```bash
black .                 # Format code
ruff check .           # Lint code  
mypy evalarena         # Type checking
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

- 📖 Documentation: [docs.evalarena.ai](https://docs.evalarena.ai)
- 🐛 Issues: [GitHub Issues](https://github.com/evalarena/evalarena-cli/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/evalarena/evalarena-cli/discussions)
- 🌐 Website: [evalarena.ai](https://evalarena.ai)

---

Built with ❤️ by the EvalArena team
