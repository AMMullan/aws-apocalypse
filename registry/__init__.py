import os.path
from importlib import import_module
from pathlib import Path
from typing import Callable

registry: dict[str, Callable[..., None]] = {}


def load_resources():
    """Automatically detects all solutions in the project"""
    services = sorted(Path('services/').rglob("*.py"))

    for svc in services:
        import_module(f"services.{os.path.splitext(svc.name)[0]}")
