<div align="center">

# AI-Workflows

### *An evaluation framework for AI-powered workflow generation.*

[![python-logo]](https://www.python.org/)
[![license-logo]](LICENSE)

</div>

---

## 📖 Overview

AI-Workflows is a framework for generating and evaluating AI-powered workflows using different generation strategies. It supports multiple workflow generation approaches, various LLM providers, and comprehensive evaluation metrics for comparing workflow quality.

**Key Features:**
- Multiple workflow generation strategies (monolithic, incremental, bottom-up)
- Support for Google Gemini and Cerebras LLM models
- Extensible tool registry with 20+ pre-built tools
- Workflow enhancement features (chat clarification, refinement)
- Similarity and correctness evaluation metrics

---

## 📋 Table of Contents

* [Overview](#-overview)
* [Getting Started](#-getting-started)
    * [Prerequisites](#prerequisites)
    * [Installation](#installation)
* [Project Structure](#-project-structure)
* [Quick Start](#-quick-start)
    * [CLI Options](#cli-options)
* [Architecture](#-architecture)
    * [Generation Strategies](#generation-strategies)
    * [Supported Models](#supported-models)
    * [Tool Categories](#tool-categories)
    * [Workflow Models](#workflow-models)
* [Evaluation](#-evaluation)
* [License](#-license)

---

## 🚀 Getting Started

### Prerequisites

- **Python:** v3.12+
- **API Keys:**
  - Google AI API Key (for Gemini): https://ai.google.dev/
  - Cerebras API Key (for Cerebras models): https://cerebras.ai/

### Installation

1. Clone the repository:
```bash
git clone https://github.com/wamuumu/ai-workflows.git
cd ai-workflows
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up your API keys:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

---

## 📁 Project Structure

```
ai-workflows/
├── src/
│   ├── agents/              # LLM agent implementations (Gemini, Cerebras)
│   ├── features/            # Enhancement features (chat, refinement)
│   ├── models/              # Workflow and response schemas
│   ├── orchestrators/       # Workflow generation and execution
│   ├── prompts/             # System and user prompts
│   ├── strategies/          # Generation strategies
│   ├── tools/               # Tool implementations
│   ├── utils/               # Utilities (logging, metrics, workflow)
│   ├── main.py              # Main entry point
│   └── evaluate.py          # Evaluation script
├── tests/                   # Evaluation constraints
├── data/                    # Generated workflows, visualizations and runtime data
├── logs/                    # Execution logs
└── metrics/                 # Evaluation results
```

---

## 🎯 Quick Start

All commands should be run from the `src/` directory:

```bash
cd src
```

### Generate a Workflow

```bash
python main.py --generate --prompt weather_activity_plan
```

### Execute a Workflow

```bash
python main.py --execute --workflow-path ../data/workflows/workflow_*.json
```

### Generate and Execute

```bash
python main.py --generate --execute --prompt weather_activity_plan
```

### Evaluate Workflows

```bash
python evaluate.py --all --reference ../tests/constraints/weather_activity_plan.json
```

### CLI Options

#### main.py

| Flag | Description |
|------|-------------|
| `--generate` | Generate a workflow from the given prompt |
| `--execute` | Execute the generated or loaded workflow |
| `--workflow-path` | Path to a saved workflow JSON to load when not generating |
| `--prompt` | Prompt name (default: `weather_activity_plan`) |
| `--strategy` | Generation strategy: `monolithic`, `incremental`, `bottomup` (default: `monolithic`) |
| `--workflow-model` | Workflow format: `linear`, `structured` (default: `structured`) |
| `--runs` | Number of sequential runs to execute (default: `1`) |
| `--it` | Specific iteration index for prompt/workflow (default: `1`) |
| `--random-it` | Pick a random iteration for prompt/workflow |
| `--chat` | Enable chat clarification feature |
| `--refinement` | Enable refinement feature |
| `--validation-refinement` | Enable validation refinement |
| `--select-tools` | Space-separated tool names to enable (default: all tools) |
| `--atomic-tools-only` | Enable only atomic tools (default: `false`) |
| `--macro-tools-only` | Enable only macro tools (default: `false`) |
| `--no-tools` | Disable all tools |
| `--generator` | Generator agent (`provider:model`) |
| `--reviewer` | Reviewer agent (`provider:model`) |
| `--planner` | Planner agent (`provider:model`) |
| `--chatter` | Chatter agent (`provider:model`) |
| `--refiner` | Refiner agent (`provider:model`) |
| `--executor` | Executor agent (`provider:model`) |
| `--debug` | Enable debug logging |

#### evaluate.py

| Flag | Description |
|------|-------------|
| `--reference` | Path to reference constraints JSON |
| `--workflow-similarity` | Compare workflow structures |
| `--execution-similarity` | Compare execution traces |
| `--correctness-scores` | Validate against constraints |
| `--intent-resolution` | Evaluate intent resolution |
| `--reasoning-coherence` | Evaluate reasoning coherence |
| `--all` | Run all metrics |

---

## 🏗️ Architecture

### Generation Strategies

| Strategy | Description |
|----------|-------------|
| **Monolithic** | Single-shot complete workflow generation |
| **Incremental** | Step-by-step generation with sliding window context |
| **Bottom-Up** | Hierarchical: tool identification → ordering → control flow → assembly |

### Supported Models

| Provider | Models |
|----------|--------|
| Google Gemini | `gemini:2.5-flash`, `gemini:2.5-flash-lite` |
| Cerebras | `cerebras:gpt-oss`, `cerebras:llama-3.3`, `cerebras:qwen-3` |

### Tool Categories

Communication, Weather, Travel, Finance, Documents, Text, Math, Web, News, ML

### Workflow Models

- **LinearWorkflow:** Sequential list of steps
- **StructuredWorkflow:** Directed graph with dependencies and conditional execution

---

## 📊 Evaluation

The framework provides five evaluation metrics:

1. **Workflow Similarity:** Compares generated workflows structurally using embedding-based similarity
2. **Execution Similarity:** Measures similarity between workflow execution traces
3. **Correctness Scores:** Validates workflows against reference constraints (required steps, tool usage, dependencies)
4. **Intent Resolution:** Measures how well the agent interprets underlying goals vs literal prompts
5. **Reasoning Coherence:** Evaluates logical structure and consistency of reasoning chains

Results are saved at runtime to the `metrics/` directory with timestamps and detailed breakdowns.

To see all evaluation results, check the following spreadsheet:

[![google-sheet-logo]](https://docs.google.com/spreadsheets/d/1NI1UVD8nQ_wCcqrUvtZBqOlGUgmrKu4HsEMqdm3orDs/edit?usp=sharing)

---

## 📄 License
[![license-logo]](LICENSE)

<div align="right">

[![](https://img.shields.io/badge/Return-5D4ED3?style=flat&logo=ReadMe&logoColor=white)](#top)

</div>

<!-- LOGOs -->
[python-logo]: https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python
[license-logo]: https://img.shields.io/badge/License-MIT-green?style=for-the-badge
[google-sheet-logo]: https://img.shields.io/badge/AI_Workflows_Metrics-34A853?style=for-the-badge&logo=google-sheets&logoColor=white