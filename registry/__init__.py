import os.path
from collections import defaultdict
from dataclasses import dataclass, field
from importlib import import_module
from pathlib import Path
from typing import Callable

query_registry: dict[str, Callable[..., None]] = {}
terminate_registry: dict[str, Callable[..., None]] = {}


@dataclass
class DeleteResponse:
    successful: list = field(default_factory=list)
    failures: dict[str, list] = field(default_factory=lambda: defaultdict(list))


def init_registry_resources():
    """Automatically detects all solutions in the project"""
    services = sorted(Path('services/').rglob('*.py'))

    for svc in services:
        import_module(f'services.{os.path.splitext(svc.name)[0]}')
