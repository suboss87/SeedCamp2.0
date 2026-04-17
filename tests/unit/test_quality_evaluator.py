"""Tests for the quality evaluator service.

All tests mock the OpenAI client -- no real API calls.
Verifies: grade classification, token/cost tracking, pipeline integration,
disabled-quality bypass, and dimension scoring.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.quality_schemas import QualityEvalResult
from app.models.schemas import AdScript, SKUTier
from app.services.quality_evaluator import (
    _calculate_eval_cost,
    _classify_grade,
    evaluate_video_quality,
)

# ── Fixtures ─────────────────────────────────────────────────────────────────


def _make_llm_response(overall_score: float, dimensions=None, suggestions=None):
    """Build a mock OpenAI chat completion response for quality assessment."""
    if dimensions is None:
        dimensions = [
            {"name": "prompt_clarity", "score": overall_score, "explanation": "Test"},
            {"name": "brand_alignment", "score": overall_score, "explanation": "Test"},
            {"name": "creative_quality", "score": overall_score, "explanation": "Test"},
            {"name": "technical_precision", "score": overall_score, "explanation": "Test"},
            {"name": "platform_fit", "score": overall_score, "explanation": "Test"},
        ]

    data = {
        "overall_score": overall_score,
        "dimensions": dimensions,
        "suggestions": suggestions or [],
    }

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps(data)
    mock_response.usage = MagicMock()
    mock_response.usage.prompt_tokens = 350
    mock_response.usage.completion_tokens = 160
    return mock_response


# ── Grade Classification ────────────────────────────────────────────────────


class TestClassifyGrade:
    def test_excellent(self):
        assert _classify_grade(0.8) == "excellent"
        assert _classify_grade(1.0) == "excellent"

    def test_good(self):
        assert _classify_grade(0.6) == "good"
        assert _classify_grade(0.79) == "good"

    def test_fair(self):
        assert _classify_grade(0.4) == "fair"
        assert _classify_grade(0.59) == "fair"

    def test_poor(self):
        assert _classify_grade(0.0) == "poor"
        assert _classify_grade(0.39) == "poor"


# ── Cost Calculation ────────────────────────────────────────────────────────


class TestCalculateAssessmentCost:
    def test_zero_tokens(self):
        assert _calculate_eval_cost(0, 0) == 0.0

    def test_known_tokens(self):
        cost = _calculate_eval_cost(1_000_000, 1_000_000)
        assert cost == 2.25

    def test_small_tokens(self):
        cost = _calculate_eval_cost(350, 160)
        assert cost > 0
        assert cost < 0.001


# ── Quality Assessment ──────────────────────────────────────────────────────


class TestAssessVideoQuality:
    @pytest.fixture
    def sample_script(self):
        return AdScript(
            ad_copy="Summer vibes, run free",
            scene_description="Runner at golden hour on clean urban streets",
            video_prompt="A runner sprinting through city streets at golden hour",
            camera_direction="tracking shot, low angle",
        )

    @patch("app.services.quality_evaluator._client")
    async def test_high_quality_passes(self, mock_client, sample_script):
        mock_client.chat.completions.create = AsyncMock(return_value=_make_llm_response(0.85))
        result, in_tok, out_tok = await evaluate_video_quality(sample_script)

        assert result.grade == "excellent"
        assert result.overall_score == 0.85
        assert len(result.dimensions) == 5
        assert in_tok == 350
        assert out_tok == 160

    @patch("app.services.quality_evaluator._client")
    async def test_fair_quality_scored(self, mock_client, sample_script):
        mock_client.chat.completions.create = AsyncMock(return_value=_make_llm_response(0.45))
        result, _, _ = await evaluate_video_quality(sample_script)

        assert result.grade == "fair"
        assert result.overall_score == 0.45

    @patch("app.services.quality_evaluator._client")
    async def test_poor_quality_scored(self, mock_client, sample_script):
        mock_client.chat.completions.create = AsyncMock(return_value=_make_llm_response(0.2))
        result, _, _ = await evaluate_video_quality(sample_script)

        assert result.grade == "poor"
        assert result.overall_score == 0.2

    @patch("app.services.quality_evaluator._client")
    async def test_token_and_cost_tracking(self, mock_client, sample_script):
        mock_client.chat.completions.create = AsyncMock(return_value=_make_llm_response(0.7))
        result, in_tok, out_tok = await evaluate_video_quality(sample_script)

        assert result.eval_tokens_in == 350
        assert result.eval_tokens_out == 160
        assert result.eval_cost_usd > 0
        assert in_tok == 350
        assert out_tok == 160

    @patch("app.services.quality_evaluator._client")
    async def test_malformed_response_defaults_fair(self, mock_client, sample_script):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "not valid json"
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50

        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        result, _, _ = await evaluate_video_quality(sample_script)

        assert result.grade == "fair"
        assert result.overall_score == 0.5

    @patch("app.services.quality_evaluator._client")
    async def test_dimensions_properly_scored(self, mock_client, sample_script):
        dimensions = [
            {"name": "prompt_clarity", "score": 0.9, "explanation": "Clear"},
            {"name": "brand_alignment", "score": 0.7, "explanation": "Aligned"},
            {"name": "creative_quality", "score": 0.8, "explanation": "Creative"},
            {"name": "technical_precision", "score": 0.6, "explanation": "OK"},
            {"name": "platform_fit", "score": 0.85, "explanation": "Good fit"},
        ]
        mock_client.chat.completions.create = AsyncMock(
            return_value=_make_llm_response(0.77, dimensions=dimensions)
        )
        result, _, _ = await evaluate_video_quality(sample_script)

        assert len(result.dimensions) == 5
        by_name = {d.name: d for d in result.dimensions}
        assert by_name["prompt_clarity"].score == 0.9
        assert by_name["technical_precision"].score == 0.6

    @patch("app.services.quality_evaluator._client")
    async def test_suggestions_returned(self, mock_client, sample_script):
        suggestions = ["Add more brand-specific details", "Improve camera direction"]
        mock_client.chat.completions.create = AsyncMock(
            return_value=_make_llm_response(0.65, suggestions=suggestions)
        )
        result, _, _ = await evaluate_video_quality(sample_script)

        assert len(result.suggestions) == 2
        assert "brand-specific" in result.suggestions[0]

    @patch("app.services.quality_evaluator._client")
    async def test_platforms_included(self, mock_client, sample_script):
        mock_client.chat.completions.create = AsyncMock(return_value=_make_llm_response(0.75))
        result, _, _ = await evaluate_video_quality(
            sample_script, brief="Summer campaign", platforms=["tiktok", "instagram"]
        )

        assert result.grade == "good"
        call_args = mock_client.chat.completions.create.call_args
        user_content = call_args.kwargs["messages"][1]["content"]
        assert "tiktok" in user_content
        assert "instagram" in user_content


# ── Pipeline Integration ─────────────────────────────────────────────────────


class TestPipelineQualityIntegration:
    @pytest.fixture
    def mock_script_writer(self, sample_ad_script):
        with patch("app.services.pipeline.script_writer") as mock:
            mock.generate_script = AsyncMock(
                return_value=(sample_ad_script, 500, 200),
            )
            yield mock

    @pytest.fixture
    def mock_video_gen(self):
        with patch("app.services.pipeline.video_gen") as mock:
            mock.create_video_task = AsyncMock(return_value="task-qual-123")
            mock.RATIO_MAP = {"tiktok": "9:16", "instagram": "1:1", "youtube": "16:9"}
            yield mock

    @pytest.fixture
    def mock_monitoring(self):
        with patch("app.services.pipeline.monitoring") as mock:
            yield mock

    @pytest.fixture
    def mock_safety_safe(self):
        from app.models.safety_schemas import SafetyEvalResult

        safe_result = SafetyEvalResult(
            overall_score=0.05,
            risk_level="safe",
            categories=[],
            flagged_issues=[],
            recommendation="proceed",
            eval_tokens_in=300,
            eval_tokens_out=150,
            eval_cost_usd=0.000375,
        )
        with patch("app.services.pipeline.safety_evaluator") as mock:
            mock.evaluate_content_safety = AsyncMock(
                return_value=(safe_result, 300, 150),
            )
            yield mock

    @pytest.fixture
    def mock_quality_good(self):
        good_result = QualityEvalResult(
            overall_score=0.78,
            grade="good",
            dimensions=[],
            suggestions=[],
            eval_tokens_in=350,
            eval_tokens_out=160,
            eval_cost_usd=0.000408,
        )
        with patch("app.services.pipeline.quality_evaluator") as mock:
            mock.evaluate_video_quality = AsyncMock(
                return_value=(good_result, 350, 160),
            )
            yield mock

    async def test_quality_included_in_result(
        self,
        mock_script_writer,
        mock_video_gen,
        mock_monitoring,
        mock_safety_safe,
        mock_quality_good,
    ):
        from app.services.pipeline import run_pipeline

        result = await run_pipeline(
            brief="test brief",
            sku_tier=SKUTier.catalog,
            sku_id="SKU-001",
        )
        assert "quality" in result
        assert result["quality"].grade == "good"
        mock_quality_good.evaluate_video_quality.assert_called_once()

    async def test_disabled_quality_skips_assessment(
        self,
        mock_script_writer,
        mock_video_gen,
        mock_monitoring,
        mock_safety_safe,
        mock_quality_good,
    ):
        from app.services.pipeline import run_pipeline

        with patch("app.services.pipeline.settings") as mock_settings:
            mock_settings.safety_enabled = True
            mock_settings.quality_eval_enabled = False
            result = await run_pipeline(
                brief="test brief",
                sku_tier=SKUTier.catalog,
                sku_id="SKU-002",
            )
        assert result["quality"] is None
        mock_quality_good.evaluate_video_quality.assert_not_called()

    async def test_quality_cost_included(
        self,
        mock_script_writer,
        mock_video_gen,
        mock_monitoring,
        mock_safety_safe,
        mock_quality_good,
    ):
        from app.services.pipeline import run_pipeline

        result = await run_pipeline(
            brief="test brief",
            sku_tier=SKUTier.catalog,
            sku_id="SKU-003",
        )
        assert result["cost"].quality_eval_cost_usd > 0
