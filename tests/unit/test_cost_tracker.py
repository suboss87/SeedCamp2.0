"""Tests for token-aware cost tracking (Pattern 3).

Verifies: cost calculation formula, tier tracking, history aggregation, summary stats.
All pure functions -- no mocks needed.
"""

import pytest

from app.config import settings
from app.models.schemas import SKUTier
from app.services import cost_tracker


class TestCalculateCost:
    """Verify cost calculation matches the token pricing formula."""

    def test_hero_cost_uses_pro_rate(self):
        cost = cost_tracker.calculate_cost(
            script_input_tokens=500,
            script_output_tokens=200,
            video_tokens=400_000,
            model_used="seedance-pro",
            cost_per_m=settings.cost_per_m_seedance_pro,
            sku_tier=SKUTier.hero,
        )
        expected_video = (400_000 / 1_000_000) * settings.cost_per_m_seedance_pro
        assert cost.video_cost_usd == pytest.approx(expected_video, abs=1e-5)

    def test_catalog_cost_uses_fast_rate(self):
        cost = cost_tracker.calculate_cost(
            script_input_tokens=500,
            script_output_tokens=200,
            video_tokens=400_000,
            model_used="seedance-fast",
            cost_per_m=settings.cost_per_m_seedance_fast,
            sku_tier=SKUTier.catalog,
        )
        expected_video = (400_000 / 1_000_000) * settings.cost_per_m_seedance_fast
        assert cost.video_cost_usd == pytest.approx(expected_video, abs=1e-5)

    def test_hero_costs_more_than_catalog(self):
        hero = cost_tracker.calculate_cost(
            script_input_tokens=500,
            script_output_tokens=200,
            video_tokens=400_000,
            model_used="pro",
            cost_per_m=settings.cost_per_m_seedance_pro,
            sku_tier=SKUTier.hero,
        )
        catalog = cost_tracker.calculate_cost(
            script_input_tokens=500,
            script_output_tokens=200,
            video_tokens=400_000,
            model_used="fast",
            cost_per_m=settings.cost_per_m_seedance_fast,
            sku_tier=SKUTier.catalog,
        )
        assert hero.total_cost_usd > catalog.total_cost_usd

    def test_zero_tokens_zero_cost(self):
        cost = cost_tracker.calculate_cost(
            script_input_tokens=0,
            script_output_tokens=0,
            video_tokens=0,
            model_used="any",
            cost_per_m=1.20,
            sku_tier=SKUTier.catalog,
        )
        assert cost.total_cost_usd == 0.0
        assert cost.script_cost_usd == 0.0
        assert cost.video_cost_usd == 0.0

    def test_script_cost_formula(self):
        cost = cost_tracker.calculate_cost(
            script_input_tokens=1_000_000,
            script_output_tokens=1_000_000,
            video_tokens=0,
            model_used="any",
            cost_per_m=0.70,
            sku_tier=SKUTier.catalog,
        )
        expected = settings.cost_per_m_seed18_input + settings.cost_per_m_seed18_output
        assert cost.script_cost_usd == pytest.approx(expected, abs=1e-5)

    def test_total_is_script_plus_video(self):
        cost = cost_tracker.calculate_cost(
            script_input_tokens=500,
            script_output_tokens=200,
            video_tokens=400_000,
            model_used="pro",
            cost_per_m=1.20,
            sku_tier=SKUTier.hero,
        )
        assert cost.total_cost_usd == pytest.approx(
            cost.script_cost_usd + cost.video_cost_usd,
            abs=1e-5,
        )

    def test_token_scaling_is_linear(self):
        cost_1x = cost_tracker.calculate_cost(
            script_input_tokens=0,
            script_output_tokens=0,
            video_tokens=100_000,
            model_used="m",
            cost_per_m=1.0,
            sku_tier=SKUTier.catalog,
        )
        cost_tracker._history.clear()
        cost_2x = cost_tracker.calculate_cost(
            script_input_tokens=0,
            script_output_tokens=0,
            video_tokens=200_000,
            model_used="m",
            cost_per_m=1.0,
            sku_tier=SKUTier.catalog,
        )
        assert cost_2x.video_cost_usd == pytest.approx(2 * cost_1x.video_cost_usd, abs=1e-6)


class TestGetSummary:
    """Verify summary aggregation across multiple calculations."""

    def test_empty_history_returns_defaults(self):
        summary = cost_tracker.get_summary()
        assert summary.total_videos == 0
        assert summary.total_cost_usd == 0.0

    def test_summary_tracks_hero_and_catalog(self):
        cost_tracker.calculate_cost(
            100,
            50,
            200_000,
            "pro",
            1.20,
            SKUTier.hero,
        )
        cost_tracker.calculate_cost(
            100,
            50,
            200_000,
            "fast",
            0.70,
            SKUTier.catalog,
        )
        summary = cost_tracker.get_summary()
        assert summary.total_videos == 2
        assert summary.hero_videos == 1
        assert summary.catalog_videos == 1
        assert summary.hero_cost_usd > summary.catalog_cost_usd

    def test_avg_cost_per_video(self):
        for _ in range(4):
            cost_tracker.calculate_cost(
                100,
                50,
                200_000,
                "fast",
                0.70,
                SKUTier.catalog,
            )
        summary = cost_tracker.get_summary()
        assert summary.avg_cost_per_video == pytest.approx(
            summary.total_cost_usd / 4,
            abs=1e-4,
        )
