import botocore.exceptions

from registry import DeleteResponse
from registry.decorator import register_query_function, register_terminate_function
from utils.aws import boto3_paginate, boto3_tag_list_to_dict
from utils.general import check_delete


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
def remove_cloudwatch_alarms(
    session, region, resource_arns: list[str]
) -> DeleteResponse:
    cloudwatch = session.client('cloudwatch', region_name=region)

    response = DeleteResponse()

    for alarm_arn in resource_arns:
        alarm_name = alarm_arn.split(':')[-1]

        try:
            cloudwatch.delete_alarms(AlarmNames=[alarm_name])
            response.successful.append(alarm_arn)
        except botocore.exceptions.ClientError as e:
            error_code = e.response['Error']['Code']
            response.failures[error_code].append(alarm_arn)

    return response


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
def remove_cloudwatch_dashboards(
    session, region, resource_arns: list[str]
) -> DeleteResponse:
    cloudwatch = session.client('cloudwatch', region_name='us-east-1')

    response = DeleteResponse()

    for dasbboard_arn in resource_arns:
        dashboard_name = dasbboard_arn.split('/')[-1]

        try:
            cloudwatch.delete_dashboards(DashboardNames=[dashboard_name])
            response.successful.append(dasbboard_arn)
        except botocore.exceptions.ClientError as e:
            error_code = e.response['Error']['Code']
            response.failures[error_code].append(dasbboard_arn)

    return response
