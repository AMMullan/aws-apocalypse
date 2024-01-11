from config import CONFIG
from lib.utils import boto3_tag_list_to_dict, check_delete, paginate_and_search
from registry.decorator import register_resource


@register_resource('CloudWatch::Alarm')
def remove_cloudwatch_alarms(session, region) -> list[str]:
    cloudwatch = session.client('cloudwatch', region_name=region)
    removed_resources = []

    log_groups = list(
        paginate_and_search(
            cloudwatch,
            'describe_alarms',
            AlarmTypes=['MetricAlarm'],
            PaginationConfig={'PageSize': 50},
            SearchPath='MetricAlarms[].[AlarmArn,AlarmName]',
        )
    )

    for alarm_arn, alarm_name in log_groups:
        alarm_tags = cloudwatch.list_tags_for_resource(ResourceARN=alarm_arn)['Tags']

        if check_delete(boto3_tag_list_to_dict(alarm_tags)):
            if not CONFIG['LIST_ONLY']:
                cloudwatch.delete_alarms(AlarmNames=[alarm_name])

            removed_resources.append(alarm_arn)

    return removed_resources


@register_resource('CloudWatch::Dashboard')
def remove_cloudwatch_dashboards(session, region) -> list[str]:
    if region != 'global':
        return

    cloudwatch = session.client('cloudwatch', region_name='us-east-1')
    removed_resources = []

    dashboards = [
        [dashboard['DashboardName'], dashboard['DashboardArn']]
        for dashboard in cloudwatch.list_dashboards()['DashboardEntries']
    ]

    for dashboard_name, dashboard_arn in dashboards:
        if not CONFIG['LIST_ONLY']:
            cloudwatch.delete_dashboards(DashboardNames=[dashboard_name])

        removed_resources.append(dashboard_arn)

    return removed_resources
