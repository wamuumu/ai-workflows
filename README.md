<div align="center">

# AI-Workflows

### *An evaluation framework to test different workflow generation designs.*

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
* [Architecture](#-architecture)
    * [Core Components](#core-components)
    * [Workflow Generation Strategies](#workflow-generation-strategies)
    * [Enhancement Features](#enhancement-features)
    * [Available Tools](#available-tools)
* [Evaluation](#-evaluation)
    * [Similarity Scores](#similarity-scores)
    * [Correctness Scores](#correctness-scores)
* [License](#-license)

---

## 🚀 Getting Started

### Prerequisites

To run this project, ensure that all the following dependencies are installed and available: 

| Tool | Version | Purpose |
|------|---------|---------|
| [Python](https://www.python.org/) | v3.12+ | Programming language |

**Required API Keys:**
- **Google AI API Key** (for Gemini models) or **Cerebras API Key** (for Cerebras models)
- You can obtain these keys from:
  - Google AI: https://ai.google.dev/
  - Cerebras: https://cerebras.ai/

### Installation

1. Clone the repository and move into the project directory:

```bash
git clone https://github.com/wamuumu/ai-workflows.git
cd ai-workflows
```

2. Set up a virtual environment and install the required packages:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

3. Configure your API keys:

Create a `.env` file in the root directory with your API credentials:

```bash
GOOGLE_API_KEY=your_google_api_key_here
CEREBRAS_API_KEY=your_cerebras_api_key_here
```

Alternatively, the system will prompt you for API keys at runtime if they are not set.

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
│   ├── 📁 orchestrators/           # Workflow orchestration
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

The main entry point for the framework is `src/main.py`. This script generates and optionally executes AI workflows based on user prompts.

### Command-Line Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--runs` | int | 1 | Number of sequential runs to execute |
| `--it` | bool | False | Pick a random iteration for user prompt |

### Examples

**Basic workflow generation:**
```bash
python src/main.py
```

**Execute multiple sequential runs:**
```bash
python src/main.py --runs 5
```

**Use random prompt iterations:**
```bash
python src/main.py --it True
```

**Combine multiple runs with random iterations:**
```bash
python src/main.py --runs 10 --it True
```

### Configuration

Modify the configuration settings in `src/main.py` to customize the workflow generation and execution process:

**1. Select a Generation Strategy:**

| Strategy | Parameters | Description |
|----------|------------|-------------|
| `MonolithicStrategy` | None | One-shot workflow generation using a single LLM agent. Fast but may miss complex dependencies. |
| `IterativeStrategy` | `max_rounds` (default: 5) | Step-by-step workflow generation with iterative generation-validation refinement. More reliable but slower. |
| `HierarchicalStrategy` | None | Workflow generation using task decomposition and hierarchical planning. Best for complex tasks with dependencies. |

**2. Choose available tools from the registry:**

To use all registered tools:

```python
available_tools = ToolRegistry.get_all()
```

To select specific tools by name:

```python
available_tools = [ToolRegistry.get("tool_name_1"), ToolRegistry.get("tool_name_2"), ...]
```

Then in the orchestrator configuration:

```python
orchestrator = ConfigurableOrchestrator(
    available_tools=available_tools,
    ...
)
```

**2. Configure Enhancement Features:**

```python
orchestrator = ConfigurableOrchestrator(
    features=[
        ChatClarificationFeature(),  # Interactive user clarification
        RefinementFeature()          # Post-generation refinement
    ],
    ...
)
```

**3. Configure LLM Agents:**

```python
orchestrator = ConfigurableOrchestrator(
    agents={
        "generator": GeminiAgent(GeminiModel.GEMINI_2_5_FLASH),
        "discriminator": CerebrasAgent(CerebrasModel.LLAMA_3_3),
        "planner": CerebrasAgent(CerebrasModel.LLAMA_3_3),
        # ... other agents
    },
    ...
)
```

**4. Select User Prompt:**

Choose from predefined prompts in `src/prompts/user/`:
- `weather_activity_plan.json` - Weather-based activity planning
- `paris_trip_planner.json` - Multi-step travel planning
- `tesla_stock_analysis.json` - Conditional financial analysis
- `document_sentiment_report.json` - Batch document processing
- And more...

> [!NOTE]  
> Each prompt file contains multiple iterations (1, 2, 3, ...) for variability. During execution, you can select a specific iteration or pick randomly if `--it` is set to True.

```python
# Select first iteration of weather activity planning prompt
user_prompt = PromptUtils.get_user_prompts("weather_activity_plan").get("1")
```

**5. Choose Workflow Model:**

```python
# For linear workflows (sequential steps only)
workflow = orchestrator.generate(user_prompt, response_model=LinearWorkflow)

# For structured workflows (with branching/conditionals)
workflow = orchestrator.generate(user_prompt, response_model=StructuredWorkflow)
```

---

## 🏗 Architecture

### Core Components

**1. Orchestrator (`orchestrators/base.py`)**
- Central controller for workflow generation and execution
- Manages agent coordination and feature application
- Handles workflow serialization and visualization

**2. Agents (`agents/`)**
- Abstract base class defining LLM interaction interface
- Implementations for Google Gemini and Cerebras models
- Support for both unstructured and structured (JSON schema) outputs
- Chat session management for multi-turn interactions

**3. Tool Registry (`tools/registry.py`)**
- Dynamic tool discovery and registration
- Automatic input/output schema extraction from type hints
- Prompt-friendly tool documentation generation
- Category-based tool organization

### Workflow Generation Strategies

**MonolithicStrategy** (`strategies/monolithic.py`)
- **Approach:** Single LLM call generates entire workflow

**IterativeStrategy** (`strategies/iterative.py`)
- **Approach:** Generator-discriminator loop with configurable rounds
- **Process:** Generate → Critique → Understand → Repeat
- **Configuration:** `max_rounds` parameter (default: 5)

**HierarchicalStrategy** (`strategies/hierarchical.py`)
- **Approach:** Recursive task decomposition into sub-tasks
- **Process:** Plan → Generate fragments → Merge → Resolve

### Enhancement Features

**ChatClarificationFeature** (`features/clarification.py`)
- **Phase:** Pre-generation
- **Purpose:** Interactive user interview to gather missing information
- **Process:** Multi-turn dialogue asking one question at a time
- **Output:** Enriched context for workflow generation

**RefinementFeature** (`features/refinement.py`)
- **Phase:** Post-generation
- **Purpose:** Polish and validate generated workflow
- **Actions:** Fix references, add missing steps, resolve ambiguities
- **Output:** Refined workflow ready for execution

### Available Tools

The framework includes 20+ pre-built tools across 10 categories:

| Category | Tools | Description |
|----------|-------|-------------|
| **Communication** | `send_email` | Email sending capabilities |
| **Documents** | `list_files`, `read_file`, `write_file` | File system operations |
| **Finance** | `convert_currency`, `get_stock_price` | Financial data retrieval |
| **Math** | `calculator`, `compute_statistics` | Mathematical computations |
| **ML** | `embed_text`, `cluster_data`, `train_regression`, `make_predictions` | Machine learning utilities |
| **News** | `get_news`, `search_news` | News article search |
| **Text** | `clean_text`, `analyze_sentiment`, `translate_text` | Text processing |
| **Travel** | `get_city_attractions`, `get_indoor_activities`, `get_outdoor_activities` | Location services |
| **Weather** | `current_weather` | Weather forecasting |
| **Web** | `search_web`, `scrape_web` | Web information retrieval |

**Adding Custom Tools:**

```python
from tools.decorator import tool
from typing import TypedDict

class MyToolOutput(TypedDict):
    result: str
    status: str

@tool(
    name="my_custom_tool",
    description="Description of what the tool does",
    category="custom"
)
def my_custom_tool(param1: str, param2: int) -> MyToolOutput:
    # Implementation
    return MyToolOutput(result="...", status="success")
```

---

## 📊 Evaluation

The framework provides two main evaluation approaches accessible via `src/evaluate.py`:

### Similarity Scores

**Purpose:** Measure consistency and reproducibility across multiple workflow generations

**Usage:**
```python
from models import StructuredWorkflow
from utils.workflow import WorkflowUtils
from utils.metric import MetricUtils

# Load workflows to compare
workflow1 = WorkflowUtils.load_json("/path/to/workflow1.json", StructuredWorkflow)
workflow2 = WorkflowUtils.load_json("/path/to/workflow2.json", StructuredWorkflow)

# Compute pairwise similarity matrix
MetricUtils.similarity_scores([workflow1, workflow2, workflow3])
```

**Metrics Computed:**
- **Step Similarity** (70% weight): Compares actions, tools, parameters, and finality
- **Transition Similarity** (30% weight): Compares control flow edges
- **Overall Score**: Weighted combination normalized to [0, 1]

**Output Example:**
```
Workflow Similarity Matrix

      W1    W2    W3
W1    1.00  0.85  0.72
W2    0.85  1.00  0.68
W3    0.72  0.68  1.00
```

### Correctness Scores

**Purpose:** Evaluate workflow behavior against expected ground truth constraints

**Usage:**
```python
from utils.metric import MetricUtils
from utils.workflow import WorkflowUtils

workflow = WorkflowUtils.load_json("/path/to/workflow.json", StructuredWorkflow)
MetricUtils.correctness_scores(
    reference="/path/to/constraints.json",
    workflow=workflow
)
```

*Example of constraints file:*
```json
{
  "expected_tool_calls": {
    "current_weather": {"min": 1, "max": 1},
    "get_indoor_activities": {"min": 1, "max": 1},
    "get_outdoor_activities": {"min": 1, "max": 1},
    "write_file": {"min": 1, "max": 2},
    "send_email": {"min": 1, "max": 2}
  },
  "expected_llm_calls": {"min": 1, "max": 3},
  "expected_branch_transitions": {
    "weather_check": {
        "keywords": ["rain", "rainy", "forecast", "forecasts", "determine", "respond", "decide"],
        "transitions": 2
    }
  },
  "expected_step_count_range": [8, 12]
}
```

**Metrics Computed:**
- Tool call frequency (min/max constraints)
- LLM call frequency (min/max constraints)
- Total step count (range validation)
- Branch transition correctness (keyword + count matching)

**Output Example:**

*If all constraints are satisfied, you will get somthing like this:*

```
Correctness Evaluation Results:
  Overall correctness score: 1.000
  Tool call scores: ['1.000', '1.000', '1.000', '1.000', '1.000']
  LLM call score: 1.000
  Total step score: 1.000
  Branch transition score: 1.000
```

---

## 📄 License
[![license-logo]](LICENSE)

<div align="right">

[![](https://img.shields.io/badge/Return-5D4ED3?style=flat&logo=ReadMe&logoColor=white)](#top)

</div>

<!-- LOGOs -->
[python-logo]: https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python
[license-logo]: https://img.shields.io/badge/License-MIT-green?style=for-the-badge