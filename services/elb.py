from config import CONFIG
from lib.utils import (
    boto3_tag_list_to_dict,
    check_delete,
    get_account_id,
    paginate_and_search,
)
from registry.decorator import register_resource


@register_resource('ElasticLoadBalancing::LoadBalancer')
def remove_elb_loadbalancers(session, region) -> list[str]:
    account_id = get_account_id(session)
    elb = session.client('elb', region_name=region)
    removed_resources = []

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
            if not CONFIG['LIST_ONLY']:
                elb.delete_load_balancer(LoadBalancerName=lb_name)

            removed_resources.append(
                f'arn:aws:elasticloadbalancing:{region}:{account_id}:loadbalancer/{lb_name}'
            )

    return removed_resources
