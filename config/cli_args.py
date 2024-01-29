import argparse
import contextlib

from config import CONFIG


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
        '--resource',
        help='Search Resources for a Specific AWS Service',
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
        '--exclude-resource',
        help='Exclude Resources for a Specific AWS Service',
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
        '--resource',
        help='Resources for a Specific AWS Service',
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
        '--exclude-resource',
        help='Exclude Resources for a Specific AWS Service',
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
    args.list_resource_types = global_args.list_resource_types

    if not args.command and not args.list_resource_types:
        main_parser.print_help()
        raise SystemExit

    with contextlib.suppress(AttributeError):
        CONFIG['ALLOW_EXCEPTIONS'] = args.allow_exceptions
        CONFIG['EXCEPTION_TAGS'] = list(
            set(CONFIG['EXCEPTION_TAGS']) | set(args.exception_tag or [])
        )

    return args
