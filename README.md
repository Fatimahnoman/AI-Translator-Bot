<div align="center">

# 🌐 AI Translator Bot

**An AI-powered translator chatbot with dual LLM support, premium UI, and 14 language translations.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Chainlit](https://img.shields.io/badge/Chainlit-2.11-000000?style=for-the-badge&logo=chainlit&logoColor=white)](https://chainlit.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-22C55E?style=for-the-badge)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-4F8CFF?style=for-the-badge)](https://github.com/Fatimahnoman/AI-Translator-Bot/pulls)

---

A premium chatbot that translates text into **14 languages** using **Gemini** and **OpenRouter** AI models, with a professional dark/light UI built on Chainlit.

</div>

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🤖 **Dual AI Providers** | Switch between Gemini and OpenRouter with `/model` |
| 🌍 **14 Languages** | English, Urdu, Arabic, French, German, Spanish, Hindi, Japanese, Chinese, Turkish, Italian, Russian, Portuguese, Korean |
| 🎨 **Premium UI** | Glassmorphism dark mode + full light mode |
| 🔒 **Security** | Input sanitization, XSS protection, rate limiting |
| ⚡ **Fast** | Instant translations with streaming-ready architecture |
| 🗄️ **Cloud Database** | Chat history persisted with Neon PostgreSQL |
| 🐳 **Docker Ready** | One-command deployment with Dockerfile |
| 📊 **35+ Tests** | Unit + integration tests with pytest |

## 🚀 Quick Start

### Prerequisites
- **Python 3.11+**
- **API Key**: [Gemini](https://aistudio.google.com/apikey) or [OpenRouter](https://openrouter.ai/keys)

### Setup

```bash
# Clone
git clone https://github.com/Fatimahnoman/AI-Translator-Bot.git
cd AI-Translator-Bot

# Virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux

# Install
pip install -r requirements.txt

# Configure
copy .env.example .env       # Windows
cp .env.example .env         # macOS/Linux
```

Edit `.env` with your keys:
```env
GEMINI_API_KEY=your_key_here
OPENROUTER_API_KEY=your_key_here
NEON_DATABASE_URL=your_neon_url_here   # Optional
```

### Run
```bash
python -m chainlit run trans-agent.py
```

App opens at **http://localhost:8000**

## 📋 Commands

| Command | Description |
|---------|-------------|
| `/model gemini` | Switch to Gemini provider |
| `/model openrouter` | Switch to OpenRouter provider |
| `/change` | Change target language |
| `/help` | Show all commands |

## 🗣️ How It Works

```
User: "hello"
Bot:  "Hey there! Welcome to TranslateHub 🌐
       Which language would you like to translate into today?"

User: "urdu"
Bot:  "✅ Language selected: Urdu
       Now enter the text you want to translate into Urdu."

User: "How are you?"
Bot:  "🌐 Translated to Urdu:
       آپ کیسے ہیں؟"
```

## 🏗️ Project Structure

```
AI-Translator-Bot/
├── trans-agent.py           # Main app — providers, logic, handlers
├── public/
│   ├── chatgpt-theme.css    # Premium dark/light theme
│   └── interactions.js      # Custom UI interactions
├── tests/
│   ├── test_core.py         # Unit tests (17 tests)
│   └── test_integration.py  # Integration tests (18 tests)
├── .chainlit/
│   └── config.toml          # Chainlit configuration
├── .github/
│   └── workflows/
│       └── ci.yml           # GitHub Actions CI
├── requirements.txt         # Dependencies
├── Dockerfile               # Docker deployment
└── .env.example             # API key template
```

## 🧪 Testing

```bash
python -m pytest tests/ -v
```

```
tests/test_core.py::TestValidateLanguage          PASSED
tests/test_core.py::TestSanitizeInput             PASSED
tests/test_core.py::TestRateLimiting              PASSED
tests/test_integration.py::TestFullTranslation    PASSED
tests/test_integration.py::TestSanitization       PASSED
======================== 35 passed ========================
```

## 🐳 Docker

```bash
docker build -t ai-translator-bot .
docker run -p 8000:8000 -e GEMINI_API_KEY=your_key ai-translator-bot
```

## 🛡️ Security

- **XSS Protection** — All user inputs sanitized with `html.escape()`
- **Rate Limiting** — 15 requests/minute per user
- **Input Validation** — Strict language whitelist, max length enforced
- **No secrets in code** — `.env` excluded via `.gitignore`

## 📦 Tech Stack

| Technology | Purpose |
|------------|---------|
| [Python](https://python.org) | Backend language |
| [Chainlit](https://chainlit.io) | Chat UI framework |
| [LiteLLM](https://litellm.ai) | Unified LLM API |
| [Gemini](https://ai.google.dev) | Primary AI provider |
| [OpenRouter](https://openrouter.ai) | Secondary AI provider |
| [Neon PostgreSQL](https://neon.tech) | Cloud database |
| [GitHub Actions](https://github.com/features/actions) | CI/CD |

## 👩‍💻 Author

**Fatimah Noman**

## 📄 License

MIT License — feel free to use and modify.

---

<div align="center">

**If this project helped you, give it a ⭐ on GitHub!**

</div>
