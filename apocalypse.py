import argparse

# Script to wipe AWS account - IMPORTANT, this script is _BRUTAL_ - use at your own risk
# TODO:
# - Do we need to batch up the terminate_instance API calls ??
# - Remove snapshots after an AMI is removed
# - At the moment, we merge the services/resource types from CLI/Config - should that change?
import signal
import sys

import boto3
import botocore
from rich.console import Console

from config import config
from config.cli_args import parse_args
from config.config_file import parse_config_file
from lib.utils import get_enabled_regions
from registry import load_resources, query_registry, terminate_registry
from view.output_handlers import JSONOutputHandler, OutputHandler, RichOutputHandler


# Define the signal handler
def signal_handler(sig, frame):
    print('\nCtrl+C pressed. Exiting gracefully...')
    # Perform any necessary cleanup here
    sys.exit(0)


# Set the signal handler for SIGINT
signal.signal(signal.SIGINT, signal_handler)


def confirm_deletion():
    while True:
        response = input("Are you sure you want to delete? (yes/no): ").strip().lower()
        if response == "yes":
            return True
        elif response == "no":
            return False
        else:
            print("Invalid input. Please type 'yes' or 'no'.")


def validate_regions(
    requested_regions: list[str] | set[str], enabled_regions: list[str]
) -> list[str]:
    return [region for region in requested_regions if region in enabled_regions]


def exclude_regions(
    regions: list[str], excluded_regions: list[str] | set[str]
) -> list[str]:
    return [region for region in regions if region not in excluded_regions]


def check_account_compliance(session) -> None:
    account_id = session.client('sts').get_caller_identity()['Account']

    if account_id in config.BLACKLIST_ACCOUNTS:
        raise SystemError('Cannot Operate On A Blacklisted Account')

    if not config.WHITELIST_ACCOUNTS:
        return

    if account_id not in config.WHITELIST_ACCOUNTS:
        raise SystemError('Can Only Operate On A Whitelisted Account')


def get_resource_regions(session) -> set[str]:
    enabled_regions = get_enabled_regions(session) + ['global']
    regions = (
        validate_regions(config.REGIONS, enabled_regions)
        if config.REGIONS
        else enabled_regions
    )
    regions = (
        exclude_regions(regions, config.EXCLUDE_REGIONS)
        if config.EXCLUDE_REGIONS
        else regions
    )

    return set(regions)


def get_actionable_resource_types(registry_services: list[str]) -> list[str]:
    def warn_unsupported(
        items: set[str], valid_items: set[str], item_type: str
    ) -> None:
        for item in items:
            if item not in valid_items:
                print(f'WARNING: Unsupported {item_type}: {item}')

    registry_resource_types = {svc.lower() for svc in registry_services}
    include_services = {svc.lower() for svc in config.INCLUDE_SERVICES}
    exclude_services = {svc.lower() for svc in config.EXCLUDE_SERVICES}
    include_resources = {svc.lower() for svc in config.INCLUDE_RESOURCES}
    exclude_resources = {svc.lower() for svc in config.EXCLUDE_RESOURCES}

    warn_unsupported(
        include_services | exclude_services,
        {svc.split(':')[0] for svc in registry_resource_types},
        'Service',
    )
    warn_unsupported(
        include_resources | exclude_resources,
        registry_resource_types,
        'Resource',
    )

    actionable = []
    for resource_type in registry_services:
        resource_service = resource_type.split(':')[0].lower()

        if include_services and resource_service in include_services:
            actionable.append(resource_type)

        if include_resources and resource_type.lower() in include_resources:
            actionable.append(resource_type)

        if resource_service in exclude_services and resource_type in actionable:
            actionable.remove(resource_type)

        if resource_type.lower() in exclude_resources and resource_type in actionable:
            actionable.remove(resource_type)

    return actionable


def main(args: argparse.Namespace) -> None:
    # Setup Rich Console
    console = Console(
        log_path=False, log_time=False, color_system='truecolor', highlight=False
    )

    # Load Resources from the Registry
    load_resources()

    if args.config:
        parse_config_file(args.config)

    # Listing Resource Types
    if args.list_resource_types:
        console.print('# [yellow] Found AWS Resources\n')
        for service in sorted(query_registry.keys()):
            console.print('[grey35]•[/grey35]', f'{service}')
        return

    # Establish a boto3 session
    try:
        session_args = {'profile_name': args.profile} if args.profile else {}
        session = boto3.session.Session(**session_args)  # type: ignore
    except botocore.exceptions.ProfileNotFound as e:  # type: ignore
        raise SystemError(f'Profile "{args.profile}" Not Found.') from e

    # Check that we're allowed to operate in this account.
    check_account_compliance(session)

    # Clear the screen - TODO: Should we make this optional?
    if args.output != 'json':
        console.clear()

    config.REGIONS = get_resource_regions(session)

    resource_types = get_actionable_resource_types(list(query_registry.keys()))
    if not resource_types:
        print("No Valid Resources")
        return

    match args.output:
        case 'json':
            handler: OutputHandler = JSONOutputHandler(session)
        case 'rich':
            handler: OutputHandler = RichOutputHandler(session, console)
        case _:
            raise ValueError('Invalid Output Method')

    retrieved_resources = handler.retrieve_data(resource_types, config.REGIONS)
    if not retrieved_resources or args.command == 'inspect-aws':
        return

    if not confirm_deletion():
        return

    for region, resource_detail in retrieved_resources.items():
        for resource_type, resource_arns in resource_detail.items():
            terminate_registry[resource_type](session, region, resource_arns)


# This will only ever trigger if the script is executed directly
if __name__ == '__main__':
    args = parse_args()

    main(args)  # type: ignore
