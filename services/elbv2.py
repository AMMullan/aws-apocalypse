from lib.utils import boto3_tag_list_to_dict, check_delete
from registry.decorator import register_query_function, register_terminate_function
from utils.aws import boto3_paginate


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
def remove_elbv2_loadbalancers(session, region, resource_arns: list[str]) -> None:
    elb = session.client('elbv2', region_name=region)

    for lb_arn in resource_arns:
        elb.delete_load_balancer(LoadBalancerArn=lb_arn)


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
def remove_elbv2_targetgroups(session, region, resource_arns: list[str]) -> None:
    elb = session.client('elbv2', region_name=region)

    for group_arn in resource_arns:
        elb.delete_target_group(TargetGroupArn=group_arn)
