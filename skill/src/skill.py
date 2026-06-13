from typing import List, Dict, Optional, Union
from enum import Enum


class AnalysisType(Enum):
    """Four core analysis dimensions for data analysis."""
    BENCHMARK = "benchmark"
    CLASSIFICATION = "classification"
    ATTRIBUTION = "attribution"
    PREDICTION = "prediction"


class DataAnalyticSkill:
    """
    A framework for decomposing complex data analysis questions 
    into structured analysis plans.
    
    This skill serves as a PLANNING GUIDE for agents, providing:
    1. Analysis types framework
    2. Workflow sequence guidance
    3. Analysis dimension explanations
    
    The agent should use its own LLM/NLU to:
    - Classify question types
    - Generate specific analysis plans
    - Create actionable sub-questions
    
    This skill only provides framework guidance, not specific templates.
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
    
    # Context-specific guidance templates
    GUIDANCE_TEMPLATES = {
        "is_normal_question": {
            AnalysisType.BENCHMARK: {
                "logic": "Establish baseline to compare current value against historical data. Use YoY/MoM/WoW to find the appropriate comparison period.",
                "guidance": "Calculate historical average and standard deviation. Compare current value against the baseline to determine if it's within normal range."
            }
        },
        "change_with_magnitude": {
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
        "comparison_question": {
            AnalysisType.BENCHMARK: {
                "logic": "For comparison questions, establish baseline values for each group being compared.",
                "guidance": "Calculate baseline metrics for each group. Use appropriate normalization if groups have different scales."
            },
            AnalysisType.CLASSIFICATION: {
                "logic": "Segment by the comparison dimensions to identify which groups differ and how.",
                "guidance": "Compare metrics across groups. Calculate the difference and determine if it's statistically significant."
            }
        },
        "prediction_question": {
            AnalysisType.BENCHMARK: {
                "logic": "For prediction, first establish the historical pattern and seasonality as baseline.",
                "guidance": "Analyze historical trends, seasonality, and periodicity. Identify the baseline pattern for forecasting."
            },
            AnalysisType.PREDICTION: {
                "logic": "Based on historical patterns and identified drivers, forecast future values.",
                "guidance": "Build prediction model considering trends, seasonality, and key drivers. Generate confidence intervals and scenario projections."
            }
        }
    }
    
    def _detect_question_context(self, question: str) -> List[str]:
        """
        Detect the context of the question based on its content.
        
        Returns list of context tags that match the question.
        """
        contexts = []
        question_lower = question.lower()
        
        # Check if it's a "is this normal" question
        if any(keyword in question_lower for keyword in ['正常', 'normal', 'regular', 'expected', 'standard']):
            contexts.append("is_normal_question")
        
        # Check if it mentions a specific change magnitude
        if any(keyword in question_lower for keyword in ['下降', '降低', '增长', '上升', 'drop', 'decrease', 'increase', 'rise', '%', 'percent']):
            contexts.append("change_with_magnitude")
        
        # Check if it's a comparison question
        if any(keyword in question_lower for keyword in ['对比', '比较', 'compare', '对比']):
            contexts.append("comparison_question")
        
        # Check if it's a prediction question
        if any(keyword in question_lower for keyword in ['未来', '预测', 'forecast', 'predict', 'will', '预期']):
            contexts.append("prediction_question")
        
        # Default context
        if not contexts:
            contexts.append("change_with_magnitude")  # Default assumption
        
        return contexts
    
    def _generate_targeted_guidance(self, analysis_type: AnalysisType, contexts: List[str]) -> Dict:
        """
        Generate targeted guidance based on question context.
        """
        # Start with base information
        result = {
            "purpose": self.ANALYSIS_DIMENSIONS[analysis_type]["purpose"],
            "focus": self.ANALYSIS_DIMENSIONS[analysis_type]["focus"],
            "key_methods": self.ANALYSIS_DIMENSIONS[analysis_type]["key_methods"]
        }
        
        # Collect context-specific guidance
        best_match = None
        for context in contexts:
            if context in self.GUIDANCE_TEMPLATES:
                if analysis_type in self.GUIDANCE_TEMPLATES[context]:
                    template = self.GUIDANCE_TEMPLATES[context][analysis_type]
                    best_match = template
                    break
        
        if best_match:
            result["logic"] = best_match.get("logic", "")
            result["guidance"] = best_match.get("guidance", "")
        else:
            # Fallback to generic guidance
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
        
        This provides abstract guidance that the agent should use
        to generate specific analysis plans.
        
        Args:
            analysis_type: The analysis type to get guidance for
            
        Returns:
            Dict containing purpose, focus, methods, and guidance
        """
        if isinstance(analysis_type, str):
            analysis_type = AnalysisType(analysis_type)
        
        return self.ANALYSIS_DIMENSIONS.get(analysis_type, {})
    
    def get_workflow(self, analysis_types: Optional[List[AnalysisType]] = None, 
                     original_question: Optional[str] = None) -> List[Dict]:
        """
        Get the recommended analysis workflow with targeted guidance.
        
        Args:
            analysis_types: Optional list to filter relevant steps.
            original_question: Optional original question for context-specific guidance.
                             If provided, generates targeted logic and guidance.
                             
        Returns:
            List of workflow steps with context-specific guidance
        """
        # Determine contexts from question
        contexts = self._detect_question_context(original_question) if original_question else []
        
        # Default workflow sequence
        workflow_order = [
            (AnalysisType.BENCHMARK, "Establish baseline and thresholds"),
            (AnalysisType.CLASSIFICATION, "Identify where change occurred"),
            (AnalysisType.ATTRIBUTION, "Determine root causes"),
            (AnalysisType.PREDICTION, "Forecast future outcomes")
        ]
        
        if analysis_types is None:
            # Return full workflow
            result = []
            for order, (at, _) in enumerate(workflow_order, 1):
                guidance = self._generate_targeted_guidance(at, contexts)
                result.append({
                    "order": order,
                    "type": at.value,
                    "logic": guidance.get("logic", ""),
                    "guidance": guidance.get("guidance", "")
                })
            return result
        
        # Filter and order workflow
        analysis_type_set = set(analysis_types)
        result = []
        expected_order = 1
        
        for at, _ in workflow_order:
            if at in analysis_type_set:
                guidance = self._generate_targeted_guidance(at, contexts)
                result.append({
                    "order": expected_order,
                    "type": at.value,
                    "logic": guidance.get("logic", ""),
                    "guidance": guidance.get("guidance", "")
                })
                expected_order += 1
        
        return result
    
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
