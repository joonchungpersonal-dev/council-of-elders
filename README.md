# Council of Elders

A local AI advisory system that embodies the wisdom of great thinkers. All processing happens locally using Ollama - your conversations stay on your machine.

## Installation

```bash
# Clone or download this repository
cd council-of-elders

# Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install the package
pip install -e .
```

## Prerequisites

- **Python 3.10+**
- **Ollama** installed and running (https://ollama.ai)
- A language model pulled in Ollama (e.g., `ollama pull qwen2.5:14b`)

## Quick Start

```bash
# Activate the environment
source venv/bin/activate

# List available elders
council elders

# Ask a specific elder
council ask munger "Should I invest in this startup opportunity?"

# Ask Buddha about inner peace
council ask buddha "How do I find peace with uncertainty?"

# Convene a roundtable
council roundtable --elders munger,buffett "How should I evaluate a business?"

# Interactive chat session
council chat aurelius
```

## Available Elders

| ID | Elder | Domain |
|----|-------|--------|
| `munger` | Charlie Munger | Investing, Mental Models |
| `buffett` | Warren Buffett | Business, Value Investing |
| `aurelius` | Marcus Aurelius | Stoicism, Leadership |
| `franklin` | Benjamin Franklin | Pragmatic Wisdom, Self-Improvement |
| `bruce_lee` | Bruce Lee | Martial Arts Philosophy, Self-Expression |
| `musashi` | Miyamoto Musashi | Strategy, Discipline |
| `sun_tzu` | Sun Tzu | Strategic Thinking |
| `buddha` | Siddhartha Gautama | Mindfulness, Inner Peace |

## Commands

| Command | Description |
|---------|-------------|
| `council ask <elder> "<question>"` | Ask a specific elder |
| `council chat <elder>` | Interactive session |
| `council roundtable "<topic>"` | Multi-elder discussion |
| `council elders` | List available elders |
| `council history` | View past sessions |
| `council config` | View/edit configuration |
| `council models` | List Ollama models |
| `council status` | Check system status |

## Configuration

Configuration is stored in `~/.council/config.yaml`:

```yaml
model: qwen2.5:14b          # Ollama model to use
temperature: 0.7            # Response creativity (0-1)
max_tokens: 2048            # Maximum response length
history_enabled: true       # Save conversation history
```

Change settings with:
```bash
council config model llama3:70b
council config temperature 0.8
```

## Privacy

- All processing happens locally via Ollama
- Conversations are stored in `~/.council/history/`
- No data is sent to external servers
- Disable history with `council config history_enabled false`

## Adding Custom Knowledge (RAG)

You can enhance elders with additional knowledge from texts:

```python
from council.knowledge import get_knowledge_store

store = get_knowledge_store()
store.add_file("munger", "path/to/poor_charlies_almanack.txt")
```

## License

MIT
