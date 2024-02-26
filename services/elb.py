import botocore.exceptions

from registry import DeleteResponse
from registry.decorator import register_query_function, register_terminate_function
from utils.aws import boto3_paginate, boto3_tag_list_to_dict, get_account_id
from utils.general import check_delete


@register_query_function('ElasticLoadBalancing::LoadBalancer')
def query_elb_loadbalancers(session, region) -> list[str]:
    account_id = get_account_id(session)
    elb = session.client('elb', region_name=region)
    resource_arns = []

    loadbalancers = list(
        boto3_paginate(
            elb,
            'describe_load_balancers',
            search='LoadBalancerDescriptions[].LoadBalancerName',
        )
    )

    for lb_name in loadbalancers:
        tags = elb.describe_tags(LoadBalancerNames=[lb_name])['TagDescriptions'][0][
            'Tags'
        ]

        if check_delete(boto3_tag_list_to_dict(tags)):
            resource_arns.append(
                f'arn:aws:elasticloadbalancing:{region}:{account_id}:loadbalancer/{lb_name}'
            )

    return resource_arns


@register_terminate_function('ElasticLoadBalancing::LoadBalancer')
def remove_elb_loadbalancers(
    session, region, resource_arns: list[str]
) -> DeleteResponse:
    elb = session.client('elb', region_name=region)

    response = DeleteResponse()

    for lb_arn in resource_arns:
        lb_name = lb_arn.split('/')[-1]

        try:
            elb.delete_load_balancer(LoadBalancerName=lb_name)
            response.successful.append(lb_arn)
        except botocore.exceptions.ClientError as e:
            error_code = e.response['Error']['Code']
            response.failures[error_code].append(lb_arn)

    return response
