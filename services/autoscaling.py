import botocore.exceptions

from registry import DeleteResponse
from registry.decorator import register_query_function, register_terminate_function
from utils.aws import boto3_paginate, boto3_tag_list_to_dict
from utils.general import check_delete


@register_query_function('AutoScaling::AutoScalingGroup')
def query_autoscaling_groups(session, region) -> list[str]:
    autoscaling = session.client('autoscaling', region_name=region)
    groups = list(
        boto3_paginate(
            autoscaling,
            'describe_auto_scaling_groups',
            search='AutoScalingGroups[].[AutoScalingGroupARN,Tags]',
        )
    )

    return [
        group_arn
        for group_arn, group_tags in groups
        if check_delete(boto3_tag_list_to_dict(group_tags))
    ]


@register_terminate_function('AutoScaling::AutoScalingGroup')
def remove_autoscaling_groups(
    session, region, resource_arns: list[str]
) -> DeleteResponse:
    autoscaling = session.client('autoscaling', region_name=region)

    response = DeleteResponse()

    for group_arn in resource_arns:
        try:
            autoscaling.delete_auto_scaling_group(
                AutoScalingGroupName=group_arn.split('/')[-1]
            )
            response.successful.append(group_arn)
        except botocore.exceptions.ClientError as e:
            error_code = e.response['Error']['Code']
            response.failures[error_code].append(group_arn)

    return response


@register_query_function('AutoScaling::LaunchConfiguration')
def query_autoscaling_launch_configs(session, region) -> list[str]:
    autoscaling = session.client('autoscaling', region_name=region)
    return list(
        boto3_paginate(
            autoscaling,
            'describe_launch_configurations',
            search='LaunchConfigurations[].LaunchConfigurationARN',
        )
    )


@register_terminate_function('AutoScaling::LaunchConfiguration')
def remove_autoscaling_launch_configs(
    session, region, resource_arns: list[str]
) -> DeleteResponse:
    autoscaling = session.client('autoscaling', region_name=region)

    response = DeleteResponse()

    for config_arn in resource_arns:
        try:
            autoscaling.delete_launch_configuration(
                LaunchConfigurationName=config_arn.split('/')[-1]
            )
        except botocore.exceptions.ClientError as e:
            error_code = e.response['Error']['Code']
            response.failures[error_code].append(config_arn)

    return response
