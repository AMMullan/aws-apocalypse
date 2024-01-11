from config import CONFIG
from lib.utils import boto3_tag_list_to_dict, check_delete
from registry.decorator import register_resource


@register_resource('OpenSearchService::Domain')
def remove_opensearch_domains(session, region) -> list[str]:
    opensearch = session.client('opensearch', region_name=region)
    removed_items = []

    domains = [
        domain['DomainName']
        for domain in opensearch.list_domain_names(EngineType='OpenSearch')[
            'DomainNames'
        ]
    ]
    for domain_name in domains:
        domain_detail = opensearch.describe_domain(DomainName=domain_name)[
            'DomainStatus'
        ]

        if domain_detail['Deleted']:
            continue

        domain_arn = domain_detail['ARN']
        domain_tags = opensearch.list_tags(ARN=domain_arn)['TagList']

        if check_delete(boto3_tag_list_to_dict(domain_tags)):
            if not CONFIG['LIST_ONLY']:
                opensearch.delete_domain(DomainName=domain_name)

            removed_items.append(domain_arn)

    return removed_items
