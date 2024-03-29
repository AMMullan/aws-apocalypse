import json
from pathlib import Path

from . import config


def parse_config_file(config_file: Path) -> None:
    json_config = json.loads(config_file.read_text())

    if config_command := json_config.get('command'):
        if config_command in ['rich', 'json']:
            config.COMMAND = config_command
        else:
            config.COMMAND = 'json'

    for account_id in json_config.get('blacklisted_accounts', []):
        config.add_blacklisted_account(account_id)

    for account_id in json_config.get('whitelisted_accounts'):
        config.add_whitelisted_account(account_id)

    if json_config.get('allow_exceptions', False):
        config.ALLOW_EXCEPTIONS = True

    for exception in json_config.get('custom_exception_tags'):
        config.add_custom_exception_tag(exception)

    for region in json_config.get('regions', []):
        config.add_region(region)

    for region in json_config.get('exclude_regions', []):
        config.remove_region(region)

    for service in json_config.get('resource_types', []):
        config.add_included_resource(service)

    for service in json_config.get('services', []):
        config.add_included_service(service)

    for service in json_config.get('exclude_resource_types', []):
        config.add_excluded_resource(service)

    for service in json_config.get('exclude_services', []):
        config.add_excluded_service(service)
