"""Public API; providers are loaded only when requested."""

from importlib import import_module

__all__ = ["Agent", "OpenDeepProvider", "ToolRegistry"]

_EXPORTS = {
    "Agent": ".agent.loop",
    "OpenDeepProvider": ".core.opendeep_provider",
    "ToolRegistry": ".tools.registry",
}


def __getattr__(name):
    if name not in _EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(_EXPORTS[name], __name__), name)
    globals()[name] = value
    return value
