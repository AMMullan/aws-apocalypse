#
# Script to wipe AWS accounts
#
# IMPORTANT, this script is _BRUTAL_ - use at your own risk
#

import signal
import sys
from typing import Optional

import boto3
import botocore
from rich.console import Console
from rich.table import Table

from config import config
from config.cli_args import parse_args
from config.config_environment import parse_environment_config
from config.config_file import parse_config_file
from registry import init_registry_resources, query_registry, terminate_registry
from utils.aws import get_enabled_regions
from view.output_handlers import JSONOutputHandler, RichOutputHandler


# Define the signal handler
def signal_handler(sig, frame):
    """
    Handle the Ctrl+C signal and exit gracefully.

    Args:
        sig: The signal number.
        frame: The current stack frame.

    Returns:
        None

    """
    print('\nCtrl+C pressed. Exiting gracefully...')
    # Perform any necessary cleanup here
    sys.exit(0)


# Set the signal handler for SIGINT
signal.signal(signal.SIGINT, signal_handler)


class UnauthorizedAccountException(Exception):
    pass


def confirm_deletion():
    """
    Prompt the user to confirm deletion.

    Returns:
        bool: True if the user confirms deletion, False otherwise.

    """
    while True:
        response = input('Are you sure you want to delete? (yes/no): ').strip().lower()
        return response == 'yes'


def check_account_compliance(session) -> None:
    """
    Check the compliance of the AWS account.

    Args:
        session: The Boto3 session object.

    Raises:
        SystemError: If the account is blacklisted or not whitelisted.

    """
    account_id = session.client('sts').get_caller_identity()['Account']

    if account_id in config.BLACKLIST_ACCOUNTS:
        raise UnauthorizedAccountException('Cannot Operate On A Blacklisted Account')

    if not config.WHITELIST_ACCOUNTS:
        return

    if account_id not in config.WHITELIST_ACCOUNTS:
        raise UnauthorizedAccountException('Can Only Operate On A Whitelisted Account')


def validate_and_filter_regions(enabled_regions) -> None:
    """
    Validate and filter the enabled regions passed into configuration.

    Args:
        enabled_regions: A list of enabled regions.

    Returns:
        None

    """
    for region in list(config.REGIONS):
        if region not in enabled_regions:
            config.remove_region(region)


def get_actionable_resource_types(registry_services: list[str]) -> list[str]:
    """
    Get the actionable resource types based on the provided registry services.

    Args:
        registry_services (list[str]): The list of registry services.

    Returns:
        list[str]: The list of actionable resource types.

    """

    def warn_unsupported(
        items: set[str], valid_items: set[str], item_type: str
    ) -> None:
        """
        Print a warning for unsupported items.

        Args:
            items (set[str]): The set of items to check.
            valid_items (set[str]): The set of valid items.
            item_type (str): The type of items.

        Returns:
            None

        """
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

        # Check for specific services...
        if include_services and resource_service in include_services:
            actionable.append(resource_type)

        # ... and resource types
        if include_resources and resource_type.lower() in include_resources:
            actionable.append(resource_type)

        # If there are no specific ones, add everything in...
        if not include_resources and not include_services:
            actionable.append(resource_type)

        # ... then remove any explicitly excluded services...
        if resource_service in exclude_services and resource_type in actionable:
            actionable.remove(resource_type)

        # ... and resource types
        if resource_type.lower() in exclude_resources and resource_type in actionable:
            actionable.remove(resource_type)

    return actionable


def show_failures(hard_failures, console):
    table = Table(title='Failures (Access Denied)')
    table.add_column('Region')
    table.add_column('Resource Type')
    table.add_column('Identifier')

    for region, regional_resources in hard_failures.items():
        for resource_type, resource_arns in regional_resources.items():
            for arn in resource_arns:
                table.add_row(region, resource_type, arn)

    print()
    console.print(table)


def get_output_handler(output_format: Optional[str], session, console):
    if output_format == 'json':
        return JSONOutputHandler(session)
    elif output_format == 'rich':
        return RichOutputHandler(session, console)
    else:
        raise ValueError('Invalid Output Method')


def process_resources(session, retrieved_resources):
    hard_failures = {}
    for region, resource_detail in retrieved_resources.items():
        for resource_type, resource_arns in resource_detail.items():
            response = terminate_registry[resource_type](session, region, resource_arns)
            if not response:
                continue
            for arn in response.successful:
                retrieved_resources[region][resource_type].remove(arn)
            for error_code, failed_resources in response.failures.items():
                if error_code == 'AccessDenied':
                    hard_failures.setdefault(region, {}).setdefault(
                        resource_type, []
                    ).extend(failed_resources)
                    for arn in failed_resources:
                        retrieved_resources[region][resource_type].remove(arn)
    return hard_failures


def main(script_args: Optional[dict] = None) -> None:
    """
    The main entry point of the AWS Apocalypse script.

    Args:
        script_args (Optional[dict]): Optional script arguments.

    Returns:
        None

    """
    if not script_args:
        script_args = {}

    # Setup Rich Console
    console = Console(log_path=False, log_time=False, highlight=False)

    # Load Resources from the Registry
    init_registry_resources()

    # Listing Resource Types
    if script_args.get('list_resource_types'):
        console.print('# [yellow] Found AWS Resources\n')
        for service in sorted(query_registry.keys()):
            console.print('[grey35]•[/grey35]', f'{service}')
        return

    if config_file := script_args.get('config'):
        parse_config_file(config_file)

    parse_environment_config()

    # Establish a boto3 session
    try:
        session = boto3.session.Session(profile_name=script_args.get('profile'))
    except botocore.exceptions.ProfileNotFound as e:
        raise SystemError(f'Profile "{script_args.get("profile")}" Not Found.') from e

    # Check that we're allowed to operate in this account.
    try:
        check_account_compliance(session)
    except botocore.exceptions.ClientError as e:
        print('No AWS Access | Please pass an AWS Profile')
        raise SystemExit from e
    except UnauthorizedAccountException as e:
        raise e

    # Clear the screen - TODO: Should we make this optional?
    if config.OUTPUT_FORMAT != 'json':
        console.clear()

    enabled_regions = get_enabled_regions(session) + ['global']
    if config.REGIONS:
        validate_and_filter_regions(enabled_regions)
    else:
        for region in enabled_regions:
            config.add_region(region)

    resource_types = get_actionable_resource_types(list(query_registry.keys()))
    if not resource_types:
        print('No Valid Resources')
        return

    handler = get_output_handler(config.OUTPUT_FORMAT, session, console)
    retrieved_resources = handler.retrieve_data(resource_types, config.REGIONS)
    if not retrieved_resources or config.COMMAND == 'inspect-aws':
        return

    if not confirm_deletion():
        return

    hard_failures = process_resources(session, retrieved_resources)

    if config.OUTPUT_FORMAT == 'rich':
        show_failures(hard_failures, console)


def lambda_handler(
    event: dict,
    context: 'awslambdaric.lambda_context.LambdaContext',  # noqa: F821
):
    """
    Entry point for the AWS Lambda function.

    Args:
        event (dict): The event data passed to the Lambda function.
        context (LambdaContext): The context object representing the runtime information.

    Returns:
        None

    """
    main()


# This will only ever trigger if the script is executed directly
if __name__ == '__main__':
    args = parse_args()
    main(args)
