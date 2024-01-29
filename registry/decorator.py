from typing import Callable

from registry import query_registry, terminate_registry


def register_query_function(resource_type: str) -> Callable:
    def decorator(deletion_function: Callable[..., None]) -> Callable[..., None]:
        query_registry[resource_type] = deletion_function
        return deletion_function

    return decorator


def register_terminate_function(resource_type: str) -> Callable:
    def decorator(deletion_function: Callable[..., None]) -> Callable[..., None]:
        terminate_registry[resource_type] = deletion_function
        return deletion_function

    return decorator
