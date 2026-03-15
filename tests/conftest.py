"""Shared fixtures for SeedCamp tests."""

import pytest

from app.models.schemas import AdScript
from app.services import cost_tracker


@pytest.fixture
def sample_ad_script():
    """A realistic AdScript for pipeline tests."""
    return AdScript(
        ad_copy="Summer vibes, unstoppable energy",
        scene_description="Urban runner at golden hour, dynamic street shots",
        video_prompt="A runner sprinting through city streets at golden hour, cinematic slow motion",
        camera_direction="tracking shot following the runner, low angle",
    )


@pytest.fixture(autouse=True)
def clear_cost_history():
    """Reset cost_tracker in-memory history between tests."""
    cost_tracker._history.clear()
    yield
    cost_tracker._history.clear()
