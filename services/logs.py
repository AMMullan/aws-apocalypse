from config import CONFIG
from lib.utils import check_delete, paginate_and_search
from registry.decorator import register_resource


@register_resource('Logs::LogGroup')
def remove_logs_loggroups(session, region) -> list[str]:
    logs = session.client('logs', region_name=region)
    removed_resources = []

    log_groups = [
        group_arn[:-2]
        for group_arn in paginate_and_search(
            logs,
            'describe_log_groups',
            PaginationConfig={'PageSize': 50},
            SearchPath='logGroups[].arn',
        )
    ]

    for group_arn in log_groups:
        group_name = group_arn.split(':')[-1]
        group_tags = logs.list_tags_for_resource(resourceArn=group_arn)['tags']

        if check_delete(group_tags):
            if not CONFIG['LIST_ONLY']:
                logs.delete_log_group(logGroupName=group_name)

            removed_resources.append(group_arn)

    return removed_resources
