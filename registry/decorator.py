from typing import Callable

from registry import registry


def register_resource(resource_type: str) -> Callable:
    def decorator(deletion_function: Callable[..., None]) -> Callable[..., None]:
        registry[resource_type] = deletion_function
        return deletion_function

    return decorator
