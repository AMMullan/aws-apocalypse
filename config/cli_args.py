import argparse
import contextlib
from pathlib import Path

from config import config


def is_valid_file(parser, arg):
    if not Path(arg).exists():
        parser.error(f"The configuration file '{arg}' does not exist!")

    return Path(arg)


def parse_args() -> None:  # sourcery skip: extract-duplicate-method
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

    # Arguments for 'aws' command
    command_aws = subparsers.add_parser(
        'aws',
        parents=[global_parser],
        help='BEWARE: DESTRUCTIVE OPERATION! Nukes AWS resources',
    )
    command_aws.add_argument(
        '--allow-exceptions', help='Allow Exceptions', action='store_true'
    )
    command_aws.add_argument('--exception-tag', help='Exception Tag', action='append')
    command_aws.add_argument('--region', help='AWS Region', action='append')
    command_aws.add_argument('--exclude-region', help='AWS Region', action='append')
    command_aws.add_argument(
        '--resource-type',
        help='Included Resource Types',
        action='append',
        default=[],
    )
    command_aws.add_argument(
        '--service',
        help='Search Search Specific AWS Service',
        action='append',
        default=[],
    )
    command_aws.add_argument(
        '--exclude-resource-type',
        help='Exclude Resource Type',
        action='append',
        default=[],
    )
    command_aws.add_argument(
        '--exclude-service',
        help='Exclude Specific AWS Service',
        action='append',
        default=[],
    )

    # Arguments for 'inspect-aws' command
    command_inspect = subparsers.add_parser(
        'inspect-aws',
        parents=[global_parser],
        help='Non-destructive inspection of target resources only',
    )
    command_inspect.add_argument(
        '--allow-exceptions', help='Allow Exceptions', action='store_true'
    )
    command_inspect.add_argument(
        '--exception-tag', help='Exception Tag', action='append'
    )
    command_inspect.add_argument('--region', help='AWS Region', action='append')
    command_inspect.add_argument('--exclude-region', help='AWS Region', action='append')
    command_inspect.add_argument(
        '--resource-type',
        help='Included Resource Types',
        action='append',
        default=[],
    )
    command_inspect.add_argument(
        '--service',
        help='Specific AWS Service',
        action='append',
        default=[],
    )
    command_inspect.add_argument(
        '--exclude-resource-type',
        help='Exclude Resource Type',
        action='append',
        default=[],
    )
    command_inspect.add_argument(
        '--exclude-service',
        help='Exclude Specific AWS Service',
        action='append',
        default=[],
    )

    args = main_parser.parse_args()

    # Add Global Arguments here
    args.profile = global_args.profile
    args.config = global_args.config
    args.list_resource_types = global_args.list_resource_types

    if not args.command and not args.list_resource_types:
        main_parser.print_help()
        raise SystemExit

    if args.region:
        for region in args.region:
            config.REGIONS.add(region)

    if args.exclude_region:
        for region in args.exclude_region:
            config.EXCLUDE_REGIONS.add(region)

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

    return args
