# MLBB Coach AI

**Intelligent Coaching for Mobile Legends: Bang Bang Players**

---

## 🎯 Project Goal

MLBB Coach AI is an experimental AI-powered coaching tool for Mobile Legends: Bang Bang players. It analyzes match stats and generates actionable feedback to help players improve their gameplay, decision-making, and overall strategy.

This project is designed for players seeking improvement without relying on toxic in-game environments or vague advice. It aims to simulate what a smart, non-tilted coach would tell you—based on real data.

## 📖 Subject Domain

- **Mobile Legends: Bang Bang (MLBB)** – specifically focused on gameplay strategy, performance metrics, and role-specific tactics
- **Machine Learning & Python Development** – integrating AI techniques (rule-based and eventually ML-based)
- **UX/UI Design** – delivering feedback in a clean, clear interface (CLI to web)

## 🧠 What It Does

- **Accepts input match data** (as JSON or manual entry)
- **Analyzes performance** (KDA, positioning, gold per minute, etc.)
- **Identifies common mistakes** or weak patterns
- **Generates role-specific coaching feedback** (starting with Marksman or Jungler roles)
- **Outputs a readable performance report**

## 🧩 Project Components

### 1. Stat Input System
- Start with static JSON-style inputs
- Eventually allow manual entry or future integration with replays/screenshots

### 2. Game Logic Engine
- Python-based system that interprets stats and produces coaching advice
- Uses hardcoded strategy rules in MVP
- ML-based performance prediction for later versions

### 3. Feedback Generator
- Translates analysis into readable, role-specific tips
- **Examples:**
  - *"You initiated 4 teamfights solo—coordinate better with tanks"*
  - *"Gold efficiency drops drastically after 6 minutes—consider lane rotation"*

### 4. User Interface
- **V1:** CLI
- **V2:** Web interface

## 📁 Project Structure (MVP Phase)

```
mlbb-coach-ai/
├── main.py                 # CLI-based interface for entering/viewing match stats
├── coach.py               # Core logic for interpreting match data and producing coaching output
├── data/
│   └── sample_match.json  # Example match data structure used for testing and feedback generation
├── rules/
│   └── marksman.py        # Role-specific strategy rules (e.g., marksman.py, jungler.py)
├── utils.py               # Helper functions (data validation, formatting, etc.)
└── README.md
```

| Component | Description |
|-----------|-------------|
| `main.py` | CLI-based interface for entering/viewing match stats |
| `coach.py` | Core logic for interpreting match data and producing coaching output |
| `data/sample_match.json` | Example match data structure used for testing and feedback generation |
| `rules/` | Folder for role-specific strategy rules (e.g., `marksman.py`, `jungler.py`) |
| `utils.py` | Helper functions (data validation, formatting, etc.) |

## 📌 Project Status

- 🔧 **MVP development phase** (CLI version, basic rule-based logic)
- 📚 **Learning and building** in real-time
- 🔜 **Future plans:**
  - ML model integration for performance prediction
  - Web-based interface (React, Tailwind, GSAP)
  - Role-specific dashboards
  - Data scraping/automation from MLBB API or replay uploads (if possible)

## 🤖 Tech Stack

### Current (MVP)
- **Python 3.x**
- **JSON** for mock input
- **CLI** for MVP interface

### Planned
- **Frontend:** React + Tailwind + GSAP
- **ML Libraries:** scikit-learn, pandas
- **Data Processing:** NumPy, matplotlib

## ⚙️ Development Timeline

| Week | Goal |
|------|------|
| **Week 1** | Prep: Learn Python basics + define MVP scope |
| **Week 2** | Build CLI/app core + learn data processing |
| **Week 3** | Learn basic ML (regression/classification) + test models on sample replays/stats |
| **Week 4** | Add output/report feature + basic UI (CLI or web) |
| **Week 5** | Refine, test with friends, maybe integrate TikTok feedback for exposure |
| **Week 6** | Polish, deploy MVP, write Medium post or devlog |

## 🧠 About the Developer

This project is being built by **Rhine (Les)**—a 400+ star Mythical-ranked MLBB player with a passion for AI, game improvement, and creating tools to help others play smarter, not harder. Currently self-learning Python and Machine Learning while designing and developing this MVP.

## 💡 Why It Matters

Most players don't understand where they fail—especially in solo queue hell. Current tools are limited or purely statistical. This project provides actionable, human-friendly feedback, backed by real gameplay patterns and tactical knowledge.

You're combining your deep game experience with AI to solve a real pain point: learning from mistakes without rage-quitting or relying on unreliable teammates.

---

## 🚀 Alternative Project Names

- **NeuraStrat**
- **CoachBot Alpha**
- **MLBB Coach AI** (current)

*Feel free to rename it later to something cooler that makes you sound like a genius with branding skills!*