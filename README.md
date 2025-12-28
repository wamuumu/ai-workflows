<div align="center">

# AI-Workflows

### *An evaluation framework to test different workflows generation designs.*

[![python-logo]](https://www.python.org/)
[![license-logo]](LICENSE)

</div>

---

## 📖 Introduction

AI-Workflows is a comprehensive evaluation framework designed to test and compare different approaches for generating AI-powered workflows. The framework enables researchers and developers to experiment with various workflow generation strategies, from simple one-shot generation to complex hierarchical decomposition, while maintaining a consistent evaluation methodology.

**Key Objectives:**
- Provide a modular architecture for implementing and testing workflow generation strategies
- Enable systematic evaluation of workflow quality through similarity and correctness metrics
- Support multiple LLM providers (Google Gemini, Cerebras) for flexible experimentation
- Offer extensible tool registries for diverse workflow capabilities

**Use Cases:**
- Research on AI agent orchestration and planning
- Evaluation of different prompt engineering approaches
- Benchmarking LLM performance on structured task decomposition
- Development of intelligent automation systems

---

## 📋 Table of Contents

* [Introduction](#-introduction)
* [Getting Started](#-getting-started)
    * [Prerequisites](#prerequisites)
    * [Installation](#installation)
* [Folder Structure](#-folder-structure)
* [Usage](#-usage)
    * [Command-Line Arguments](#command-line-arguments)
    * [Examples](#examples)
    * [Configuration](#configuration)
* [License](#-license)

---

## 🚀 Getting Started

### Prerequisites

To run this project, ensure that all the following dependencies are installed and available: 

| Tool | Version | Purpose |
|------|---------|---------|
| 🐍 [Python](https://www.python.org/) | v3.8+ | Programming language |

### Installation

Clone the repository and move into the project directory:

```bash
git clone https://github.com/wamuumu/ai-workflows.git
cd ai-workflows
```

Set up a virtual environment and install the required packages:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 📁 Folder Structure

```
ai-workflows/
├── 📁 data/                   # JSON/HTML representation files
├── 📁 logs/                   # Logs files
├── 📁 src/                    # Source code files
│   ├── 📁 agents/                  # LLM agent implemetations
│   ├── 📁 features/                # Workflow enhancement features 
│   ├── 📁 models/                  # LLM response schemas
│   ├── 📁 orchestrators/           # Automation responsible
│   ├── 📁 prompts/                 # Prompt definitions (user and system)
|   ├── 📁 strategies/              # Workflow generation strategies
|   ├── 📁 tools/                   # Tool implementations
|   ├── 📁 utils/                   # Utility functions and helpers
|   ├── evaluate.py                 # Evaluation script
│   └── main.py                     # Main entry point
└── 📁 tests/                  # Evauluation files
```

---

## 💡 Usage

The main entry point for the framework is [main.py](src/main.py). This script generates and optionally executes AI workflows based on user prompts.

To run with default settings, use the following command:

```bash
python src/main.py
```

### Command-Line Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--runs` | int | 1 | Number of sequential runs to execute |
| `--it` | bool | False | Pick a random iteration for user prompt |

### Examples

Execute multiple sequential runs:

```bash
python src/main.py --runs 5
```

Use random prompt iterations:

```bash
python src/main.py --it
```

Combine multiple runs with random iterations:

```bash
python src/main.py --runs 10 --it True
```

### Configuration

Modify the configuration settings in [main.py](src/main.py) to customize the workflow generation and execution process:

| Strategy | Parameters | Description |
|----------|------|----------------------|
| `MonolithicStrategy` | N/A | One-shot workflow generation using a single LLM agent |
| `IterativeStrategy` | max_rounds | Step-by-step workflow generation with iterative (max_rounds) generation-validation refinement |
| `HierarchicalStrategy` | N/A | Workflow generation using task decomposition and hierarchical planning |

| Tools | Description |
|-------|-------------|
| `ToolRegistry` | Register and configure available tools for workflow execution |

---

## 📄 License

[![license-logo]](LICENSE)

<div align="right">

[![](https://img.shields.io/badge/Return-5D4ED3?style=flat&logo=ReadMe&logoColor=white)](#top)

</div>

<!-- LOGOs -->
[python-logo]: https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python
[license-logo]: https://img.shields.io/badge/License-MIT-green?style=for-the-badge