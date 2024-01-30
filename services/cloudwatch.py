from utils.general import check_delete
from registry.decorator import register_query_function, register_terminate_function
from utils.aws import boto3_paginate, boto3_tag_list_to_dict


@register_query_function('CloudWatch::Alarm')
def query_cloudwatch_alarms(session, region) -> list[str]:
    cloudwatch = session.client('cloudwatch', region_name=region)
    resource_arns = []

    for alarm_arn in boto3_paginate(
        cloudwatch,
        'describe_alarms',
        AlarmTypes=['MetricAlarm'],
        search='MetricAlarms[].AlarmArn',
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
        for dashboard in boto3_paginate(
            cloudwatch, 'list_dashboards', search='DashboardEntries[]'
        )
    ]


@register_terminate_function('CloudWatch::Dashboard')
def remove_cloudwatch_dashboards(session, region, resource_arns: list[str]) -> None:
    cloudwatch = session.client('cloudwatch', region_name='us-east-1')

    dashboard_names = [name.split('/')[-1] for name in resource_arns]
    cloudwatch.delete_dashboards(DashboardNames=dashboard_names)
