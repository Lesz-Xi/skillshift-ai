# Project: SkillShift AI

## Project Overview

This project, **SkillShift AI**, is an intelligent coaching system for the popular mobile game **Mobile Legends: Bang Bang (MLBB)**. It analyzes a player's match statistics and provides actionable, role-specific feedback to help them improve their gameplay.

The system is built with a sophisticated evaluation engine that uses dynamic thresholds based on match duration and hero roles. It simulates the advice a professional coach would give, focusing on key performance indicators (KPIs) like KDA (Kills/Deaths/Assists), GPM (Gold Per Minute), damage ratios, and teamfight participation.

A key feature of this project is its ability to analyze screenshots of the game's post-match screen. It uses **Optical Character Recognition (OCR)** and **object detection (YOLOv8)** to extract the statistical data from the image, making it easy for players to get feedback without manual data entry.

The backend is a **Python** application using the **FastAPI** framework. It includes a modular, rule-based system for evaluating player performance, with specific rules for different heroes and roles. The project also uses **Redis** for caching and task queuing.

## Building and Running

### 1. Installation

To set up the project, install the required dependencies using pip:

```bash
pip install -r skillshift-ai/requirements.txt
```

### 2. Configuration

The project requires Redis connection details. You can configure them by creating a `.env` file in the `skillshift-ai` directory, based on the `config.template` file.

```bash
# skillshift-ai/.env
REDIS_URL="redis://your_redis_url"
SKILLSHIFT_AI_URL="http://localhost:8000"
DEFAULT_IGN="YourInGameName"
```

### 3. Running the Application

The main application logic is in `skillshift-ai/main.py`. You can run it directly to test the screenshot analysis feature:

```bash
python skillshift-ai/main.py
```

To run the web server, use `uvicorn`:

```bash
uvicorn skillshift-ai.main:app --host 0.0.0.0 --port 8000
```

### 4. Running Tests

The project has a suite of unit tests. To run them, use the following command:

```bash
python -m unittest discover skillshift-ai/tests
```

## Development Conventions

*   **Modular Architecture:** The coaching logic is organized into a `rules` directory, with subdirectories for each hero role. This makes it easy to add new heroes or modify existing rules.
*   **Configuration-Driven:** Performance thresholds and other parameters are intended to be stored in YAML files, separating configuration from code.
*   **Data Validation:** The project uses **Pydantic** to define data schemas and validate incoming data, ensuring data integrity.
*   **Type Hinting:** The codebase uses Python's type hints for better readability and static analysis.
*   **Testing:** The project has a `tests` directory with unit tests for the core logic and hero-specific rules.
