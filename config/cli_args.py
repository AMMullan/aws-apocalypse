import argparse
import contextlib
from pathlib import Path

from config import config


def is_valid_file(parser, arg):
    if not Path(arg).exists():
        parser.error(f"The configuration file '{arg}' does not exist!")

    return Path(arg)


def add_common_arguments(parser):
    parser.add_argument(
        '--allow-exceptions', help='Allow Exceptions', action='store_true'
    )
    parser.add_argument(
        '--exception-tag', help='Exception Tag', action='append', default=[]
    )
    parser.add_argument('--region', help='AWS Region', action='append', default=[])
    parser.add_argument(
        '--exclude-region', help='AWS Region', action='append', default=[]
    )
    parser.add_argument(
        '--resource-type',
        help='Included Resource Types',
        action='append',
        default=[],
    )
    parser.add_argument(
        '--service',
        help='Specific AWS Service',
        action='append',
        default=[],
    )
    parser.add_argument(
        '--exclude-resource-type',
        help='Exclude Resource Type',
        action='append',
        default=[],
    )
    parser.add_argument(
        '--exclude-service',
        help='Exclude Specific AWS Service',
        action='append',
        default=[],
    )


def parse_args() -> dict:
    global_parser = argparse.ArgumentParser(add_help=False)
    global_parser.add_argument(
        '-v',
        '--version',
        action='version',
        version='%(prog)s 1.0',
        help="Show program's version number and exit.",
    )

    # NB: Any Global Argument needs to be added to the main_parser later
    global_parser.add_argument('--profile', help='AWS SSO Profile')
    global_parser.add_argument(
        '--config',
        help='Configuration File',
        type=lambda x: is_valid_file(global_parser, x),
    )
    global_parser.add_argument(
        '--list-resource-types',
        action='store_true',
        help='List Supported Resource Types',
    )

    global_parser.add_argument(
        '--output',
        choices=['rich', 'json'],
        default='rich',
        help='Output Format - "rich" for Rich Formatting, or "json" to retrieve pure data',
    )
    global_args, _ = global_parser.parse_known_args()

    main_parser = argparse.ArgumentParser(parents=[global_parser])
    subparsers = main_parser.add_subparsers(dest='command', required=False)

    # Arguments for 'inspect-aws' command
    command_inspect = subparsers.add_parser(
        'inspect-aws',
        parents=[global_parser],
        help='(default) Non-destructive inspection of target resources only',
    )

    # Arguments for 'aws' command
    command_aws = subparsers.add_parser(
        'aws',
        parents=[global_parser],
        help='BEWARE: DESTRUCTIVE OPERATION! Nukes AWS resources',
    )

    add_common_arguments(command_inspect)
    add_common_arguments(command_aws)

    args = main_parser.parse_args()

    if args.command is None:
        config.COMMAND = 'inspect-aws'
        args = command_inspect.parse_args()
    else:
        config.COMMAND = args.command

    # Add Global Arguments here
    args.profile = global_args.profile
    args.config = global_args.config
    args.list_resource_types = global_args.list_resource_types

    # If we're doing a --list-resource-types, return early so we can just list resources
    if args.list_resource_types:
        return vars(args)

    config.OUTPUT_FORMAT = args.output

    if args.region:
        for region in args.region:
            config.add_region(region)

    if args.exclude_region:
        for region in args.exclude_region:
            config.remove_region(region)

    if args.resource_type:
        for resource in args.resource_type:
            config.add_included_resource(resource)

    if args.exclude_resource_type:
        for resource in args.exclude_resource_type:
            config.add_excluded_resource(resource)

    if args.service:
        for service in args.service:
            config.add_included_service(service)

    if args.exclude_service:
        for service in args.exclude_service:
            config.add_excluded_service(service)

    with contextlib.suppress(AttributeError):
        config.ALLOW_EXCEPTIONS = args.allow_exceptions
        if args.exception_tag:
            config.add_custom_exception_tag(args.exception_tag)

    return vars(args)
