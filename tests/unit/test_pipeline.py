"""Tests for the pipeline orchestration (Patterns 1-3 together).

Verifies: token estimation formula, routing integration, cost recording, end-to-end flow.
Mocks script_writer and video_gen (external API calls) — tests the glue logic.
"""

from unittest.mock import AsyncMock, patch

import pytest

from app.models.safety_schemas import SafetyEvalResult
from app.models.schemas import SKUTier
from app.services import cost_tracker
from app.services.pipeline import _estimate_video_tokens, run_pipeline

# ── Token Estimation ──────────────────────────────────────────────────────────


class TestEstimateVideoTokens:
    """Verify the formula: (W * H * FPS * Duration) / 1024."""

    def test_720p_8s(self):
        tokens = _estimate_video_tokens(duration=8, resolution="720p")
        expected = int((1280 * 720 * 24 * 8) / 1024)
        assert tokens == expected

    def test_1080p_5s(self):
        tokens = _estimate_video_tokens(duration=5, resolution="1080p")
        expected = int((1920 * 1080 * 24 * 5) / 1024)
        assert tokens == expected

    def test_480p(self):
        tokens = _estimate_video_tokens(duration=5, resolution="480p")
        expected = int((854 * 480 * 24 * 5) / 1024)
        assert tokens == expected

    def test_unknown_resolution_falls_back_to_720p(self):
        tokens = _estimate_video_tokens(duration=5, resolution="4k")
        tokens_720p = _estimate_video_tokens(duration=5, resolution="720p")
        assert tokens == tokens_720p


# ── Pipeline Integration ──────────────────────────────────────────────────────


class TestRunPipeline:
    """Verify pipeline orchestrates routing, cost tracking, and returns expected keys."""

    @pytest.fixture
    def mock_script_writer(self, sample_ad_script):
        """Mock script_writer.generate_script to return a fixed AdScript."""
        with patch("app.services.pipeline.script_writer") as mock:
            mock.generate_script = AsyncMock(
                return_value=(sample_ad_script, 500, 200),
            )
            yield mock

    @pytest.fixture
    def mock_video_gen(self):
        """Mock video_gen.create_video_task to return a fixed task ID."""
        with patch("app.services.pipeline.video_gen") as mock:
            mock.create_video_task = AsyncMock(return_value="task-abc-123")
            mock.RATIO_MAP = {"tiktok": "9:16", "instagram": "1:1", "youtube": "16:9"}
            yield mock

    @pytest.fixture
    def mock_monitoring(self):
        """Mock monitoring to avoid side effects."""
        with patch("app.services.pipeline.monitoring") as mock:
            yield mock

    @pytest.fixture
    def mock_safety_evaluator(self):
        """Mock safety_evaluator to return safe result."""
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

    async def test_pipeline_returns_all_required_keys(
        self,
        mock_script_writer,
        mock_video_gen,
        mock_monitoring,
        mock_safety_evaluator,
    ):
        result = await run_pipeline(
            brief="test brief",
            sku_tier=SKUTier.catalog,
            sku_id="SKU-001",
        )
        assert set(result.keys()) == {
            "script",
            "model_id",
            "cost_per_m",
            "task_id",
            "cost",
            "in_tokens",
            "out_tokens",
            "safety",
            "quality",
        }

    async def test_hero_routes_to_pro_model(
        self,
        mock_script_writer,
        mock_video_gen,
        mock_monitoring,
        mock_safety_evaluator,
    ):
        result = await run_pipeline(
            brief="hero brief",
            sku_tier=SKUTier.hero,
            sku_id="HERO-001",
        )
        assert "fast" not in result["model_id"].lower()

    async def test_catalog_routes_to_fast_model(
        self,
        mock_script_writer,
        mock_video_gen,
        mock_monitoring,
        mock_safety_evaluator,
    ):
        result = await run_pipeline(
            brief="catalog brief",
            sku_tier=SKUTier.catalog,
            sku_id="CAT-001",
        )
        assert "fast" in result["model_id"].lower()

    async def test_pipeline_records_to_cost_history(
        self,
        mock_script_writer,
        mock_video_gen,
        mock_monitoring,
        mock_safety_evaluator,
    ):
        await run_pipeline(
            brief="test",
            sku_tier=SKUTier.catalog,
            sku_id="SKU-001",
        )
        assert len(cost_tracker._history) == 1
        assert cost_tracker._history[0]["sku_tier"] == "catalog"

    async def test_hero_costs_more_than_catalog_end_to_end(
        self,
        mock_script_writer,
        mock_video_gen,
        mock_monitoring,
        mock_safety_evaluator,
    ):
        hero = await run_pipeline(
            brief="hero",
            sku_tier=SKUTier.hero,
            sku_id="H-001",
        )
        catalog = await run_pipeline(
            brief="catalog",
            sku_tier=SKUTier.catalog,
            sku_id="C-001",
        )
        assert hero["cost"].total_cost_usd > catalog["cost"].total_cost_usd
