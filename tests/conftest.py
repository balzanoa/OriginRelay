import pytest

from origin_relay.models import Role
from origin_relay.orchestrator import Orchestrator


def _pass(_subtask):
    return True


@pytest.fixture
def gate():
    """Orquestador con runners que pasan, para probar el grafo sin ejecutar herramientas."""

    def build(runners=None, **kwargs):
        merged = {role: _pass for role in Role}
        if runners:
            merged.update(runners)
        return Orchestrator(runners=merged, **kwargs)

    return build
