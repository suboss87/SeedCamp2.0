"""Tests for the Smart Model Router (Step 3 of the pipeline)."""

import pytest

from app.models.schemas import SKUTier
from app.services.model_router import route


class TestModelRouter:
    """Verify tier-based routing returns correct model IDs and costs."""

    def test_hero_routes_to_pro(self):
        model_id, cost = route(SKUTier.hero)
        # Seedance 2.0: dreamina-seedance-2-0-260128 (standard, no "fast" suffix)
        assert "fast" not in model_id.lower()
        assert "seedance" in model_id.lower() or "dreamina" in model_id.lower()

    def test_catalog_routes_to_fast(self):
        model_id, cost = route(SKUTier.catalog)
        assert "fast" in model_id.lower()

    def test_hero_costs_more_than_catalog(self):
        _, hero_cost = route(SKUTier.hero)
        _, catalog_cost = route(SKUTier.catalog)
        assert hero_cost > catalog_cost

    def test_route_returns_tuple(self):
        result = route(SKUTier.catalog)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], str)
        assert isinstance(result[1], float)

    def test_invalid_tier_raises(self):
        with pytest.raises(KeyError):
            route("nonexistent")
