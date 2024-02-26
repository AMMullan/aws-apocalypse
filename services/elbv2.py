import botocore.exceptions

from registry import DeleteResponse
from registry.decorator import register_query_function, register_terminate_function
from utils.aws import boto3_paginate, boto3_tag_list_to_dict
from utils.general import check_delete


@register_query_function('ElasticLoadBalancingV2::LoadBalancer')
def query_elbv2_loadbalancers(session, region) -> list[str]:
    elb = session.client('elbv2', region_name=region)
    resource_arns = []

    loadbalancers = list(
        boto3_paginate(
            elb,
            'describe_load_balancers',
            search='LoadBalancers[].LoadBalancerArn',
        )
    )

    for lb_arn in loadbalancers:
        tags = elb.describe_tags(ResourceArns=[lb_arn])['TagDescriptions'][0]['Tags']

        if check_delete(boto3_tag_list_to_dict(tags)):
            resource_arns.append(lb_arn)

    return resource_arns


@register_terminate_function('ElasticLoadBalancingV2::LoadBalancer')
def remove_elbv2_loadbalancers(
    session, region, resource_arns: list[str]
) -> DeleteResponse:
    elb = session.client('elbv2', region_name=region)

    response = DeleteResponse()

    for lb_arn in resource_arns:
        try:
            elb.delete_load_balancer(LoadBalancerArn=lb_arn)
            response.successful.append(lb_arn)
        except botocore.exceptions.ClientError as e:
            error_code = e.response['Error']['Code']
            response.failures[error_code].append(lb_arn)

    return response


@register_query_function('ElasticLoadBalancingV2::TargetGroup')
def query_elbv2_targetgroups(session, region) -> list[str]:
    elb = session.client('elbv2', region_name=region)
    resource_arns = []

    groups = list(
        boto3_paginate(
            elb,
            'describe_target_groups',
            search='TargetGroups[].TargetGroupArn',
        )
    )

    for group_arn in groups:
        tags = elb.describe_tags(ResourceArns=[group_arn])['TagDescriptions'][0]['Tags']

        if check_delete(boto3_tag_list_to_dict(tags)):
            resource_arns.append(group_arn)

    return resource_arns


@register_terminate_function('ElasticLoadBalancingV2::TargetGroup')
def remove_elbv2_targetgroups(
    session, region, resource_arns: list[str]
) -> DeleteResponse:
    elb = session.client('elbv2', region_name=region)

    response = DeleteResponse()

    for group_arn in resource_arns:
        try:
            elb.delete_target_group(TargetGroupArn=group_arn)
            response.successful.append(group_arn)
        except botocore.exceptions.ClientError as e:
            error_code = e.response['Error']['Code']
            response.failures[error_code].append(group_arn)

    return response
