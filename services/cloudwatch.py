from lib.utils import boto3_tag_list_to_dict, check_delete, paginate_and_search
from registry.decorator import register_query_function, register_terminate_function


@register_query_function('CloudWatch::Alarm')
def query_cloudwatch_alarms(session, region) -> list[str]:
    cloudwatch = session.client('cloudwatch', region_name=region)
    resource_arns = []

    for alarm_arn in paginate_and_search(
        cloudwatch,
        'describe_alarms',
        AlarmTypes=['MetricAlarm'],
        PaginationConfig={'PageSize': 50},
        SearchPath='MetricAlarms[].AlarmArn',
    ):
        alarm_tags = cloudwatch.list_tags_for_resource(ResourceARN=alarm_arn)['Tags']

        if check_delete(boto3_tag_list_to_dict(alarm_tags)):
            resource_arns.append(alarm_arn)

    return resource_arns


@register_terminate_function('CloudWatch::Alarm')
def remove_cloudwatch_alarms(session, region, resource_arns: list[str]) -> None:
    cloudwatch = session.client('cloudwatch', region_name=region)

    alarm_names = [name.split(':')[-1] for name in resource_arns]
    cloudwatch.delete_alarms(AlarmNames=alarm_names)


@register_query_function('CloudWatch::Dashboard')
def query_cloudwatch_dashboards(session, region) -> list[str]:
    cloudwatch = session.client('cloudwatch', region_name='us-east-1')
    return [
        dashboard['DashboardArn']
        for dashboard in paginate_and_search(
            cloudwatch, 'list_dashboards', SearchPath='DashboardEntries[]'
        )
    ]


@register_terminate_function('CloudWatch::Dashboard')
def remove_cloudwatch_dashboards(session, region, resource_arns: list[str]) -> None:
    cloudwatch = session.client('cloudwatch', region_name='us-east-1')

    dashboard_names = [name.split('/')[-1] for name in resource_arns]
    cloudwatch.delete_dashboards(DashboardNames=dashboard_names)
