import argparse

import boto3
import botocore
from rich.console import Console

from config import BLACKLIST_ACCOUNTS, WHITELIST_ACCOUNTS
from config.cli_args import parse_args
from lib.utils import get_enabled_regions
from registry import load_resources, query_registry, terminate_registry
from view.output_handlers import JSONOutputHandler, OutputHandler, RichOutputHandler

# Script to wipe AWS account - IMPORTANT, this script is _BRUTAL_ - use at your own risk

# TODO:
# - Ensure that when an EC2 Instance is removed that it removes the volumes
# - Do we need to batch up the terminate_instance API calls ??
# - Remove snapshots after an AMI is removed
# - FIXME: DocDB, RDS and Neptune ALL returning ALL resources


def validate_regions(requested_regions: list, enabled_regions: list) -> list:
    return [region for region in requested_regions if region in enabled_regions]


def exclude_regions(regions: list, excluded_regions: list) -> list:
    return [region for region in regions if region not in excluded_regions]


def check_account_compliance(
    account_id: str, whitelisted_accounts: list, blacklisted_accounts: list
) -> None:
    if account_id in blacklisted_accounts:
        raise SystemError('Cannot Operate On A Blacklisted Account')

    if not whitelisted_accounts:
        return

    if account_id not in whitelisted_accounts:
        raise SystemError('Can Only Operate On A Whitelisted Account')


def get_resource_regions(
    session, requested_regions: list, excluded_regions: list
) -> list:
    enabled_regions = get_enabled_regions(session) + ['global']
    regions = (
        validate_regions(requested_regions, enabled_regions)
        if requested_regions
        else enabled_regions
    )
    regions = (
        exclude_regions(regions, excluded_regions) if excluded_regions else regions
    )

    return regions


def get_actionable_resource_types(
    registry_services: list,
    include_service: list,
    include_resource: list,
    exclude_service: list,
    exclude_resource: list,
) -> list:
    lower_registry_resource_types = {svc.lower() for svc in registry_services}
    lower_registry_services = {
        svc.split(':')[0] for svc in lower_registry_resource_types
    }
    lower_include_service = {svc.lower() for svc in include_service}
    lower_exclude_service = {svc.lower() for svc in exclude_service}
    lower_include_resource = {svc.lower() for svc in include_resource}
    lower_exclude_resource = {svc.lower() for svc in exclude_resource}

    # Check requested service(s) exist, otherwise raise a warning
    for service in lower_include_service | lower_exclude_service:
        if service not in lower_registry_services:
            print(f'WARNING: Unsupported Service: {service}')

    # Check requested resource(s) exist, otherwise raise a warning
    for resource in lower_include_resource | lower_exclude_resource:
        if resource not in lower_registry_resource_types:
            print(f'WARNING: Unsupported Resource: {resource}')

    return [
        resource_type
        for resource_type in registry_services
        if (
            (
                not include_service
                or resource_type.split(':')[0].lower() in lower_include_service
            )
            and (
                not include_resource or resource_type.lower() in lower_include_resource
            )
            and (
                not exclude_service
                or resource_type.split(':')[0].lower() not in lower_exclude_service
            )
            and (
                not exclude_resource
                or resource_type.lower() not in lower_exclude_resource
            )
        )
    ]


def main(args: argparse.Namespace) -> None:
    # Setup Rich Console
    console = Console(
        log_path=False, log_time=False, color_system='truecolor', highlight=False
    )

    # Load Resources from the Registry
    load_resources()

    # Listing Resource Types
    if args.list_resource_types:
        console.print('# [yellow] Found AWS Resources\n')
        for service in sorted(query_registry.keys()):
            console.print('[grey35]•[/grey35]', f'{service}')
        return

    session_args = {'profile_name': args.profile} if args.profile else {}

    # Establish a boto3 session
    try:
        session = boto3.session.Session(**session_args)  # type: ignore
    except botocore.exceptions.ProfileNotFound as e:  # type: ignore
        raise SystemError(f'Profile "{args.profile}" Not Found.') from e

    # Check that we're allowed to operate in this account.
    account_id = session.client('sts').get_caller_identity()['Account']
    check_account_compliance(account_id, WHITELIST_ACCOUNTS, BLACKLIST_ACCOUNTS)

    # Clear the screen - TODO: Should we make this optional?
    if args.output != 'json':
        console.clear()

    regions = get_resource_regions(session, args.region, args.exclude_region)
    resource_types = get_actionable_resource_types(
        list(query_registry.keys()),
        args.service,
        args.resource,
        args.exclude_service,
        args.exclude_resource,
    )

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

    handler.retrieve_data(resource_types, regions)


# This will only ever trigger if the script is executed directly
if __name__ == '__main__':
    args = parse_args()
    main(args)
