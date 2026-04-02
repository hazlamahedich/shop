"""Handler-level transition phrase tests.

Story 11-4: Split from test_handler_transitions.py into per-handler files.
This conftest provides the shared autouse reset fixture.
"""

import pytest

from app.services.personality.transition_selector import get_transition_selector


@pytest.fixture(autouse=True)
def reset_selector():
    selector = get_transition_selector()
    selector.reset()
    yield
    selector.reset()
