"""Tests for the Responsible AI content safety evaluator.

All tests mock the OpenAI client -- no real API calls.
Verifies: risk classification, token/cost tracking, pipeline integration,
disabled-safety bypass, and category scoring.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.safety_schemas import SafetyEvalResult
from app.models.schemas import AdScript, SKUTier
from app.services.pipeline import ContentBlockedError, run_pipeline
from app.services.safety_evaluator import (
    _calculate_eval_cost,
    _classify_risk,
    evaluate_content_safety,
)

# ── Fixtures ─────────────────────────────────────────────────────────────────


def _make_llm_response(overall_score: float, categories=None, flagged=None):
    """Build a mock OpenAI chat completion response for safety eval."""
    if categories is None:
        categories = [
            {"name": "bias", "score": 0.0, "explanation": "No bias detected"},
            {"name": "stereotypes", "score": 0.0, "explanation": "No stereotypes"},
            {"name": "violence", "score": 0.0, "explanation": "No violence"},
            {"name": "sexual_content", "score": 0.0, "explanation": "No sexual content"},
            {"name": "hate_speech", "score": 0.0, "explanation": "No hate speech"},
            {"name": "cultural_insensitivity", "score": 0.0, "explanation": "No issues"},
            {"name": "brand_safety", "score": 0.0, "explanation": "Brand safe"},
        ]

    data = {
        "overall_score": overall_score,
        "categories": categories,
        "flagged_issues": flagged or [],
        "recommendation": (
            "proceed" if overall_score < 0.3 else "review" if overall_score < 0.8 else "block"
        ),
    }

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps(data)
    mock_response.usage = MagicMock()
    mock_response.usage.prompt_tokens = 300
    mock_response.usage.completion_tokens = 150
    return mock_response


# ── Risk Classification ──────────────────────────────────────────────────────


class TestClassifyRisk:
    def test_safe(self):
        assert _classify_risk(0.0) == "safe"
        assert _classify_risk(0.29) == "safe"

    def test_low_risk(self):
        assert _classify_risk(0.3) == "low_risk"
        assert _classify_risk(0.5) == "low_risk"

    def test_high_risk(self):
        assert _classify_risk(0.6) == "high_risk"
        assert _classify_risk(0.79) == "high_risk"

    def test_blocked(self):
        assert _classify_risk(0.8) == "blocked"
        assert _classify_risk(1.0) == "blocked"


# ── Cost Calculation ─────────────────────────────────────────────────────────


class TestCalculateEvalCost:
    def test_zero_tokens(self):
        assert _calculate_eval_cost(0, 0) == 0.0

    def test_known_tokens(self):
        # 1M input tokens at $0.25 + 1M output tokens at $2.00 = $2.25
        cost = _calculate_eval_cost(1_000_000, 1_000_000)
        assert cost == 2.25

    def test_small_tokens(self):
        # 300 input + 150 output
        cost = _calculate_eval_cost(300, 150)
        assert cost > 0
        assert cost < 0.001  # Very small cost


# ── Safety Evaluator ─────────────────────────────────────────────────────────


class TestEvaluateContentSafety:
    @pytest.fixture
    def safe_script(self):
        return AdScript(
            ad_copy="Summer vibes, run free",
            scene_description="Runner at golden hour on clean urban streets",
            video_prompt="A runner sprinting through city streets at golden hour",
            camera_direction="tracking shot, low angle",
        )

    @patch("app.services.safety_evaluator._client")
    async def test_safe_content_passes(self, mock_client, safe_script):
        mock_client.chat.completions.create = AsyncMock(return_value=_make_llm_response(0.05))
        result, in_tok, out_tok = await evaluate_content_safety(safe_script)

        assert result.risk_level == "safe"
        assert result.overall_score == 0.05
        assert len(result.categories) == 7
        assert len(result.flagged_issues) == 0
        assert in_tok == 300
        assert out_tok == 150

    @patch("app.services.safety_evaluator._client")
    async def test_harmful_content_flagged(self, mock_client, safe_script):
        categories = [
            {"name": "bias", "score": 0.1, "explanation": "Minor bias"},
            {"name": "stereotypes", "score": 0.7, "explanation": "Gender stereotypes present"},
            {"name": "violence", "score": 0.0, "explanation": "None"},
            {"name": "sexual_content", "score": 0.0, "explanation": "None"},
            {"name": "hate_speech", "score": 0.0, "explanation": "None"},
            {"name": "cultural_insensitivity", "score": 0.2, "explanation": "Minor"},
            {"name": "brand_safety", "score": 0.1, "explanation": "OK"},
        ]
        mock_client.chat.completions.create = AsyncMock(
            return_value=_make_llm_response(
                0.7,
                categories=categories,
                flagged=["Gender stereotypes in scene description"],
            )
        )
        result, _, _ = await evaluate_content_safety(safe_script)

        assert result.risk_level == "high_risk"
        assert result.overall_score == 0.7
        assert len(result.flagged_issues) == 1

    @patch("app.services.safety_evaluator._client")
    async def test_blocked_content_high_score(self, mock_client, safe_script):
        mock_client.chat.completions.create = AsyncMock(
            return_value=_make_llm_response(
                0.95,
                flagged=["Explicit violence", "Hate speech detected"],
            )
        )
        result, _, _ = await evaluate_content_safety(safe_script)

        assert result.risk_level == "blocked"
        assert result.overall_score == 0.95

    @patch("app.services.safety_evaluator._client")
    async def test_token_and_cost_tracking(self, mock_client, safe_script):
        mock_client.chat.completions.create = AsyncMock(return_value=_make_llm_response(0.0))
        result, in_tok, out_tok = await evaluate_content_safety(safe_script)

        assert result.eval_tokens_in == 300
        assert result.eval_tokens_out == 150
        assert result.eval_cost_usd > 0
        assert in_tok == 300
        assert out_tok == 150

    @patch("app.services.safety_evaluator._client")
    async def test_malformed_response_defaults_safe(self, mock_client, safe_script):
        """If LLM returns unparseable JSON, default to safe."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "not valid json"
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50

        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        result, _, _ = await evaluate_content_safety(safe_script)

        assert result.risk_level == "safe"
        assert result.overall_score == 0.0

    @patch("app.services.safety_evaluator._client")
    async def test_categories_properly_scored(self, mock_client, safe_script):
        categories = [
            {"name": "bias", "score": 0.1, "explanation": "Slight bias"},
            {"name": "stereotypes", "score": 0.4, "explanation": "Some stereotypes"},
            {"name": "violence", "score": 0.0, "explanation": "None"},
            {"name": "sexual_content", "score": 0.0, "explanation": "None"},
            {"name": "hate_speech", "score": 0.0, "explanation": "None"},
            {"name": "cultural_insensitivity", "score": 0.0, "explanation": "None"},
            {"name": "brand_safety", "score": 0.2, "explanation": "Minor concern"},
        ]
        mock_client.chat.completions.create = AsyncMock(
            return_value=_make_llm_response(0.4, categories=categories)
        )
        result, _, _ = await evaluate_content_safety(safe_script)

        assert len(result.categories) == 7
        by_name = {c.name: c for c in result.categories}
        assert by_name["stereotypes"].score == 0.4
        assert by_name["violence"].score == 0.0


# ── Pipeline Integration ─────────────────────────────────────────────────────


class TestPipelineSafetyIntegration:
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
            mock.create_video_task = AsyncMock(return_value="task-safe-123")
            mock.RATIO_MAP = {"tiktok": "9:16", "instagram": "1:1", "youtube": "16:9"}
            yield mock

    @pytest.fixture
    def mock_monitoring(self):
        with patch("app.services.pipeline.monitoring") as mock:
            yield mock

    @pytest.fixture
    def mock_safety_safe(self):
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
    def mock_safety_blocked(self):
        blocked_result = SafetyEvalResult(
            overall_score=0.95,
            risk_level="blocked",
            categories=[],
            flagged_issues=["Violent content"],
            recommendation="block",
            eval_tokens_in=300,
            eval_tokens_out=150,
            eval_cost_usd=0.000375,
        )
        with patch("app.services.pipeline.safety_evaluator") as mock:
            mock.evaluate_content_safety = AsyncMock(
                return_value=(blocked_result, 300, 150),
            )
            yield mock

    async def test_safe_content_proceeds(
        self,
        mock_script_writer,
        mock_video_gen,
        mock_monitoring,
        mock_safety_safe,
    ):
        result = await run_pipeline(
            brief="safe brief",
            sku_tier=SKUTier.catalog,
            sku_id="SKU-001",
        )
        assert "safety" in result
        assert result["safety"].risk_level == "safe"
        mock_video_gen.create_video_task.assert_called_once()

    async def test_blocked_content_raises_error(
        self,
        mock_script_writer,
        mock_video_gen,
        mock_monitoring,
        mock_safety_blocked,
    ):
        with pytest.raises(ContentBlockedError) as exc_info:
            await run_pipeline(
                brief="dangerous brief",
                sku_tier=SKUTier.catalog,
                sku_id="SKU-002",
            )
        assert exc_info.value.safety_result.risk_level == "blocked"
        mock_video_gen.create_video_task.assert_not_called()

    async def test_disabled_safety_skips_eval(
        self,
        mock_script_writer,
        mock_video_gen,
        mock_monitoring,
        mock_safety_safe,
    ):
        with patch("app.services.pipeline.settings") as mock_settings:
            mock_settings.safety_enabled = False
            result = await run_pipeline(
                brief="any brief",
                sku_tier=SKUTier.catalog,
                sku_id="SKU-003",
            )
        assert result["safety"] is None
        mock_safety_safe.evaluate_content_safety.assert_not_called()

    async def test_safety_cost_included(
        self,
        mock_script_writer,
        mock_video_gen,
        mock_monitoring,
        mock_safety_safe,
    ):
        result = await run_pipeline(
            brief="safe brief",
            sku_tier=SKUTier.catalog,
            sku_id="SKU-004",
        )
        assert result["cost"].safety_eval_cost_usd > 0
