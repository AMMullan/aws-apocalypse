import botocore.exceptions

from registry import DeleteResponse
from registry.decorator import register_query_function, register_terminate_function
from utils.aws import boto3_paginate
from utils.general import check_delete


@register_query_function('Logs::LogGroup')
def query_logs_loggroups(session, region) -> list[str]:
    logs = session.client('logs', region_name=region)
    resource_arns = []

    log_groups = [
        group_arn[:-2]
        for group_arn in boto3_paginate(
            logs,
            'describe_log_groups',
            search='logGroups[].arn',
        )
    ]

    for group_arn in log_groups:
        group_tags = logs.list_tags_for_resource(resourceArn=group_arn)['tags']

        if check_delete(group_tags):
            resource_arns.append(group_arn)

    return resource_arns


@register_terminate_function('Logs::LogGroup')
def remove_logs_loggroups(session, region, resource_arns: list[str]) -> DeleteResponse:
    logs = session.client('logs', region_name=region)

    response = DeleteResponse()

    for group_arn in resource_arns:
        group_name = group_arn.split(':')[-1]

        try:
            logs.delete_log_group(logGroupName=group_name)
            response.successful.append(group_arn)
        except botocore.exceptions.ClientError as e:
            error_code = e.response['Error']['Code']
            response.failures[error_code].append(group_arn)

    return response
