from typing import List, Dict, Optional, Union, Any
from enum import Enum
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
import re


class AnalysisType(Enum):
    """Four core analysis dimensions for data analysis."""
    BENCHMARK = "benchmark"
    CLASSIFICATION = "classification"
    ATTRIBUTION = "attribution"
    PREDICTION = "prediction"


class QuestionContext(Enum):
    """Context tags for classifying data questions."""
    IS_NORMAL = "is_normal_question"
    CHANGE_WITH_MAGNITUDE = "change_with_magnitude"
    COMPARISON = "comparison_question"
    PREDICTION = "prediction_question"
    FUNNEL = "funnel_question"
    RETENTION = "retention_question"
    GENERAL = "general_question"


class ToolCallType(Enum):
    """Types of tool calls that can be generated."""
    SQL_QUERY = "sql_query"
    PYTHON_SNIPPET = "python_snippet"
    DATA_EXPORT = "data_export"
    VISUALIZATION = "visualization"


# ---------------------------------------------------------------------------
# Strongly-typed data contracts (dataclasses)
# ---------------------------------------------------------------------------

@dataclass
class ToolParam:
    """Schema definition for a tool parameter."""
    name: str
    type: str
    description: str
    required: bool = True
    default: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "required": self.required,
            "default": self.default,
        }


@dataclass
class WorkflowStep:
    """A single step in the analysis workflow."""
    order: int
    type: str
    logic: str
    guidance: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ToolCall:
    """A structured, executable tool call."""
    order: int
    analysis_type: str
    tool_type: str
    name: str
    description: str
    content: str
    parameters: List[ToolParam] = field(default_factory=list)
    placeholders: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order": self.order,
            "analysis_type": self.analysis_type,
            "tool_type": self.tool_type,
            "name": self.name,
            "description": self.description,
            "content": self.content,
            "parameters": [p.to_dict() for p in self.parameters],
            "placeholders": self.placeholders,
        }

    def fill_params(self, params: Dict[str, str]) -> "ToolCall":
        """Return a new ToolCall with placeholders replaced by actual values."""
        new_content = self.content
        filled_placeholders = []
        for key, value in params.items():
            pattern = r"{" + re.escape(key) + r"}"
            if re.search(pattern, new_content):
                new_content = re.sub(pattern, str(value), new_content)
                filled_placeholders.append(key)
        return ToolCall(
            order=self.order,
            analysis_type=self.analysis_type,
            tool_type=self.tool_type,
            name=self.name,
            description=self.description,
            content=new_content,
            parameters=self.parameters,
            placeholders=[p for p in self.placeholders if p not in filled_placeholders],
        )

    def missing_params(self) -> List[str]:
        """Return list of required parameters that are still placeholders."""
        required_names = {p.name for p in self.parameters if p.required}
        return sorted(required_names & set(self.placeholders))


@dataclass
class AnalysisRecommendation:
    """Recommendation of which analysis types to use for a question."""
    question: str
    contexts: List[str]
    recommended_types: List[str]
    reasoning: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Classifier interface
# ---------------------------------------------------------------------------

class QuestionClassifier(ABC):
    """
    Abstract base class for question classifiers.

    Agents can provide their own classifier implementation (e.g. LLM-based)
    by subclassing this and passing an instance to DataAnalyticSkill.
    """

    @abstractmethod
    def classify(self, question: str) -> List[QuestionContext]:
        """
        Classify a question into one or more context tags.

        Args:
            question: The user's natural language question.

        Returns:
            List of QuestionContext tags matching the question.
        """
        pass


class KeywordClassifier(QuestionClassifier):
    """
    Default rule-based classifier using keyword matching.

    This is a simple baseline classifier. For production use,
    agents should provide an LLM-based classifier instead.
    """

    KEYWORD_MAP = {
        QuestionContext.IS_NORMAL: [
            '正常', 'normal', 'regular', 'expected', 'standard',
            '是否正常', 'is this normal', '算不算正常'
        ],
        QuestionContext.CHANGE_WITH_MAGNITUDE: [
            '下降', '降低', '增长', '上升', 'drop', 'decrease',
            'increase', 'rise', '下滑', '上涨', '跌', '涨'
        ],
        QuestionContext.COMPARISON: [
            '对比', '比较', 'compare', 'vs', 'versus',
            '哪个好', '差异', '差别'
        ],
        QuestionContext.PREDICTION: [
            '未来', '预测', 'forecast', 'predict', 'will',
            '预期', '趋势', '展望', '会不会'
        ],
        QuestionContext.FUNNEL: [
            '漏斗', 'funnel', '转化', 'conversion',
            '加购', '下单', '付款', '流失'
        ],
        QuestionContext.RETENTION: [
            '留存', 'retention', '回访', '复购',
            '活跃率', '留存率'
        ],
    }

    def classify(self, question: str) -> List[QuestionContext]:
        contexts = []
        question_lower = question.lower()

        for context, keywords in self.KEYWORD_MAP.items():
            if any(kw.lower() in question_lower for kw in keywords):
                contexts.append(context)

        if not contexts:
            contexts.append(QuestionContext.GENERAL)

        return contexts


# ---------------------------------------------------------------------------
# Analysis dimension templates with parameter schemas
# ---------------------------------------------------------------------------

def _sql_params(extra: Optional[List[ToolParam]] = None) -> List[ToolParam]:
    base = [
        ToolParam(name="table", type="string", description="Name of the data table to query"),
        ToolParam(name="metric", type="string", description="Metric column name to analyze"),
        ToolParam(name="date_col", type="string", description="Date/timestamp column name", default="date"),
    ]
    if extra:
        base.extend(extra)
    return base


def _python_params(extra: Optional[List[ToolParam]] = None) -> List[ToolParam]:
    base = [
        ToolParam(name="df", type="DataFrame", description="Input pandas DataFrame"),
    ]
    if extra:
        base.extend(extra)
    return base


def _extract_placeholders(content: str) -> List[str]:
    """Extract {placeholder} names from a template string."""
    return sorted(set(re.findall(r"\{(\w+)\}", content)))


class AnalysisDimension:
    """Pre-defined analysis dimension templates with parameter schemas."""

    SQL_TEMPLATES = {
        AnalysisType.BENCHMARK: [
            {
                "name": "calculate_historical_baseline",
                "description": "Compute historical average, std, and percentiles for the target metric",
                "sql_hint": (
                    "SELECT AVG({metric}) AS avg_value, "
                    "STDDEV({metric}) AS std_value, "
                    "PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY {metric}) AS p95_value "
                    "FROM {table} "
                    "WHERE {date_col} BETWEEN '{start_date}' AND '{end_date}'"
                ),
                "parameters": _sql_params([
                    ToolParam(name="start_date", type="string", description="Start date of baseline period (YYYY-MM-DD)"),
                    ToolParam(name="end_date", type="string", description="End date of baseline period (YYYY-MM-DD)"),
                ]),
            },
            {
                "name": "period_over_period_comparison",
                "description": "Compare current period vs previous period (YoY/MoM/WoW)",
                "sql_hint": (
                    "WITH current AS ("
                    "SELECT SUM({metric}) AS cur FROM {table} WHERE {period_col} = '{current_period}'"
                    "), previous AS ("
                    "SELECT SUM({metric}) AS prev FROM {table} WHERE {period_col} = '{previous_period}'"
                    ") "
                    "SELECT cur, prev, (cur - prev) / prev AS change_pct FROM current, previous"
                ),
                "parameters": _sql_params([
                    ToolParam(name="period_col", type="string", description="Period column name", default="period"),
                    ToolParam(name="current_period", type="string", description="Current period identifier"),
                    ToolParam(name="previous_period", type="string", description="Previous period identifier"),
                ]),
            }
        ],
        AnalysisType.CLASSIFICATION: [
            {
                "name": "segment_by_dimensions",
                "description": "Break down the metric by key dimensions (region, user type, channel)",
                "sql_hint": (
                    "SELECT {dimension}, SUM({metric}) AS total, COUNT(*) AS cnt "
                    "FROM {table} "
                    "GROUP BY {dimension} "
                    "ORDER BY total DESC"
                ),
                "parameters": _sql_params([
                    ToolParam(name="dimension", type="string", description="Dimension column to segment by (e.g., region, user_type, channel)"),
                ]),
            },
            {
                "name": "outlier_detection",
                "description": "Identify segments that deviate most from the baseline",
                "sql_hint": (
                    "SELECT {dimension}, {metric}, "
                    "({metric} - baseline_avg) / baseline_std AS z_score "
                    "FROM ("
                    "SELECT {dimension}, {metric}, "
                    "AVG({metric}) OVER() AS baseline_avg, "
                    "STDDEV({metric}) OVER() AS baseline_std "
                    "FROM {table}"
                    ") sub "
                    "WHERE ABS(z_score) > 2 "
                    "ORDER BY ABS(z_score) DESC"
                ),
                "parameters": _sql_params([
                    ToolParam(name="dimension", type="string", description="Dimension column to segment by"),
                ]),
            }
        ],
        AnalysisType.ATTRIBUTION: [
            {
                "name": "correlation_analysis",
                "description": "Calculate correlation between target metric and potential factors",
                "sql_hint": (
                    "SELECT CORR({metric}, {factor_1}) AS corr_factor1, "
                    "CORR({metric}, {factor_2}) AS corr_factor2, "
                    "CORR({metric}, {factor_3}) AS corr_factor3 "
                    "FROM {table}"
                ),
                "parameters": _sql_params([
                    ToolParam(name="factor_1", type="string", description="First factor column name"),
                    ToolParam(name="factor_2", type="string", description="Second factor column name"),
                    ToolParam(name="factor_3", type="string", description="Third factor column name"),
                ]),
            },
            {
                "name": "variance_decomposition",
                "description": "Decompose total change by dimension contributions",
                "sql_hint": (
                    "SELECT {dimension}, current_val, previous_val, "
                    "(current_val - previous_val) AS absolute_change, "
                    "(current_val - previous_val) / total_previous AS contribution_pct "
                    "FROM ("
                    "SELECT {dimension}, "
                    "SUM(CASE WHEN {period_col} = '{current_period}' THEN {metric} END) AS current_val, "
                    "SUM(CASE WHEN {period_col} = '{previous_period}' THEN {metric} END) AS previous_val "
                    "FROM {table} GROUP BY {dimension}"
                    ") sub, "
                    "(SELECT SUM({metric}) AS total_previous FROM {table} WHERE {period_col} = '{previous_period}') total "
                    "ORDER BY contribution_pct DESC"
                ),
                "parameters": _sql_params([
                    ToolParam(name="dimension", type="string", description="Dimension column for decomposition"),
                    ToolParam(name="period_col", type="string", description="Period column name", default="period"),
                    ToolParam(name="current_period", type="string", description="Current period identifier"),
                    ToolParam(name="previous_period", type="string", description="Previous period identifier"),
                ]),
            }
        ],
        AnalysisType.PREDICTION: [
            {
                "name": "time_series_aggregation",
                "description": "Aggregate metric by time granularity for forecasting",
                "sql_hint": (
                    "SELECT DATE_TRUNC('{granularity}', {date_col}) AS period, "
                    "SUM({metric}) AS total_value "
                    "FROM {table} "
                    "GROUP BY period "
                    "ORDER BY period"
                ),
                "parameters": _sql_params([
                    ToolParam(name="granularity", type="string", description="Time granularity: day, week, month", default="day"),
                ]),
            },
            {
                "name": "seasonality_analysis",
                "description": "Extract weekly/monthly seasonality patterns",
                "sql_hint": (
                    "SELECT EXTRACT(DOW FROM {date_col}) AS day_of_week, "
                    "AVG({metric}) AS avg_metric "
                    "FROM {table} "
                    "GROUP BY day_of_week "
                    "ORDER BY day_of_week"
                ),
                "parameters": _sql_params([]),
            }
        ]
    }

    PYTHON_TEMPLATES = {
        AnalysisType.BENCHMARK: [
            {
                "name": "statistical_significance_test",
                "description": "Perform statistical tests to determine if change is significant",
                "code_hint": (
                    "from scipy import stats\n"
                    "# t-test between two periods\n"
                    "t_stat, p_value = stats.ttest_ind({period_a}, {period_b})\n"
                    "print(f't-statistic: {t_stat}, p-value: {p_value}')\n"
                    "print('Significant' if p_value < 0.05 else 'Not significant')"
                ),
                "parameters": _python_params([
                    ToolParam(name="period_a", type="array", description="Values from period A"),
                    ToolParam(name="period_b", type="array", description="Values from period B"),
                ]),
            }
        ],
        AnalysisType.CLASSIFICATION: [
            {
                "name": "clustering_analysis",
                "description": "Cluster segments to find natural groupings",
                "code_hint": (
                    "from sklearn.cluster import KMeans\n"
                    "import numpy as np\n"
                    "# X: feature matrix of shape (n_samples, n_features)\n"
                    "kmeans = KMeans(n_clusters={n_clusters}, random_state=42)\n"
                    "labels = kmeans.fit_predict({X})\n"
                    "print(f'Cluster centers: {kmeans.cluster_centers_}')"
                ),
                "parameters": _python_params([
                    ToolParam(name="X", type="array", description="Feature matrix (n_samples, n_features)"),
                    ToolParam(name="n_clusters", type="int", description="Number of clusters", default="3"),
                ]),
            }
        ],
        AnalysisType.ATTRIBUTION: [
            {
                "name": "shapley_value_attribution",
                "description": "Calculate Shapley values for fair attribution",
                "code_hint": (
                    "import shap\n"
                    "import xgboost as xgb\n"
                    "model = xgb.XGBRegressor(random_state=42)\n"
                    "model.fit({X}, {y})\n"
                    "explainer = shap.TreeExplainer(model)\n"
                    "shap_values = explainer.shap_values({X})\n"
                    "shap.summary_plot(shap_values, {X})"
                ),
                "parameters": _python_params([
                    ToolParam(name="X", type="DataFrame", description="Feature matrix"),
                    ToolParam(name="y", type="Series", description="Target variable"),
                ]),
            },
            {
                "name": "causal_inference_did",
                "description": "Difference-in-Differences analysis for causal estimation",
                "code_hint": (
                    "import statsmodels.formula.api as smf\n"
                    "# DiD model: outcome ~ treatment * post + covariates\n"
                    "model = smf.ols('{outcome_col} ~ {treatment_col} * {post_col} + {covariates}', data={df})\n"
                    "result = model.fit()\n"
                    "print(result.summary())\n"
                    "print(f'\\nTreatment effect (DiD): {result.params[\"{treatment_col}:{post_col}\"]:.4f}')"
                ),
                "parameters": _python_params([
                    ToolParam(name="outcome_col", type="string", description="Outcome column name"),
                    ToolParam(name="treatment_col", type="string", description="Treatment group indicator column"),
                    ToolParam(name="post_col", type="string", description="Post-period indicator column"),
                    ToolParam(name="covariates", type="string", description="Covariate column names separated by +", default=""),
                ]),
            }
        ],
        AnalysisType.PREDICTION: [
            {
                "name": "prophet_forecasting",
                "description": "Time series forecasting using Prophet",
                "code_hint": (
                    "from prophet import Prophet\n"
                    "# df must have columns 'ds' (date) and 'y' (value)\n"
                    "m = Prophet(yearly_seasonality=True, weekly_seasonality=True)\n"
                    "m.fit({df})\n"
                    "future = m.make_future_dataframe(periods={forecast_periods})\n"
                    "forecast = m.predict(future)\n"
                    "fig = m.plot(forecast)"
                ),
                "parameters": _python_params([
                    ToolParam(name="forecast_periods", type="int", description="Number of periods to forecast", default="30"),
                ]),
            }
        ]
    }

    VIZ_TEMPLATES = {
        AnalysisType.BENCHMARK: [
            {
                "name": "time_series_chart",
                "description": "Plot metric over time with baseline band",
                "parameters": [
                    ToolParam(name="title", type="string", description="Chart title", required=False),
                ],
            },
            {
                "name": "distribution_histogram",
                "description": "Histogram of metric distribution",
                "parameters": [
                    ToolParam(name="bins", type="int", description="Number of bins", default="30"),
                ],
            }
        ],
        AnalysisType.CLASSIFICATION: [
            {
                "name": "bar_chart_by_segment",
                "description": "Bar chart comparing segments",
                "parameters": [
                    ToolParam(name="top_n", type="int", description="Show top N segments", default="10"),
                ],
            },
            {
                "name": "heatmap",
                "description": "Heatmap of metric across two dimensions",
                "parameters": [
                    ToolParam(name="x_dim", type="string", description="X-axis dimension"),
                    ToolParam(name="y_dim", type="string", description="Y-axis dimension"),
                ],
            }
        ],
        AnalysisType.ATTRIBUTION: [
            {
                "name": "waterfall_chart",
                "description": "Waterfall chart showing factor contributions",
                "parameters": [
                    ToolParam(name="measure", type="string", description="Measure column", default="contribution"),
                ],
            },
            {
                "name": "scatter_plot",
                "description": "Scatter plot of metric vs factor",
                "parameters": [
                    ToolParam(name="x_col", type="string", description="X-axis column"),
                    ToolParam(name="y_col", type="string", description="Y-axis column"),
                ],
            }
        ],
        AnalysisType.PREDICTION: [
            {
                "name": "forecast_chart",
                "description": "Line chart with forecast and confidence interval",
                "parameters": [
                    ToolParam(name="show_confidence", type="bool", description="Show confidence interval", default="true"),
                ],
            },
            {
                "name": "scenario_comparison",
                "description": "Bar chart comparing different scenarios",
                "parameters": [
                    ToolParam(name="scenarios", type="list", description="List of scenario names"),
                ],
            }
        ]
    }


# ---------------------------------------------------------------------------
# Context → AnalysisType mapping for automatic recommendation
# ---------------------------------------------------------------------------

CONTEXT_TO_ANALYSIS_MAP = {
    QuestionContext.IS_NORMAL: [
        AnalysisType.BENCHMARK,
    ],
    QuestionContext.CHANGE_WITH_MAGNITUDE: [
        AnalysisType.BENCHMARK,
        AnalysisType.CLASSIFICATION,
        AnalysisType.ATTRIBUTION,
    ],
    QuestionContext.COMPARISON: [
        AnalysisType.BENCHMARK,
        AnalysisType.CLASSIFICATION,
    ],
    QuestionContext.PREDICTION: [
        AnalysisType.BENCHMARK,
        AnalysisType.PREDICTION,
    ],
    QuestionContext.FUNNEL: [
        AnalysisType.BENCHMARK,
        AnalysisType.CLASSIFICATION,
        AnalysisType.ATTRIBUTION,
    ],
    QuestionContext.RETENTION: [
        AnalysisType.BENCHMARK,
        AnalysisType.CLASSIFICATION,
        AnalysisType.PREDICTION,
    ],
    QuestionContext.GENERAL: [
        AnalysisType.BENCHMARK,
        AnalysisType.CLASSIFICATION,
        AnalysisType.ATTRIBUTION,
        AnalysisType.PREDICTION,
    ],
}

CONTEXT_REASONING_MAP = {
    QuestionContext.IS_NORMAL:
        "Questions about normality only need baseline comparison to determine if values are within expected range.",
    QuestionContext.CHANGE_WITH_MAGNITUDE:
        "Questions mentioning a change magnitude require: 1) baseline to confirm significance, 2) classification to find where the change is, 3) attribution to understand why it happened.",
    QuestionContext.COMPARISON:
        "Comparison questions need baseline values for each group and segmentation to identify differences.",
    QuestionContext.PREDICTION:
        "Prediction questions need historical baseline patterns and then forecasting models to project future outcomes.",
    QuestionContext.FUNNEL:
        "Funnel questions need baseline conversion rates, segmentation by drop-off points, and attribution of causes.",
    QuestionContext.RETENTION:
        "Retention questions need baseline retention rates, segmentation by user groups, and prediction of future retention/LTV.",
    QuestionContext.GENERAL:
        "For general questions, we recommend the full four-step analysis workflow for comprehensive coverage.",
}


# ---------------------------------------------------------------------------
# Main Skill class
# ---------------------------------------------------------------------------

class DataAnalyticSkill:
    """
    A framework for decomposing complex data analysis questions
    into structured analysis plans and executable tool calls.

    This skill serves as a PLANNING GUIDE for agents, providing:
    1. Analysis types framework
    2. Workflow sequence guidance
    3. Analysis dimension explanations
    4. Structured tool call generation with parameter schemas
    5. Automatic analysis type recommendation from questions
    """

    ANALYSIS_DIMENSIONS = {
        AnalysisType.BENCHMARK: {
            "purpose": "Establishing baseline and threshold to determine if changes are meaningful",
            "focus": "What is normal? Is the change significant?",
            "key_methods": [
                "Historical comparison (YoY, MoM, WoW)",
                "Statistical threshold (σ, confidence interval)",
                "Business rules and benchmarks"
            ]
        },
        AnalysisType.CLASSIFICATION: {
            "purpose": "Identifying where/who changed - which segments show unusual behavior",
            "focus": "Where is the anomaly? Which groups are affected?",
            "key_methods": [
                "Segmentation by dimensions (user type, region, channel, time)",
                "Distribution analysis",
                "Outlier detection"
            ]
        },
        AnalysisType.ATTRIBUTION: {
            "purpose": "Explaining why - quantifying contributions of each factor",
            "focus": "Why did it happen? What caused the change?",
            "key_methods": [
                "Correlation analysis",
                "Regression decomposition",
                "Causal inference (A/B tests, counterfactual)"
            ]
        },
        AnalysisType.PREDICTION: {
            "purpose": "Forecasting future outcomes based on patterns and drivers",
            "focus": "What will happen? Under what scenarios?",
            "key_methods": [
                "Time series forecasting",
                "Driver-based projection",
                "Scenario analysis"
            ]
        }
    }

    GUIDANCE_TEMPLATES = {
        QuestionContext.IS_NORMAL: {
            AnalysisType.BENCHMARK: {
                "logic": "Establish baseline to compare current value against historical data. Use YoY/MoM/WoW to find the appropriate comparison period.",
                "guidance": "Calculate historical average and standard deviation. Compare current value against the baseline to determine if it's within normal range."
            }
        },
        QuestionContext.CHANGE_WITH_MAGNITUDE: {
            AnalysisType.BENCHMARK: {
                "logic": "The question mentions a specific change magnitude. First establish baseline, then determine if this magnitude exceeds normal fluctuation.",
                "guidance": "Use appropriate comparison method (YoY/MoM/WoW) to establish baseline. Calculate the expected range based on historical volatility. Determine if the mentioned change is statistically significant."
            },
            AnalysisType.CLASSIFICATION: {
                "logic": "Since a significant change is mentioned, segment data to identify which parts/groups contribute to this change.",
                "guidance": "Break down the metric by dimensions (time, user type, region, channel, etc.) to pinpoint which segments deviate most from baseline."
            },
            AnalysisType.ATTRIBUTION: {
                "logic": "With the change magnitude confirmed, investigate what external/internal factors could cause this scale of change.",
                "guidance": "Identify potential causal factors (marketing campaigns, product changes, external events, etc.). Quantify each factor's contribution to the total change."
            }
        },
        QuestionContext.COMPARISON: {
            AnalysisType.BENCHMARK: {
                "logic": "For comparison questions, establish baseline values for each group being compared.",
                "guidance": "Calculate baseline metrics for each group. Use appropriate normalization if groups have different scales."
            },
            AnalysisType.CLASSIFICATION: {
                "logic": "Segment by the comparison dimensions to identify which groups differ and how.",
                "guidance": "Compare metrics across groups. Calculate the difference and determine if it's statistically significant."
            }
        },
        QuestionContext.PREDICTION: {
            AnalysisType.BENCHMARK: {
                "logic": "For prediction, first establish the historical pattern and seasonality as baseline.",
                "guidance": "Analyze historical trends, seasonality, and periodicity. Identify the baseline pattern for forecasting."
            },
            AnalysisType.PREDICTION: {
                "logic": "Based on historical patterns and identified drivers, forecast future values.",
                "guidance": "Build prediction model considering trends, seasonality, and key drivers. Generate confidence intervals and scenario projections."
            }
        },
        QuestionContext.FUNNEL: {
            AnalysisType.BENCHMARK: {
                "logic": "For funnel analysis, first establish baseline conversion rates at each stage.",
                "guidance": "Calculate conversion rates between each funnel stage. Compare against historical benchmarks."
            },
            AnalysisType.CLASSIFICATION: {
                "logic": "Segment funnel by user groups to find where conversion drops most.",
                "guidance": "Break down funnel by dimensions (user type, source, device). Identify segments with lowest conversion."
            },
            AnalysisType.ATTRIBUTION: {
                "logic": "Attribute drop-off to specific stages and causes.",
                "guidance": "Analyze user behavior at each drop-off point. Correlate with product changes, page performance, or external factors."
            }
        },
        QuestionContext.RETENTION: {
            AnalysisType.BENCHMARK: {
                "logic": "Establish baseline retention rates (D1, D7, D30).",
                "guidance": "Calculate retention cohorts. Compare against historical benchmarks and industry standards."
            },
            AnalysisType.CLASSIFICATION: {
                "logic": "Segment users to identify which groups have different retention patterns.",
                "guidance": "Break down retention by acquisition channel, user type, region. Identify high and low retention segments."
            },
            AnalysisType.PREDICTION: {
                "logic": "Forecast future retention based on current cohort behavior.",
                "guidance": "Build retention curve models. Predict LTV (Lifetime Value) based on retention patterns."
            }
        }
    }

    WORKFLOW_ORDER = [
        AnalysisType.BENCHMARK,
        AnalysisType.CLASSIFICATION,
        AnalysisType.ATTRIBUTION,
        AnalysisType.PREDICTION,
    ]

    def __init__(self, classifier: Optional[QuestionClassifier] = None):
        """
        Initialize the DataAnalyticSkill.

        Args:
            classifier: Optional QuestionClassifier implementation.
                       If not provided, uses KeywordClassifier by default.
                       Agents can inject LLM-based classifiers here.
        """
        self.classifier = classifier or KeywordClassifier()

    def set_classifier(self, classifier: QuestionClassifier) -> None:
        """
        Replace the current question classifier with a new one.

        Args:
            classifier: The new QuestionClassifier implementation to use.
        """
        self.classifier = classifier

    def classify_question(self, question: str) -> List[str]:
        """
        Classify a question using the configured classifier.

        Args:
            question: The user's natural language question.

        Returns:
            List of context tag strings.
        """
        contexts = self.classifier.classify(question)
        return [ctx.value for ctx in contexts]

    def recommend_analysis_types(self, question: str) -> AnalysisRecommendation:
        """
        Recommend analysis types based on the question content.

        This method uses the configured classifier to detect question context,
        then maps contexts to recommended analysis types.

        Args:
            question: The user's natural language question.

        Returns:
            AnalysisRecommendation with recommended types and reasoning.
        """
        contexts = self._detect_question_context(question)

        recommended_set = set()
        reasonings = []
        for ctx in contexts:
            types = CONTEXT_TO_ANALYSIS_MAP.get(ctx, [])
            recommended_set.update(types)
            reasoning = CONTEXT_REASONING_MAP.get(ctx, "")
            if reasoning:
                reasonings.append(reasoning)

        ordered_types = [at for at in self.WORKFLOW_ORDER if at in recommended_set]

        return AnalysisRecommendation(
            question=question,
            contexts=[ctx.value for ctx in contexts],
            recommended_types=[at.value for at in ordered_types],
            reasoning=" ".join(reasonings) if reasonings else CONTEXT_REASONING_MAP[QuestionContext.GENERAL],
        )

    def _detect_question_context(self, question: str) -> List[QuestionContext]:
        """Internal: detect context using the configured classifier."""
        return self.classifier.classify(question)

    def _generate_targeted_guidance(self, analysis_type: AnalysisType,
                                    contexts: List[QuestionContext]) -> Dict:
        """Generate targeted guidance based on question context."""
        result = {
            "purpose": self.ANALYSIS_DIMENSIONS[analysis_type]["purpose"],
            "focus": self.ANALYSIS_DIMENSIONS[analysis_type]["focus"],
            "key_methods": self.ANALYSIS_DIMENSIONS[analysis_type]["key_methods"]
        }

        best_match = None
        for context in contexts:
            if context in self.GUIDANCE_TEMPLATES:
                if analysis_type in self.GUIDANCE_TEMPLATES[context]:
                    best_match = self.GUIDANCE_TEMPLATES[context][analysis_type]
                    break

        if best_match:
            result["logic"] = best_match.get("logic", "")
            result["guidance"] = best_match.get("guidance", "")
        else:
            result["logic"] = "Follow the standard analysis approach for this type."
            result["guidance"] = "Apply appropriate methods based on the context."

        return result

    def explain_framework(self) -> Dict[str, str]:
        """
        Explain the four core analysis dimensions with their purposes.

        Returns:
            Dict mapping analysis type to its purpose description
        """
        return {
            at.value: f"{info['purpose']}. Focus: {info['focus']}"
            for at, info in self.ANALYSIS_DIMENSIONS.items()
        }

    def get_analysis_guidance(self, analysis_type: Union[str, AnalysisType]) -> Dict:
        """
        Get detailed guidance for a specific analysis type.

        Args:
            analysis_type: The analysis type to get guidance for

        Returns:
            Dict containing purpose, focus, methods, and guidance
        """
        if isinstance(analysis_type, str):
            try:
                analysis_type = AnalysisType(analysis_type)
            except ValueError:
                return {}

        return self.ANALYSIS_DIMENSIONS.get(analysis_type, {})

    def get_workflow(self, analysis_types: Optional[List[AnalysisType]] = None,
                     question: Optional[str] = None) -> List[WorkflowStep]:
        """
        Get the recommended analysis workflow with targeted guidance.

        Args:
            analysis_types: Optional list to filter relevant steps.
                          If None, uses recommended types from question (if provided)
                          or all four types.
            question: Optional user question for context-specific guidance.
                      If provided, generates targeted logic and guidance.

        Returns:
            List of WorkflowStep objects with context-specific guidance
        """
        contexts = self._detect_question_context(question) if question else []

        if analysis_types is None:
            if question:
                rec = self.recommend_analysis_types(question)
                analysis_types = [AnalysisType(t) for t in rec.recommended_types]
            else:
                analysis_types = list(self.WORKFLOW_ORDER)

        analysis_type_set = set(analysis_types)
        result = []
        order = 1

        for at in self.WORKFLOW_ORDER:
            if at in analysis_type_set:
                guidance = self._generate_targeted_guidance(at, contexts)
                result.append(WorkflowStep(
                    order=order,
                    type=at.value,
                    logic=guidance.get("logic", ""),
                    guidance=guidance.get("guidance", "")
                ))
                order += 1

        return result

    def generate_tool_calls(self, analysis_types: Optional[List[AnalysisType]] = None,
                            question: Optional[str] = None,
                            tool_types: Optional[List[ToolCallType]] = None) -> List[ToolCall]:
        """
        Generate structured tool call sequences for the given analysis types.

        This provides actionable tool calls that the agent can execute,
        including SQL queries, Python snippets, and visualization suggestions.
        Each tool call includes parameter schemas and placeholder tracking.

        Args:
            analysis_types: Optional list of analysis types. If None, includes
                          recommended types based on question (or all four).
            question: Optional user question for context-aware tool selection.
            tool_types: Optional filter for specific tool call types.
                       If None, includes SQL and Python tool calls.

        Returns:
            List of ToolCall objects with parameter schemas and placeholders.
        """
        contexts = self._detect_question_context(question) if question else []

        if analysis_types is None:
            if question:
                rec = self.recommend_analysis_types(question)
                analysis_types = [AnalysisType(t) for t in rec.recommended_types]
            else:
                analysis_types = list(self.WORKFLOW_ORDER)

        if tool_types is None:
            tool_types = [ToolCallType.SQL_QUERY, ToolCallType.PYTHON_SNIPPET]

        tool_calls: List[ToolCall] = []
        order = 1

        for at in self.WORKFLOW_ORDER:
            if at not in analysis_types:
                continue

            if ToolCallType.SQL_QUERY in tool_types:
                for tmpl in AnalysisDimension.SQL_TEMPLATES.get(at, []):
                    params = tmpl.get("parameters", [])
                    content = tmpl["sql_hint"]
                    placeholders = _extract_placeholders(content)
                    tool_calls.append(ToolCall(
                        order=order,
                        analysis_type=at.value,
                        tool_type=ToolCallType.SQL_QUERY.value,
                        name=tmpl["name"],
                        description=tmpl["description"],
                        content=content,
                        parameters=list(params),
                        placeholders=placeholders,
                    ))
                    order += 1

            if ToolCallType.PYTHON_SNIPPET in tool_types:
                for tmpl in AnalysisDimension.PYTHON_TEMPLATES.get(at, []):
                    params = tmpl.get("parameters", [])
                    content = tmpl["code_hint"]
                    placeholders = _extract_placeholders(content)
                    tool_calls.append(ToolCall(
                        order=order,
                        analysis_type=at.value,
                        tool_type=ToolCallType.PYTHON_SNIPPET.value,
                        name=tmpl["name"],
                        description=tmpl["description"],
                        content=content,
                        parameters=list(params),
                        placeholders=placeholders,
                    ))
                    order += 1

            if ToolCallType.VISUALIZATION in tool_types:
                for tmpl in AnalysisDimension.VIZ_TEMPLATES.get(at, []):
                    params = tmpl.get("parameters", [])
                    content = tmpl.get("spec", tmpl["description"])
                    placeholders = _extract_placeholders(content)
                    tool_calls.append(ToolCall(
                        order=order,
                        analysis_type=at.value,
                        tool_type=ToolCallType.VISUALIZATION.value,
                        name=tmpl["name"],
                        description=tmpl["description"],
                        content=content,
                        parameters=list(params),
                        placeholders=placeholders,
                    ))
                    order += 1

        return tool_calls

    def get_all_analysis_types(self) -> List[Dict]:
        """Get all analysis types with their basic information."""
        return [
            {
                "type": at.value,
                "purpose": info["purpose"],
                "focus": info["focus"]
            }
            for at, info in self.ANALYSIS_DIMENSIONS.items()
        ]

    def get_analysis_type_description(self, analysis_type: Union[str, AnalysisType]) -> str:
        """Get description for a specific analysis type."""
        if isinstance(analysis_type, str):
            try:
                analysis_type = AnalysisType(analysis_type)
            except ValueError:
                return ""

        info = self.ANALYSIS_DIMENSIONS.get(analysis_type, {})
        return f"{info.get('purpose', '')} Focus: {info.get('focus', '')}"

    def get_available_contexts(self) -> List[Dict]:
        """Get all available question context types."""
        return [
            {"context": ctx.value, "description": ctx.name.replace("_", " ").title()}
            for ctx in QuestionContext
        ]
