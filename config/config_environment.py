import os

from . import config


def parse_environment_config() -> None:
    if allow_exceptions := os.environ.get('NUKE_ALLOW_EXCEPTIONS'):
        if allow_exceptions in ['true', 'True']:
            config.ALLOW_EXCEPTIONS = True

    if exception_tags := os.environ.get('NUKE_EXCEPTION_TAGS'):
        for tag in exception_tags.split(','):
            config.add_custom_exception_tag(tag)

    if regions := os.environ.get('NUKE_REGIONS'):
        for region in regions.split(','):
            config.add_region(region)

    if regions := os.environ.get('NUKE_EXCLUDE_REGIONS'):
        for region in regions.split(','):
            config.remove_region(region)

    if resource_types := os.environ.get('NUKE_RESOURCE_TYPES'):
        for resource_type in resource_types.split(','):
            config.add_included_resource(resource_type)

    if services := os.environ.get('NUKE_SERVICES'):
        for service in services.split(','):
            config.add_included_service(service)

    if resource_types := os.environ.get('NUKE_EXCLUDE_RESOURCE_TYPES'):
        for resource_type in resource_types.split(','):
            config.add_excluded_resource(resource_type)

    if services := os.environ.get('NUKE_EXCLUDE_SERVICES'):
        for service in services.split(','):
            config.add_excluded_service(service)
