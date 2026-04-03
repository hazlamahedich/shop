from __future__ import annotations

import pytest

from app.services.personality.personality_tracker import get_personality_tracker


@pytest.fixture(autouse=True)
def _reset_tracker():
    get_personality_tracker().reset()
    yield
    get_personality_tracker().reset()
