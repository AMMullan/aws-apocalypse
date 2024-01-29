from lib.utils import (
    boto3_tag_list_to_dict,
    check_delete,
    get_account_id,
    paginate_and_search,
)
from registry.decorator import register_query_function, register_terminate_function


@register_query_function('ElasticLoadBalancing::LoadBalancer')
def query_elb_loadbalancers(session, region) -> list[str]:
    account_id = get_account_id(session)
    elb = session.client('elb', region_name=region)
    resource_arns = []

    loadbalancers = list(
        paginate_and_search(
            elb,
            'describe_load_balancers',
            PaginationConfig={'PageSize': 400},
            SearchPath='LoadBalancerDescriptions[].LoadBalancerName',
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
def remove_elb_loadbalancers(session, region, resource_arns: list[str]) -> None:
    elb = session.client('elb', region_name=region)

    for lb_arn in resource_arns:
        lb_name = lb_arn.split('/')[-1]
        elb.delete_load_balancer(LoadBalancerName=lb_name)
