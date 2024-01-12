from config import CONFIG
from lib.utils import boto3_tag_list_to_dict, check_delete, paginate_and_search
from registry.decorator import register_resource


@register_resource('ElasticLoadBalancingV2::LoadBalancer')
def remove_elbv2_loadbalancers(session, region) -> list[str]:
    elb = session.client('elbv2', region_name=region)
    removed_resources = []

    loadbalancers = list(
        paginate_and_search(
            elb,
            'describe_load_balancers',
            PaginationConfig={'PageSize': 400},
            SearchPath='LoadBalancers[].LoadBalancerArn',
        )
    )

    for lb_arn in loadbalancers:
        tags = elb.describe_tags(ResourceArns=[lb_arn])['TagDescriptions'][0]['Tags']

        if check_delete(boto3_tag_list_to_dict(tags)):
            if not CONFIG['LIST_ONLY']:
                elb.delete_load_balancer(LoadBalancerArn=lb_arn)

            removed_resources.append(lb_arn)

    return removed_resources


@register_resource('ElasticLoadBalancingV2::TargetGroup')
def remove_elbv2_targetgroups(session, region) -> list[str]:
    elb = session.client('elbv2', region_name=region)
    removed_resources = []

    groups = list(
        paginate_and_search(
            elb,
            'describe_target_groups',
            PaginationConfig={'PageSize': 400},
            SearchPath='TargetGroups[].TargetGroupArn',
        )
    )

    for group_arn in groups:
        tags = elb.describe_tags(ResourceArns=[group_arn])['TagDescriptions'][0]['Tags']

        if check_delete(boto3_tag_list_to_dict(tags)):
            if not CONFIG['LIST_ONLY']:
                elb.delete_target_group(TargetGroupArn=group_arn)

            removed_resources.append(group_arn)

    return removed_resources
