from typing import Callable

from registry import query_registry, terminate_registry


def register_query_function(resource_type: str) -> Callable:
    def decorator(func: Callable[..., None]) -> Callable[..., None]:
        query_registry[resource_type] = func
        return func

    return decorator


def register_terminate_function(resource_type: str) -> Callable:
    def decorator(func: Callable[..., None]) -> Callable[..., None]:
        terminate_registry[resource_type] = func
        return func

    return decorator
