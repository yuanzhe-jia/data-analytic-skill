from skill import DataAnalyticSkill, AnalysisType


def test_workflow_structure():
    """Test workflow structure - simplified to only logic and guidance."""
    skill = DataAnalyticSkill()
    
    # Test full workflow
    workflow = skill.get_workflow()
    assert len(workflow) == 4
    
    # Verify simplified structure - only order, type, logic, guidance
    for step in workflow:
        assert "order" in step
        assert "type" in step
        assert "logic" in step
        assert "guidance" in step
        # Should NOT have these fields
        assert "description" not in step
        assert "purpose" not in step
        assert "focus" not in step
        assert "key_methods" not in step
        assert "questions" not in step
    
    print("✓ Workflow structure is simplified correctly")


def test_targeted_guidance():
    """Test targeted guidance generation."""
    skill = DataAnalyticSkill()
    
    # Test guidance for "is this normal" question
    guidance = skill._generate_targeted_guidance(
        AnalysisType.BENCHMARK, 
        ["is_normal_question"]
    )
    assert "Calculate historical average" in guidance["guidance"]
    assert "logic" in guidance
    assert "guidance" in guidance
    print("✓ Targeted guidance for 'is_normal_question' works")
    
    # Test guidance for change with magnitude
    guidance = skill._generate_targeted_guidance(
        AnalysisType.BENCHMARK,
        ["change_with_magnitude"]
    )
    assert "change magnitude" in guidance["logic"]
    assert "guidance" in guidance
    print("✓ Targeted guidance for 'change_with_magnitude' works")


def test_workflow_with_question():
    """Test workflow generation with original question."""
    skill = DataAnalyticSkill()
    
    workflow = skill.get_workflow(
        [AnalysisType.BENCHMARK],
        "这周的活跃用户是100，这是正常的吗？"
    )
    
    assert len(workflow) == 1
    assert workflow[0]["type"] == "benchmark"
    assert "Calculate historical average" in workflow[0]["guidance"]
    assert "logic" in workflow[0]
    assert "guidance" in workflow[0]
    print("✓ Workflow with question generates targeted guidance")


def test_workflow_filtering():
    """Test workflow filtering."""
    skill = DataAnalyticSkill()
    
    workflow = skill.get_workflow([AnalysisType.BENCHMARK, AnalysisType.ATTRIBUTION])
    
    assert len(workflow) == 2
    assert workflow[0]["type"] == "benchmark"
    assert workflow[1]["type"] == "attribution"
    assert workflow[0]["order"] == 1
    assert workflow[1]["order"] == 2
    
    print("✓ Workflow filtering works correctly")


def test_context_detection():
    """Test question context detection."""
    skill = DataAnalyticSkill()
    
    # Test normal question
    contexts = skill._detect_question_context("这周的活跃用户是100，这是正常的吗？")
    assert "is_normal_question" in contexts
    print("✓ is_normal_question context detected")
    
    # Test change with magnitude
    contexts = skill._detect_question_context("为什么活跃用户降低了30%？")
    assert "change_with_magnitude" in contexts
    print("✓ change_with_magnitude context detected")
    
    # Test comparison question
    contexts = skill._detect_question_context("对比新老用户的转化率")
    assert "comparison_question" in contexts
    print("✓ comparison_question context detected")
    
    # Test prediction question
    contexts = skill._detect_question_context("未来10天的销售情况会怎么样？")
    assert "prediction_question" in contexts
    print("✓ prediction_question context detected")


def test_four_questions():
    """Test all four question types with simplified output."""
    skill = DataAnalyticSkill()
    
    questions = [
        ("这周的活跃用户是100，这是正常的吗？", [AnalysisType.BENCHMARK]),
        ("为什么活跃用户降低了30%？", [AnalysisType.BENCHMARK, AnalysisType.CLASSIFICATION, AnalysisType.ATTRIBUTION]),
        ("对比新老用户从加购到下单的转化率", [AnalysisType.BENCHMARK, AnalysisType.CLASSIFICATION]),
        ("未来10天的销售情况会怎么样？", [AnalysisType.BENCHMARK, AnalysisType.PREDICTION])
    ]
    
    for question, types in questions:
        workflow = skill.get_workflow(types, question)
        
        # Verify each step has only order, type, logic, guidance
        for step in workflow:
            assert set(step.keys()) == {"order", "type", "logic", "guidance"}
            assert step["logic"] != ""
            assert step["guidance"] != ""
        
        print(f"✓ '{question}' - {len(workflow)} steps, all simplified")


def main():
    print("=" * 60)
    print("Running DataAnalyticSkill Tests")
    print("=" * 60)
    
    test_context_detection()
    test_targeted_guidance()
    test_workflow_with_question()
    test_workflow_structure()
    test_workflow_filtering()
    test_four_questions()
    
    print("=" * 60)
    print("All tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
