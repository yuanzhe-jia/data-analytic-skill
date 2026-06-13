# Data Analytic Skill

## Skill Metadata

| Attribute | Value |
|-----------|-------|
| **Skill Name** | DataAnalyticSkill |
| **Version** | 1.0.0 |
| **Description** | A planning framework for decomposing data analysis questions into structured analysis workflows |
| **Category** | Data Analysis |
| **License** | MIT |

## Purpose

A thinking framework that guides agents through systematic data analysis planning. It provides structured guidance without performing NLU or actual data analysis.

**Core Principles:**
- Agent's LLM handles question classification and intent recognition
- This skill provides analysis workflow guidance and decomposition templates
- Agent provides `AnalysisType(s)` determined by its NLU

## Analysis Types

| Type | Purpose | Focus |
|------|---------|-------|
| `BENCHMARK` | Establish baselines and thresholds | Is the change significant? |
| `CLASSIFICATION` | Identify anomalous segments | Where is the change occurring? |
| `ATTRIBUTION` | Quantify factor contributions | Why did the change happen? |
| `PREDICTION` | Forecast future outcomes | What will happen next? |

## Input/Output

**Input:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `question` | `str` | Yes | User's natural language question |
| `analysis_types` | `List[AnalysisType]` | Yes | Types determined by agent's NLU |

**Output:**
```json
{
  "order": int,
  "type": "benchmark|classification|attribution|prediction",
  "logic": "Analysis reasoning for this step",
  "guidance": "Actionable guidance for the agent"
}
```

## API Reference

### `get_workflow(analysis_types, question)`
Returns structured workflow with targeted guidance based on question context.

**Parameters:**
- `analysis_types`: List of AnalysisType enum values
- `question`: Original user question for context-specific guidance

**Returns:** List of workflow steps with `order`, `type`, `logic`, `guidance`

### `explain_framework()`
Returns descriptions of the four core analysis dimensions.

### `get_all_analysis_types()`
Returns list of all available analysis types with descriptions.

### `get_analysis_type_description(analysis_type)`
Returns detailed description for a specific analysis type.

## Usage Example

```python
from skill import DataAnalyticSkill, AnalysisType

# Agent determines analysis types via its NLU
question = "Why did sales drop by 12%?"
analysis_types = [AnalysisType.BENCHMARK, AnalysisType.CLASSIFICATION, AnalysisType.ATTRIBUTION]

# Get structured workflow guidance
skill = DataAnalyticSkill()
workflow = skill.get_workflow(analysis_types, question)

for step in workflow:
    print(f"Step {step['order']}: {step['type']}")
    print(f"  Logic: {step['logic']}")
    print(f"  Guidance: {step['guidance']}")
```

## Integration Flow

```
User Question → Agent NLU → Determine AnalysisTypes → DataAnalyticSkill → Get Workflow Guidance → Agent Executes Analysis
```

## Key Features

- **Context-aware Guidance**: Tailored logic and guidance based on question type
- **Standardized Output**: Consistent structure across all analysis types
- **Framework Agnostic**: Works with any agent architecture
- **Lightweight**: No external dependencies
