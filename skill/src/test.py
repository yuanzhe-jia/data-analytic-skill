from skill import (
    DataAnalyticSkill, AnalysisType, QuestionContext,
    QuestionClassifier, KeywordClassifier, ToolCallType,
    WorkflowStep, ToolCall, ToolParam, AnalysisRecommendation,
)


class MockLLMClassifier(QuestionClassifier):
    """Mock LLM-based classifier for testing the pluggable interface."""

    def classify(self, question: str):
        return [QuestionContext.CHANGE_WITH_MAGNITUDE, QuestionContext.COMPARISON]


# ---------------------------------------------------------------------------
# 1. Strongly-typed data contracts
# ---------------------------------------------------------------------------

def test_workflow_step_dataclass():
    """Test WorkflowStep dataclass structure and to_dict."""
    step = WorkflowStep(order=1, type="benchmark", logic="test logic", guidance="test guidance")
    assert step.order == 1
    assert step.type == "benchmark"

    d = step.to_dict()
    assert isinstance(d, dict)
    assert d["order"] == 1
    assert d["type"] == "benchmark"
    print("✓ WorkflowStep dataclass works correctly")


def test_tool_param_dataclass():
    """Test ToolParam dataclass structure."""
    param = ToolParam(name="table", type="string", description="Table name")
    assert param.required is True
    assert param.default is None

    d = param.to_dict()
    assert d["name"] == "table"
    assert d["required"] is True
    print("✓ ToolParam dataclass works correctly")


def test_tool_call_dataclass():
    """Test ToolCall dataclass with parameters and placeholders."""
    tc = ToolCall(
        order=1,
        analysis_type="benchmark",
        tool_type="sql_query",
        name="test_query",
        description="Test SQL query",
        content="SELECT {metric} FROM {table}",
        parameters=[ToolParam(name="metric", type="string", description="Metric column")],
        placeholders=["metric", "table"],
    )
    assert tc.order == 1
    assert len(tc.parameters) == 1
    assert len(tc.placeholders) == 2

    d = tc.to_dict()
    assert isinstance(d["parameters"], list)
    assert d["parameters"][0]["name"] == "metric"
    assert d["placeholders"] == ["metric", "table"]
    print("✓ ToolCall dataclass works correctly")


def test_tool_call_fill_params():
    """Test ToolCall.fill_params() replaces placeholders."""
    tc = ToolCall(
        order=1,
        analysis_type="benchmark",
        tool_type="sql_query",
        name="test",
        description="Test",
        content="SELECT {metric} FROM {table} WHERE date = '{date}'",
        parameters=[
            ToolParam(name="metric", type="string", description="Metric"),
            ToolParam(name="table", type="string", description="Table"),
            ToolParam(name="date", type="string", description="Date"),
        ],
        placeholders=["metric", "table", "date"],
    )

    filled = tc.fill_params({"metric": "revenue", "table": "sales"})
    assert "revenue" in filled.content
    assert "sales" in filled.content
    assert "{date}" in filled.content  # date not filled yet
    assert filled.placeholders == ["date"]  # only date left
    assert filled.order == 1  # other fields preserved

    print("✓ ToolCall.fill_params() works correctly")


def test_tool_call_missing_params():
    """Test ToolCall.missing_params() returns required unfilled params."""
    tc = ToolCall(
        order=1,
        analysis_type="benchmark",
        tool_type="sql_query",
        name="test",
        description="Test",
        content="SELECT {metric} FROM {table}",
        parameters=[
            ToolParam(name="metric", type="string", description="Metric", required=True),
            ToolParam(name="table", type="string", description="Table", required=True),
            ToolParam(name="limit", type="int", description="Limit", required=False, default="100"),
        ],
        placeholders=["metric", "table", "limit"],
    )

    missing = tc.missing_params()
    assert "metric" in missing
    assert "table" in missing
    assert "limit" not in missing  # not required
    print("✓ ToolCall.missing_params() works correctly")


def test_analysis_recommendation_dataclass():
    """Test AnalysisRecommendation dataclass."""
    rec = AnalysisRecommendation(
        question="Why did sales drop?",
        contexts=["change_with_magnitude"],
        recommended_types=["benchmark", "classification", "attribution"],
        reasoning="Change magnitude questions need full analysis.",
    )
    assert rec.question == "Why did sales drop?"
    assert len(rec.recommended_types) == 3

    d = rec.to_dict()
    assert d["recommended_types"] == ["benchmark", "classification", "attribution"]
    print("✓ AnalysisRecommendation dataclass works correctly")


# ---------------------------------------------------------------------------
# 2. Analysis type recommendation
# ---------------------------------------------------------------------------

def test_recommend_analysis_types_basic():
    """Test recommend_analysis_types returns AnalysisRecommendation."""
    skill = DataAnalyticSkill()

    rec = skill.recommend_analysis_types("为什么销售额下降了10%？")
    assert isinstance(rec, AnalysisRecommendation)
    assert "benchmark" in rec.recommended_types
    assert "classification" in rec.recommended_types
    assert "attribution" in rec.recommended_types
    assert rec.reasoning != ""
    print(f"✓ recommend_analysis_types works (types: {rec.recommended_types})")


def test_recommend_is_normal_question():
    """Test recommendation for is_normal question only has BENCHMARK."""
    skill = DataAnalyticSkill()

    rec = skill.recommend_analysis_types("这个数值正常吗？")
    assert rec.recommended_types == ["benchmark"]
    print("✓ is_normal question recommends only benchmark")


def test_recommend_prediction_question():
    """Test recommendation for prediction question."""
    skill = DataAnalyticSkill()

    rec = skill.recommend_analysis_types("未来30天销售额会怎样？")
    assert "benchmark" in rec.recommended_types
    assert "prediction" in rec.recommended_types
    assert "attribution" not in rec.recommended_types
    print("✓ prediction question recommends benchmark + prediction")


def test_recommend_funnel_question():
    """Test recommendation for funnel question."""
    skill = DataAnalyticSkill()

    rec = skill.recommend_analysis_types("加购到下单的转化率为什么下降了？")
    assert "benchmark" in rec.recommended_types
    assert "classification" in rec.recommended_types
    assert "attribution" in rec.recommended_types
    print("✓ funnel question recommends correct types")


def test_get_workflow_auto_recommends():
    """Test that get_workflow auto-recommends types when only question is given."""
    skill = DataAnalyticSkill()

    workflow = skill.get_workflow(question="这个数值正常吗？")
    assert len(workflow) == 1
    assert workflow[0].type == "benchmark"
    assert isinstance(workflow[0], WorkflowStep)
    print("✓ get_workflow auto-recommends types from question")


def test_generate_tool_calls_auto_recommends():
    """Test that generate_tool_calls auto-recommends types when only question is given."""
    skill = DataAnalyticSkill()

    tool_calls = skill.generate_tool_calls(question="这个数值正常吗？")
    assert len(tool_calls) > 0
    for tc in tool_calls:
        assert tc.analysis_type == "benchmark"
    print(f"✓ generate_tool_calls auto-recommends types ({len(tool_calls)} calls)")


# ---------------------------------------------------------------------------
# 3. Executable tool calls with parameter schemas
# ---------------------------------------------------------------------------

def test_generate_tool_calls_returns_toolcall_objects():
    """Test generate_tool_calls returns ToolCall objects (not dicts)."""
    skill = DataAnalyticSkill()

    tool_calls = skill.generate_tool_calls(
        [AnalysisType.BENCHMARK],
        tool_types=[ToolCallType.SQL_QUERY],
    )

    assert len(tool_calls) > 0
    for tc in tool_calls:
        assert isinstance(tc, ToolCall)
        assert isinstance(tc.parameters, list)
        assert isinstance(tc.placeholders, list)
        assert len(tc.placeholders) > 0
    print("✓ generate_tool_calls returns ToolCall objects with schemas")


def test_sql_template_placeholders_match_params():
    """Test that SQL placeholders correspond to parameter definitions."""
    skill = DataAnalyticSkill()

    tool_calls = skill.generate_tool_calls(
        [AnalysisType.BENCHMARK],
        tool_types=[ToolCallType.SQL_QUERY],
    )

    for tc in tool_calls:
        param_names = {p.name for p in tc.parameters}
        for placeholder in tc.placeholders:
            assert placeholder in param_names, \
                f"Placeholder '{placeholder}' not in parameters for {tc.name}"
    print("✓ SQL placeholders all have corresponding parameter definitions")


def test_python_template_placeholders():
    """Test Python snippets have placeholders and parameters."""
    skill = DataAnalyticSkill()

    tool_calls = skill.generate_tool_calls(
        [AnalysisType.ATTRIBUTION],
        tool_types=[ToolCallType.PYTHON_SNIPPET],
    )

    assert len(tool_calls) > 0
    for tc in tool_calls:
        assert len(tc.placeholders) > 0
        assert len(tc.parameters) > 0
    print(f"✓ Python templates have placeholders ({len(tool_calls)} templates)")


def test_tool_call_fill_params_real_template():
    """Test fill_params on a real SQL template from the skill."""
    skill = DataAnalyticSkill()

    tool_calls = skill.generate_tool_calls(
        [AnalysisType.BENCHMARK],
        tool_types=[ToolCallType.SQL_QUERY],
    )

    first_tc = tool_calls[0]
    missing_before = first_tc.missing_params()
    assert len(missing_before) > 0

    params = {"metric": "revenue", "table": "sales", "date_col": "order_date",
              "start_date": "2024-01-01", "end_date": "2024-06-30"}
    filled = first_tc.fill_params(params)

    assert "revenue" in filled.content
    assert "sales" in filled.content
    assert "2024-01-01" in filled.content
    assert len(filled.missing_params()) == 0
    print("✓ fill_params works on real SQL templates")


def test_visualization_tool_calls():
    """Test visualization tool calls have parameters."""
    skill = DataAnalyticSkill()

    tool_calls = skill.generate_tool_calls(
        [AnalysisType.BENCHMARK],
        tool_types=[ToolCallType.VISUALIZATION],
    )

    assert len(tool_calls) == 2
    for tc in tool_calls:
        assert tc.tool_type == "visualization"
        assert len(tc.parameters) > 0
    print("✓ Visualization tool calls have parameter schemas")


# ---------------------------------------------------------------------------
# 4. Regression tests for existing functionality
# ---------------------------------------------------------------------------

def test_workflow_structure():
    """Test workflow structure."""
    skill = DataAnalyticSkill()

    workflow = skill.get_workflow()
    assert len(workflow) == 4

    for step in workflow:
        assert isinstance(step, WorkflowStep)
        assert step.order > 0
        assert step.type != ""
        assert step.logic != ""
        assert step.guidance != ""

    print("✓ Workflow structure is correct")


def test_workflow_with_question_param():
    """Test that get_workflow accepts 'question' parameter."""
    skill = DataAnalyticSkill()

    workflow = skill.get_workflow(
        [AnalysisType.BENCHMARK],
        question="这周的活跃用户是100，这是正常的吗？"
    )

    assert len(workflow) == 1
    assert workflow[0].type == "benchmark"
    print("✓ get_workflow uses 'question' parameter correctly")


def test_custom_classifier():
    """Test pluggable classifier interface."""
    custom = MockLLMClassifier()
    skill = DataAnalyticSkill(classifier=custom)

    contexts = skill.classify_question("任意问题")
    assert "change_with_magnitude" in contexts
    assert "comparison_question" in contexts
    print("✓ Custom classifier injection works")


def test_set_classifier():
    """Test replacing classifier at runtime."""
    skill = DataAnalyticSkill()
    default_contexts = skill.classify_question("这是一个漏斗转化问题")
    assert "funnel_question" in default_contexts

    skill.set_classifier(MockLLMClassifier())
    new_contexts = skill.classify_question("任意问题")
    assert "change_with_magnitude" in new_contexts
    print("✓ set_classifier replaces classifier correctly")


def test_workflow_filtering():
    """Test workflow filtering."""
    skill = DataAnalyticSkill()

    workflow = skill.get_workflow([AnalysisType.BENCHMARK, AnalysisType.ATTRIBUTION])

    assert len(workflow) == 2
    assert workflow[0].type == "benchmark"
    assert workflow[1].type == "attribution"
    assert workflow[0].order == 1
    assert workflow[1].order == 2

    print("✓ Workflow filtering works correctly")


def test_invalid_analysis_type_handling():
    """Test that invalid analysis type string returns empty gracefully."""
    skill = DataAnalyticSkill()

    result = skill.get_analysis_guidance("invalid_type")
    assert result == {}

    desc = skill.get_analysis_type_description("invalid_type")
    assert desc == ""

    print("✓ Invalid analysis type handled gracefully")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 70)
    print("Running DataAnalyticSkill Tests (v3)")
    print("=" * 70)
    print()
    print("--- 1. Strongly-typed data contracts ---")
    test_workflow_step_dataclass()
    test_tool_param_dataclass()
    test_tool_call_dataclass()
    test_tool_call_fill_params()
    test_tool_call_missing_params()
    test_analysis_recommendation_dataclass()
    print()
    print("--- 2. Analysis type recommendation ---")
    test_recommend_analysis_types_basic()
    test_recommend_is_normal_question()
    test_recommend_prediction_question()
    test_recommend_funnel_question()
    test_get_workflow_auto_recommends()
    test_generate_tool_calls_auto_recommends()
    print()
    print("--- 3. Executable tool calls ---")
    test_generate_tool_calls_returns_toolcall_objects()
    test_sql_template_placeholders_match_params()
    test_python_template_placeholders()
    test_tool_call_fill_params_real_template()
    test_visualization_tool_calls()
    print()
    print("--- 4. Regression tests ---")
    test_workflow_structure()
    test_workflow_with_question_param()
    test_custom_classifier()
    test_set_classifier()
    test_workflow_filtering()
    test_invalid_analysis_type_handling()
    print()
    print("=" * 70)
    print("All tests passed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
