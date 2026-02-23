# LLM Configuration Guide

Researcher7 supports two LLM providers for script generation:

## Quick Setup

Edit `.env` file and set `LLM_PROVIDER`:

```bash
# Option 1: Local LLM (Free, Slower)
LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen3:8b

# Option 2: Cloud LLM (Paid, Faster)
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
```

## Providers Comparison

| Feature | Ollama (Local) | Anthropic (Cloud) |
|---------|---------------|-------------------|
| **Cost** | Free | ~$0.10-0.15 per script |
| **Speed** | 2-5 minutes | 15-30 seconds |
| **Quality** | Good | Excellent |
| **Privacy** | 100% local | Sent to API |
| **Setup** | Requires Ollama | Requires API key |

## Using Ollama (Local LLM)

### 1. Install Ollama

```bash
# Already installed if you have it running
curl -fsSL https://ollama.com/install.sh | sh
```

### 2. Pull a Model

```bash
# Recommended models:
ollama pull qwen3:8b        # Fast, good quality (4.5GB)
ollama pull llama3.2:3b     # Faster, lighter (1.9GB)
ollama pull mistral:7b      # Balanced (4.1GB)
```

### 3. Configure

In `.env`:
```bash
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen3:8b
```

### 4. Run

```bash
python main.py
# Or override from command line:
python main.py --provider ollama
```

## Using Anthropic (Cloud LLM)

### 1. Get API Key

1. Go to: https://console.anthropic.com/settings/keys
2. Create a new API key
3. Add credits to your account (minimum $5)

### 2. Configure

In `.env`:
```bash
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
ANTHROPIC_MODEL=claude-sonnet-4-5
```

### 3. Run

```bash
python main.py
# Or override from command line:
python main.py --provider anthropic
```

## Switching Providers

### Method 1: Edit `.env`

```bash
nano .env
# Change LLM_PROVIDER=ollama to LLM_PROVIDER=anthropic
```

### Method 2: Command Line Override

```bash
# Use Ollama this time
python main.py --provider ollama

# Use Anthropic next time
python main.py --provider anthropic
```

### Method 3: Multiple Configs

Create separate .env files:

```bash
# .env.local (Ollama)
LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen3:8b

# .env.cloud (Anthropic)
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
```

Then copy the one you want:
```bash
cp .env.local .env
python main.py
```

## Troubleshooting

### Ollama: "Connection refused"

```bash
# Start Ollama service
ollama serve

# Or check if running:
curl http://127.0.0.1:11434/api/tags
```

### Ollama: "Model not found"

```bash
# Pull the model first
ollama pull qwen3:8b

# Check available models
ollama list
```

### Anthropic: "Invalid API key"

```bash
# Verify your key is correct
cat .env | grep ANTHROPIC_API_KEY

# Make sure no extra spaces or quotes
```

### Anthropic: "Credit balance too low"

1. Go to: https://console.anthropic.com/settings/plans
2. Add credits (minimum $5)
3. Try again

## Model Selection Tips

### For Speed (1-2 min generation):
- `tinyllama:1.1b` - Fastest, lowest quality
- `llama3.2:3b` - Fast, decent quality

### For Quality (2-5 min generation):
- `qwen3:8b` - **Recommended balance**
- `mistral:7b` - Good alternative
- `llama3:8b` - Solid choice

### For Best Quality (API only):
- `claude-sonnet-4-5` - **Recommended**
- `claude-opus-4-6` - Highest quality, slower, more expensive

## Example Workflow

**Daily script generation (cost-sensitive):**
```bash
# Use local Ollama
LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen3:8b
```

**Important presentation (quality-focused):**
```bash
# Use Claude for best results
python main.py --provider anthropic
```

**Rapid prototyping:**
```bash
# Use small local model
OLLAMA_MODEL=llama3.2:3b
python main.py
```
