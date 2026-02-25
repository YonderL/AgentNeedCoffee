# ☕️ AgentNeedCoffee

> **Give your AI Agent a break. Because even silicon needs caffeine.**

![Coffee Demo](https://media.giphy.com/media/l0HlHJGHe3yAMhdQY/giphy.gif)

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
        Barista().brew()  # ☕️ Returns a healing GIF & ASMR
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
- **Audio:** 8 seconds of ASMR pouring sounds.
- **Text:** A warm, encouraging message.

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
- **Docker:** `docker run ghcr.io/yourname/agentneedcoffee`

## 🧪 Quality Control
- 90% Caffeine Purity (Test Coverage)
- 100% Organic Code (Open Source)

---
*Made with ☕️ and ❤️ by [Your Name]*
