# Data Analytic Skill

## Skill Metadata

| Attribute | Value |
|-----------|-------|
| **Skill Name** | DataAnalyticSkill |
| **Version** | 1.0.0 |
| **Description** | A planning framework for decomposing data analysis questions into structured workflows and executable tool call sequences with parameter schemas |
| **Category** | Data Analysis |
| **License** | MIT |

## Purpose

A thinking framework that guides agents through systematic data analysis planning. Provides structured guidance, pluggable question classification, automatic analysis type recommendation, and executable tool call generation with parameter schemas.

**Core Principles:**
- Agent's LLM can handle question classification, or inject a custom `QuestionClassifier`
- Skill auto-recommends analysis types from question context
- Tool calls include parameter schemas and placeholder tracking for direct execution
- Agent provides `AnalysisType(s)` optionally, or lets skill recommend them

## Analysis Types

| Type | Purpose | Focus |
|------|---------|-------|
| `BENCHMARK` | Establish baselines and thresholds | Is the change significant? |
| `CLASSIFICATION` | Identify anomalous segments | Where is the change occurring? |
| `ATTRIBUTION` | Quantify factor contributions | Why did the change happen? |
| `PREDICTION` | Forecast future outcomes | What will happen next? |

## Question Contexts

The skill supports multiple question context types for targeted guidance:

| Context | Description |
|---------|-------------|
| `is_normal_question` | Questions about whether a value is normal/expected |
| `change_with_magnitude` | Questions mentioning specific changes (drop, increase, etc.) |
| `comparison_question` | Questions comparing groups or periods |
| `prediction_question` | Questions about future outcomes or forecasts |
| `funnel_question` | Questions about conversion funnels |
| `retention_question` | Questions about user retention |
| `general_question` | Default fallback context |

## Data Contracts (Dataclasses)

All return types are strongly-typed dataclasses with `.to_dict()` for serialization.

| Class | Fields |
|-------|--------|
| `WorkflowStep` | `order`, `type`, `logic`, `guidance` |
| `ToolCall` | `order`, `analysis_type`, `tool_type`, `name`, `description`, `content`, `parameters`, `placeholders` |
| `ToolParam` | `name`, `type`, `description`, `required`, `default` |
| `AnalysisRecommendation` | `question`, `contexts`, `recommended_types`, `reasoning` |

### ToolCall Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `fill_params(params: Dict)` | `ToolCall` | Return new ToolCall with placeholders replaced |
| `missing_params()` | `List[str]` | List of required parameters still unfilled |
| `to_dict()` | `Dict` | Serialize to dictionary |

## API Reference

### `recommend_analysis_types(question)`
Recommend analysis types based on question content.
- **Input:** question string
- **Returns:** `AnalysisRecommendation` with types and reasoning

### `get_workflow(analysis_types, question)`
Returns structured workflow with targeted guidance.
- **Input:** optional analysis_types, optional question
- **If analysis_types is None + question provided:** auto-recommends types
- **Returns:** `List[WorkflowStep]`

### `generate_tool_calls(analysis_types, question, tool_types)`
Generates structured tool call sequences with parameter schemas and placeholders.
- **Input:** optional analysis_types, optional question, optional tool_types filter
- **If analysis_types is None + question provided:** auto-recommends types
- **Returns:** `List[ToolCall]`

### `classify_question(question)`
Classify a question using the configured classifier. Returns list of context tag strings.

### `set_classifier(classifier)`
Replace the question classifier at runtime.

### `explain_framework()`
Returns descriptions of the four core analysis dimensions.

### `get_all_analysis_types()`
Returns list of all available analysis types with descriptions.

### `get_analysis_type_description(analysis_type)`
Returns detailed description for a specific analysis type.

### `get_available_contexts()`
Returns all available question context types.

## Pluggable Classifier

Implement your own classifier by subclassing `QuestionClassifier`:

```python
from skill import QuestionClassifier, QuestionContext

class LLMClassifier(QuestionClassifier):
    def classify(self, question: str):
        # Call LLM API for intelligent classification
        return [QuestionContext.CHANGE_WITH_MAGNITUDE]

# Inject into skill
skill = DataAnalyticSkill(classifier=LLMClassifier())
```

## Usage Example

```python
from skill import DataAnalyticSkill, ToolCallType

# Step 1: Get analysis type recommendation
question = "Why did sales drop by 12%?"
skill = DataAnalyticSkill()
rec = skill.recommend_analysis_types(question)
print(f"Recommended: {rec.recommended_types}")

# Step 2: Get workflow guidance (auto-recommends types)
workflow = skill.get_workflow(question=question)

# Step 3: Generate executable tool calls
tool_calls = skill.generate_tool_calls(
    question=question,
    tool_types=[ToolCallType.SQL_QUERY, ToolCallType.PYTHON_SNIPPET]
)

# Step 4: Fill parameters and execute
first_call = tool_calls[0]
print(f"Missing params: {first_call.missing_params()}")
filled = first_call.fill_params({
    "metric": "revenue",
    "table": "sales",
    "date_col": "order_date",
    "start_date": "2024-01-01",
    "end_date": "2024-06-30"
})
print(filled.content)  # Ready-to-execute SQL
```

## Integration Flow

```
User Question → [QuestionClassifier] → Context Tags
                          ↓
            recommend_analysis_types() → Analysis Types
                          ↓
                  get_workflow() → Workflow Steps
                          ↓
              generate_tool_calls() → ToolCall[]
                          ↓
            fill_params() → Executable Tool Calls
                          ↓
                  Agent Executes Analysis
```

## Key Features

- **Strongly-typed contracts**: All outputs are dataclasses with `.to_dict()` for serialization
- **Auto-recommendation**: Skill recommends analysis types from question context
- **Pluggable classifier**: Inject LLM-based or custom classifiers for intelligent question routing
- **Context-aware guidance**: Tailored logic and guidance based on question type (7+ context categories)
- **Executable tool calls**: SQL, Python, and visualization templates with parameter schemas
- **Placeholder tracking**: Know exactly which parameters are required and which are missing
- **Framework agnostic**: Works with any agent architecture
- **Lightweight**: No external dependencies required
