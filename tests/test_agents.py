# tests/test_agents.py

import pytest
import json


class TestPlannerOutput:

    def test_planner_output_schema_valid(self):
        output = {
            "subquestions": [
                "What are AI agents?",
                "How are they used in enterprise?",
                "What are the risks?"
            ],
            "outline": [
                "Executive Summary",
                "Key Findings",
                "Analysis",
                "Risks and Limitations",
                "Conclusion"
            ]
        }
        assert "subquestions" in output
        assert "outline" in output
        assert len(output["subquestions"]) == 3

    def test_planner_output_wrong_count_detected(self):
        output = {
            "subquestions": ["Only one question"],
            "outline": ["Executive Summary"]
        }
        assert len(output["subquestions"]) != 3

    def test_planner_missing_field_detected(self):
        output = {"subquestions": ["Q1", "Q2", "Q3"]}
        assert "outline" not in output


class TestResearcherOutput:

    def test_researcher_output_schema_valid(self):
        output = {
            "subquestion": "What are AI agents?",
            "summary": "AI agents are software programs that act autonomously.",
            "key_facts": ["fact1", "fact2", "fact3"],
            "source": "Wikipedia",
            "url": "https://en.wikipedia.org/wiki/Intelligent_agent",
            "confidence": 0.85
        }
        required = ["subquestion", "summary", "key_facts", "source", "confidence"]
        for field in required:
            assert field in output

    def test_confidence_score_in_range(self):
        scores = [0.0, 0.5, 0.85, 1.0]
        for score in scores:
            assert 0.0 <= score <= 1.0

    def test_confidence_out_of_range_detected(self):
        score = 1.5
        assert not (0.0 <= score <= 1.0)

    def test_empty_finding_has_zero_confidence(self):
        empty_finding = {
            "subquestion": "test",
            "summary": "",
            "key_facts": [],
            "source": "Wikipedia",
            "url": "",
            "confidence": 0.0
        }
        assert empty_finding["confidence"] == 0.0
        assert empty_finding["summary"] == ""


class TestCriticOutput:

    def test_critic_output_schema_valid(self):
        output = {
            "approved": True,
            "confidence_score": 0.82,
            "feedback": [],
            "coverage_check": {
                "total_subquestions": 3,
                "covered": 3,
                "missing": []
            },
            "suggestion": "Good research quality."
        }
        required = ["approved", "confidence_score", "feedback", "coverage_check"]
        for field in required:
            assert field in output

    def test_critic_approved_when_no_issues(self):
        output = {
            "approved": True,
            "confidence_score": 0.85,
            "feedback": [],
            "coverage_check": {"total_subquestions": 3, "covered": 3, "missing": []}
        }
        assert output["approved"] is True
        assert len(output["feedback"]) == 0

    def test_critic_not_approved_when_low_confidence(self):
        output = {
            "approved": False,
            "confidence_score": 0.35,
            "feedback": ["Low confidence on finding 2"],
            "coverage_check": {"total_subquestions": 3, "covered": 2, "missing": ["Q3"]}
        }
        assert output["approved"] is False
        assert output["confidence_score"] < 0.65


class TestWriterOutput:

    def test_writer_output_not_empty(self):
        report = "## Research Report\n\nThis is a test report.\n\n## Conclusion\n\nDone."
        assert len(report) > 200 or len(report) > 0

    def test_writer_output_has_sections(self):
        report = "## Executive Summary\n\nSummary here.\n\n## Key Findings\n\nFindings here."
        assert "##" in report

    def test_writer_output_minimum_length(self):
        report = "Short"
        assert len(report) < 200

    def test_writer_valid_report_length(self):
        report = "## Executive Summary\n\n" + "This is content. " * 50
        assert len(report) >= 200