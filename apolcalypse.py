import argparse

import boto3
import botocore

from config import BLACKLIST_ACCOUNTS, GLOBAL_RESOURCES, WHITELIST_ACCOUNTS
from config.cli_args import parse_args
from lib.utils import get_enabled_regions
from registry import load_resources, registry

# Script to wipe AWS account - IMPORTANT, this script is _BRUTAL_ - use at your own risk


def validate_regions(requested_regions, enabled_regions):
    return [region for region in requested_regions if region in enabled_regions]


def exclude_regions(regions, excluded_regions):
    return [region for region in regions if region not in excluded_regions]


def main(args: argparse.Namespace) -> None:
    session_args = {}

    # Load Resources from the Registry
    load_resources()

    # Listing Resource Types
    if args.list_resource_types:
        for service in sorted(registry.keys()):
            print(f'• {service}')
        raise SystemExit

    session_args = {'profile_name': args.profile} if args.profile else {}

    try:
        session = boto3.session.Session(**session_args)
    except botocore.exceptions.ProfileNotFound as e:
        raise SystemError(f'Profile "{args.profile}" Not Found.') from e

    enabled_regions = get_enabled_regions(session)
    enabled_regions.append('global')
    regions = (
        validate_regions(args.region, enabled_regions)
        if args.region
        else enabled_regions
    )
    regions = (
        exclude_regions(regions, args.exclude_region)
        if args.exclude_region
        else regions
    )

    account_id = session.client('sts').get_caller_identity()['Account']

    if account_id in BLACKLIST_ACCOUNTS:
        raise SystemError('Cannot Operate On A Blacklisted Account')

    if WHITELIST_ACCOUNTS and account_id not in WHITELIST_ACCOUNTS:
        raise SystemError('Can Only Operate On A Whitelisted Account')

    for resource_type, delete_function in registry.items():
        service = resource_type.split(':')[0].lower()
        if args.service and service not in [svc.lower() for svc in args.service]:
            continue
        if args.resource and resource_type not in args.resource:
            continue
        if args.exclude_service and service in [
            svc.lower() for svc in args.exclude_service
        ]:
            continue
        if args.exclude_resource and resource_type in args.exclude_resource:
            continue

        for region in regions:
            if region == 'global' and resource_type not in GLOBAL_RESOURCES:
                continue

            results = delete_function(session, region)
            print(resource_type, results)


# This will only ever trigger if the script is executed directly
if __name__ == '__main__':
    args = parse_args()
    main(args)
