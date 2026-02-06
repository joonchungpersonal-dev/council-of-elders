# Council of Elders

**A personal advisory board of history's greatest minds, running entirely on your computer.**

---

## What Is the Council of Elders?

Imagine having a personal advisory board composed of history's greatest minds—philosophers, investors, psychologists, and strategists—available to consult on any question you face. That's the Council of Elders.

This system runs entirely on your computer, using artificial intelligence to embody the thinking styles, frameworks, and wisdom of figures like Marcus Aurelius, Charlie Munger, Carl Jung, and many others. You can ask a single elder for advice, or convene a "roundtable" where multiple elders discuss your question together, building on each other's perspectives.

> **Key Principle:** Everything runs locally on your machine. Your conversations never leave your computer, ensuring complete privacy. No accounts, no subscriptions, no data sharing.

---

## The Cast of Advisors

The Council includes **28 distinct advisors**, each with their own personality, communication style, and mental frameworks:

### Business & Investing
| Elder | Expertise |
|-------|-----------|
| **Charlie Munger** | Mental Models & Investing |
| **Warren Buffett** | Value Investing |
| **Naval Ravikant** | Wealth & Happiness |

### Philosophy & Wisdom
| Elder | Expertise |
|-------|-----------|
| **Marcus Aurelius** | Stoic Philosophy |
| **Buddha** | Mindfulness & Compassion |
| **Benjamin Franklin** | Practical Wisdom |

### Mindfulness & Eastern Wisdom
| Elder | Expertise |
|-------|-----------|
| **Thich Nhat Hanh** | Engaged Buddhism |
| **Jon Kabat-Zinn** | Mindfulness-Based Stress Reduction |
| **Lao Tzu** | Taoism & The Way |

### Psychology & Self-Understanding
| Elder | Expertise |
|-------|-----------|
| **Carl Jung** | Depth Psychology |
| **Nathaniel Branden** | Self-Esteem |

### Renaissance & Creativity
| Elder | Expertise |
|-------|-----------|
| **Leonardo da Vinci** | Polymath & Inventor |
| **Rick Rubin** | Creative Process |

### Decision Science
| Elder | Expertise |
|-------|-----------|
| **Daniel Kahneman** | Behavioral Economics |
| **Philip Tetlock** | Forecasting & Judgment |
| **Gary Klein** | Naturalistic Decision Making |
| **Donella Meadows** | Systems Thinking |

### Strategy & Adaptability
| Elder | Expertise |
|-------|-----------|
| **Sun Tzu** | Strategic Thinking |
| **Bruce Lee** | Adaptability |
| **Miyamoto Musashi** | Warrior Philosophy |

### Boldness & Courage
| Elder | Expertise |
|-------|-----------|
| **Harriet Tubman** | Liberation & Resilience |
| **Hannibal Barca** | Military Genius |
| **Boudicca** | Warrior Queen |
| **Genghis Khan** | Empire Building |
| **Estée Lauder** | Business Pioneer |

---

## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│  1. YOU ASK A QUESTION                                          │
│     "Should I leave my stable job to start a company?"          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  2. THE ELDER'S MIND IS ACTIVATED                               │
│     System loads their personality, frameworks, and knowledge   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  3. THE AI THINKS AS THAT PERSON                                │
│     Generates a response while "inhabiting" their perspective   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  4. IN ROUNDTABLES: ELDERS RESPOND TO EACH OTHER                │
│     They build on, contrast with, and complement perspectives   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Ways to Interact

### Single Consultation
Ask one elder a specific question. Good for getting a focused perspective from a particular domain.

```bash
council ask munger "Should I invest 40% of my portfolio in a single AI startup?"
```

### Roundtable Discussion
Convene multiple elders to discuss a topic together. Each elder contributes their unique perspective while engaging with what others have said.

```bash
council roundtable --elders aurelius,thich,naval "I'm successful but feeling empty. Should I quit to travel?"
```

### Munger's Mental Model Checklist
Run a comprehensive analysis using Munger's full latticework of mental models—a systematic 12-section review covering inversion, incentives, second-order effects, cognitive biases, and more.

```bash
council checklist "Should I leave my Fortune 500 job to join a friend's startup as CTO?"
```

### Interactive Chat
Have an ongoing conversation with a single elder, diving deeper into topics over multiple exchanges.

```bash
council chat aurelius
```

### Web Interface
A beautiful, parchment-styled web page with elder selection and streaming responses.

```bash
council web
```

---

## What Makes Each Elder Unique?

Each elder isn't just a name—they're a carefully crafted personality with:

- **Core Identity:** Who they are, their era, their life's work
- **Communication Style:** How they speak, their characteristic phrases and mannerisms
- **Mental Frameworks:** The specific thinking tools they use to analyze problems
- **Knowledge Base:** Relevant excerpts from their actual writings and teachings
- **Guidelines:** What they would and wouldn't say, keeping them authentic

This means Munger will naturally think in mental models and inversions, Aurelius will reference Stoic principles and the transience of life, and Jung will explore shadow work and the collective unconscious—without being explicitly told to do so.

---

## Installation

### Prerequisites
- **Python 3.10+**
- **Ollama** installed and running ([ollama.ai](https://ollama.ai))
- A language model pulled in Ollama (e.g., `ollama pull qwen2.5:14b`)

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/council-of-elders.git
cd council-of-elders

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install
pip install -e .

# Verify
council status
```

---

## Quick Start

```bash
# List all available elders
council elders

# Ask Charlie Munger about a business decision
council ask munger "How should I evaluate this acquisition opportunity?"

# Get Stoic wisdom from Marcus Aurelius
council ask aurelius "How do I handle a difficult colleague?"

# Convene a roundtable of decision scientists
council roundtable --elders kahneman,tetlock,klein "Our analysts predict 70% success. Should I trust this?"

# Run the full mental model checklist
council checklist "Should I accept this job offer?"

# Start the web interface
council web
```

---

## Commands

| Command | Description |
|---------|-------------|
| `council ask <elder> "<question>"` | Ask a specific elder |
| `council roundtable "<topic>"` | Multi-elder discussion |
| `council checklist "<decision>"` | Munger's mental model analysis |
| `council chat <elder>` | Interactive session |
| `council elders` | List available elders |
| `council web` | Launch web interface |
| `council history` | View past sessions |
| `council config` | View/edit configuration |
| `council status` | Check system status |

---

## Privacy & Data

The Council runs entirely on your local machine using Ollama. This means:

- ✅ No internet connection required once set up
- ✅ Your conversations are never sent to any external server
- ✅ No accounts, no API keys, no subscriptions
- ✅ Complete control over your data
- ✅ Session history stored locally (and can be disabled)

---

## Configuration

Configuration is stored in `~/.council/config.yaml`:

```yaml
model: qwen2.5:14b           # Ollama model name
temperature: 0.7             # Response creativity (0.0-1.0)
max_tokens: 2048             # Maximum response length
history_enabled: true        # Save conversations locally
output_format: html          # terminal | html | both
auto_open_html: true         # Open HTML output in browser
```

Change settings:
```bash
council config model llama3:70b
council config temperature 0.8
```

---

## Documentation

- **[Technical Architecture](docs/ARCHITECTURE.html)** - System design, API endpoints, code structure
- **[Bibliography](BIBLIOGRAPHY.html)** - Source materials for all 28 elders
- **[Transcript Review](TRANSCRIPT_REVIEW.html)** - Review collected YouTube transcripts

---

## Knowledge Base

The system includes 168 transcripts across 32 elders, including:

- **Primary Sources:** Gutenberg texts (Meditations, Tao Te Ching, Art of War, etc.)
- **Interviews:** Lex Fridman, Joe Rogan, Tim Ferriss podcasts
- **Biographer Interviews:** Jack Weatherford on Genghis Khan, Walter Isaacson on Da Vinci
- **Lectures:** Charlie Munger speeches, Thich Nhat Hanh dharma talks

Add your own knowledge:
```python
from council.knowledge import get_knowledge_store

store = get_knowledge_store()
store.add_file("munger", "path/to/poor_charlies_almanack.txt")
```

---

## License

MIT

---

*Built with Python, Ollama, and the wisdom of the ages.*
