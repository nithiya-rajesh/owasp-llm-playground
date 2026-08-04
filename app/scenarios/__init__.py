import importlib
import pkgutil
import os

_REGISTRY = {}


def _discover():
    if _REGISTRY:
        return _REGISTRY
    pkg_dir = os.path.dirname(__file__)
    for _, name, is_pkg in pkgutil.iter_modules([pkg_dir]):
        if not is_pkg:
            continue
        try:
            mod = importlib.import_module(f"app.scenarios.{name}.scenario")
        except ModuleNotFoundError:
            continue
        scenario = getattr(mod, "SCENARIO", None)
        if scenario is not None:
            _REGISTRY[scenario.id] = scenario
    return _REGISTRY


def all_scenarios():
    return sorted(_discover().values(), key=lambda s: s.owasp_id)


def get_scenario(scenario_id: str):
    return _discover().get(scenario_id)
