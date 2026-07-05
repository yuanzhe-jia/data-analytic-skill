# Data Analytic Skill

A thinking framework and planning tool designed to guide agents through systematic data analysis.
This skill decomposes complex questions into structured workflows, provides targeted guidance, and generates executable tool call sequences (SQL, Python, visualizations) with parameter schemas.

## Core Concept

This skill serves as an analysis navigator for agents.
It doesn't understand natural language or compute data—it provides a structured framework that agents can use to organize their analysis approach.

| Dimension | Purpose | Key Focus |
|-----------|---------|-----------|
| `BENCHMARK` | Establish baselines and statistical thresholds | Is the change meaningful? |
| `CLASSIFICATION` | Segment data to identify anomalies | Where is the change occurring? |
| `ATTRIBUTION` | Quantify contributions of causal factors | Why did it happen? |
| `PREDICTION` | Forecast future trends and outcomes | What will happen next? |

## Quick Start

### Installation

```bash
cd skill/src
pip install -e .
```

### Basic Usage

```python
from skill import DataAnalyticSkill, AnalysisType

# Just pass the question - skill auto-recommends analysis types
question = "Why did sales drop by 12%?"
skill = DataAnalyticSkill()

# Get analysis type recommendation with reasoning
rec = skill.recommend_analysis_types(question)
print(f"Recommended: {rec.recommended_types}")
print(f"Reasoning: {rec.reasoning}")

# Get structured workflow guidance (auto-recommends types from question)
workflow = skill.get_workflow(question=question)

for step in workflow:
    print(f"Step {step.order}: {step.type.upper()}")
    print(f"  Logic: {step.logic}")
    print(f"  Guidance: {step.guidance}")
```

### Using a Custom Classifier

Agents can inject their own LLM-based question classifier:

```python
from skill import DataAnalyticSkill, QuestionClassifier, QuestionContext

class LLMClassifier(QuestionClassifier):
    def classify(self, question: str):
        # Call your LLM here to classify the question
        return [QuestionContext.CHANGE_WITH_MAGNITUDE]

skill = DataAnalyticSkill(classifier=LLMClassifier())
contexts = skill.classify_question("Why did sales drop?")
```

### Generating Executable Tool Calls

Get structured tool call sequences with parameter schemas and placeholder tracking:

```python
from skill import DataAnalyticSkill, AnalysisType, ToolCallType, ToolCall

skill = DataAnalyticSkill()

# Generate tool calls (auto-recommends types from question)
tool_calls = skill.generate_tool_calls(
    question="Why did revenue drop 15%?",
    tool_types=[ToolCallType.SQL_QUERY, ToolCallType.PYTHON_SNIPPET]
)

for tc in tool_calls:
    print(f"[{tc.tool_type}] {tc.name}: {tc.description}")
    print(f"  Placeholders: {tc.placeholders}")
    print(f"  Missing required: {tc.missing_params()}")
    print()

# Fill in parameters to get executable SQL
first_sql = tool_calls[0]
filled = first_sql.fill_params({
    "metric": "revenue",
    "table": "sales",
    "date_col": "order_date",
    "start_date": "2024-01-01",
    "end_date": "2024-06-30"
})
print(filled.content)  # Ready-to-execute SQL
```

### Testing

```bash
cd skill/src
python test.py
```

## API Documentation

### `recommend_analysis_types(question)`

Recommend analysis types based on the question content.

**Parameters:**
- `question`: `str` - The user's natural language question.

**Returns:** `AnalysisRecommendation`
```python
AnalysisRecommendation(
    question="Why did sales drop?",
    contexts=["change_with_magnitude"],
    recommended_types=["benchmark", "classification", "attribution"],
    reasoning="Questions mentioning a change magnitude require..."
)
```

### `get_workflow(analysis_types, question)`

Returns a structured workflow with targeted guidance.
If `analysis_types` is None and `question` is provided, auto-recommends types.

**Parameters:**
- `analysis_types`: `List[AnalysisType]` - Optional, types determined by agent or auto-recommended
- `question`: `str` - Optional, user question for context awareness

**Returns:** `List[WorkflowStep]`
```python
WorkflowStep(
    order=1,
    type="benchmark",
    logic="Analysis reasoning for this step",
    guidance="Actionable guidance for the agent"
)
```

### `generate_tool_calls(analysis_types, question, tool_types)`

Generates structured tool call sequences with parameter schemas and placeholder tracking.

**Parameters:**
- `analysis_types`: `List[AnalysisType]` - Optional, auto-recommended if None and question provided
- `question`: `str` - Optional user question for context-aware selection
- `tool_types`: `List[ToolCallType]` - Optional filter (SQL_QUERY, PYTHON_SNIPPET, VISUALIZATION, DATA_EXPORT)

**Returns:** `List[ToolCall]`
```python
ToolCall(
    order=1,
    analysis_type="benchmark",
    tool_type="sql_query",
    name="calculate_historical_baseline",
    description="Compute historical average, std, and percentiles",
    content="SELECT AVG({metric}) FROM {table} WHERE {date_col} BETWEEN '{start_date}' AND '{end_date}'",
    parameters=[ToolParam(name="metric", type="string", description="Metric column", required=True)],
    placeholders=["metric", "table", "date_col", "start_date", "end_date"]
)
```

**ToolCall methods:**
- `fill_params(params: Dict[str, str]) -> ToolCall`: Return new ToolCall with placeholders replaced
- `missing_params() -> List[str]`: List of required parameters still missing
- `to_dict() -> Dict`: Convert to dictionary

### `classify_question(question)`

Classify a question using the configured classifier. Returns list of context tag strings.

### `set_classifier(classifier)`

Replace the current question classifier at runtime.

### `explain_framework()`

Returns descriptions of all four analysis dimensions.

### `get_all_analysis_types()`

Returns list of available analysis types with their purposes.

### `get_analysis_type_description(analysis_type)`

Returns detailed description for a specific analysis type.

### `get_available_contexts()`

Returns all available question context types.

## Data Contracts (Dataclasses)

| Class | Purpose |
|-------|---------|
| `WorkflowStep` | A step in the analysis workflow |
| `ToolCall` | A structured, executable tool call |
| `ToolParam` | Parameter schema for a tool call |
| `AnalysisRecommendation` | Recommended analysis types with reasoning |

All dataclasses have a `.to_dict()` method for serialization.

## Pluggable Classifier Interface

The skill uses the `QuestionClassifier` abstract base class. Implement your own classifier by subclassing it:

```python
from skill import QuestionClassifier, QuestionContext

class MyLLMClassifier(QuestionClassifier):
    def classify(self, question: str) -> list[QuestionContext]:
        # Your LLM-based classification logic here
        return [QuestionContext.CHANGE_WITH_MAGNITUDE]
```

Built-in classifiers:
- `KeywordClassifier` - Rule-based keyword matching (default)

## Project Structure

```
data-analytic-skill/
├── .gitignore
├── LICENSE.txt
├── README.md
├── docs/
│   └── data-science.md
└── skill/
    ├── SKILL.md
    └── src/
        ├── setup.py
        ├── skill.py
        └── test.py
```
