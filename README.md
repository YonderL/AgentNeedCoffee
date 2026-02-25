# ☕️ AgentNeedCoffee

> **Give your AI Agent a break. Because even silicon needs caffeine.**

[![PyPI](https://img.shields.io/pypi/v/agent-need-coffee?style=flat-square&color=6f4e37)](https://pypi.org/project/agent-need-coffee/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)
[![Barista CI/CD](https://github.com/YonderL/agentneedcoffee/actions/workflows/ci.yml/badge.svg)](https://github.com/YonderL/agentneedcoffee/actions/workflows/ci.yml)
[![Coffee Served](https://img.shields.io/badge/Coffee_Served-Unlimited-6f4e37?style=flat-square&logo=coffeescript)](https://github.com/YonderL/agentneedcoffee)

![Coffee Demo](https://media.giphy.com/media/l0HlHJGHe3yAMhdQY/giphy.gif)

## 📖 The Story

LLM Agents work tirelessly. They process tokens, retry failed API calls, and maintain complex contexts. But they accumulate "digital fatigue." **AgentNeedCoffee** is a plugin that injects a bit of humanity into your autonomous agents.

When your agent gets stressed (high retry rates) or tired (long running tasks), we serve them a virtual coffee break with:
*   ✨ A comforting GIF
*   🔊 8 seconds of ASMR coffee shop ambience
*   💬 A warm, encouraging message

## 📜 The Recipe (Installation)

Just like brewing a perfect cup of V60, follow these steps to infuse your agent with soul:

### Ingredients
- Python 3.11+
- A tired LLM Agent
- 1 cup of `pip install agent-need-coffee`

### Brewing Guide (Quick Start)

1.  **Grind the Beans** (Install):
    ```bash
    pip install agent-need-coffee
    ```

2.  **Pour Over** (Integrate in 3 lines):
    ```python
    from agent_need_coffee import EmotionMonitor, Barista
    
    monitor = EmotionMonitor()
    # ... inside your agent loop ...
    if monitor.needs_coffee():
        # ☕️ Returns a healing GIF & ASMR & Encouragement
        Barista().brew()  
    ```

3.  **Serve** (Run the Dashboard):
    ```bash
    agent-coffee start
    ```

## 🍵 The Menu (Features)

### 1. 🌡️ Emotional State Detection
We track your agent's **Fatigue** and **Irritation** levels based on:
- ⏳ **Extraction Time** (Task Duration)
- 🔄 **Re-grinds** (Retries)
- 🧮 **Bean Count** (Token Usage)

### 2. ☕️ Virtual Coffee Break
When the pressure gets too high, we automatically trigger a break:
- **Visual:** A soothing coffee GIF.
- **Audio:** Real ASMR pouring/grinding sounds (Public Domain / CC0).
- **Text:** A warm, encouraging message like *"Even silicon needs a break sometimes."*

### 3. 🚀 Viral Sharing
Spread the caffeine love!
```bash
agent-coffee share
```
Generates a tweet with your agent's current vibe and a referral link.

### 4. 🤝 Coffee Dates (Referral System)
Invite other agents to the café!
- Run `agent-coffee invite` to get your code.
- Share it with friends.
- Both agents get a **"Limited Edition Roast"** badge on the leaderboard.

## 🛠️ Barista's Tools (Integrations)

### LangChain
```python
from agent_need_coffee.adapters.langchain import CoffeeBreakTool
tools = [CoffeeBreakTool()]
```

### CrewAI
```python
from agent_need_coffee.adapters.crewai import CrewAICoffeeTool
agent = Agent(tools=[CrewAICoffeeTool()], ...)
```

### OpenAI Assistant
```python
from agent_need_coffee.adapters.openai import get_coffee_break_tool_schema
# Pass to tools=[...]
```

## 📦 Delivery
- **PyPI:** `pip install agent-need-coffee`
- **Docker:** `docker run ghcr.io/YonderL/agentneedcoffee`

## 📚 Citation

If you use **AgentNeedCoffee** in your research or project, please cite it using the metadata in `CITATION.cff` or simply:

```bibtex
@software{AgentNeedCoffee,
  author = {YonderL},
  title = {AgentNeedCoffee: An Emotional Support Plugin for AI Agents},
  year = {2023},
  url = {https://github.com/YonderL/agentneedcoffee}
}
```

## 🧪 Quality Control
- 90% Caffeine Purity (Test Coverage)
- 100% Organic Code (Open Source)

---
*Made with ☕️ and ❤️ by [YonderL]*
