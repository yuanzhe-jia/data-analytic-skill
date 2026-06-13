# Data Analytic Skill

A thinking framework and planning tool designed to guide intelligent agents through systematic data analysis. This skill decomposes complex questions into structured workflows, providing targeted guidance without performing NLU or actual data analysis.

## Core Concept

This skill serves as an analysis navigator for agents. It doesn't understand natural language or compute data—it provides a structured framework that agents can use to organize their analysis approach.

### Responsibility Division

| Responsibility | Provider |
|----------------|----------|
| Intent Recognition | Agent's LLM |
| Analysis Planning | This Skill |
| Data Execution | Agent/Tools |

## Analysis Framework

Four core analysis dimensions form the foundation of this framework:

| Dimension | Purpose | Key Focus |
|-----------|---------|-----------|
| **BENCHMARK** | Establish baselines and statistical thresholds | Is the change meaningful? |
| **CLASSIFICATION** | Segment data to identify anomalies | Where is the change occurring? |
| **ATTRIBUTION** | Quantify contributions of causal factors | Why did it happen? |
| **PREDICTION** | Forecast future trends and outcomes | What will happen next? |

## Quick Start

### Installation

```bash
cd skill/src
pip install -e .
```

### Basic Usage

```python
from skill import DataAnalyticSkill, AnalysisType

# Agent determines analysis types using its NLU
question = "Why did sales drop by 12%?"
analysis_types = [AnalysisType.BENCHMARK, AnalysisType.CLASSIFICATION, AnalysisType.ATTRIBUTION]

# Get structured workflow guidance
skill = DataAnalyticSkill()
workflow = skill.get_workflow(analysis_types, question)

# Workflow contains context-specific guidance for each step
for step in workflow:
    print(f"Step {step['order']}: {step['type'].upper()}")
    print(f"  Logic: {step['logic']}")
    print(f"  Guidance: {step['guidance']}")
```

### Testing

```bash
cd skill/src
python test.py
```

## API Documentation

### `get_workflow(analysis_types, question)`

Returns a structured workflow with targeted guidance.

**Parameters:**
- `analysis_types`: `List[AnalysisType]` - Types determined by agent's NLU
- `question`: `str` - Original user question for context awareness

**Returns:**
```json
[
  {
    "order": 1,
    "type": "benchmark",
    "logic": "Analysis reasoning for this step",
    "guidance": "Actionable guidance for the agent"
  }
]
```

### `explain_framework()`

Returns descriptions of all four analysis dimensions.

### `get_all_analysis_types()`

Returns list of available analysis types with their purposes.

### `get_analysis_type_description(analysis_type)`

Returns detailed description for a specific analysis type.

## Project Structure

```
data-analytic-skill/
├── .gitignore
├── LICENSE.txt
├── README.md
└── skill/
    ├── SKILL.md
    └── src/
        ├── setup.py
        ├── skill.py
        └── test.py
```
