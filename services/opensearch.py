from lib.utils import boto3_tag_list_to_dict, check_delete
from registry.decorator import register_query_function, register_terminate_function


@register_query_function('OpenSearchService::Domain')
def query_opensearch_domains(session, region) -> list[str]:
    opensearch = session.client('opensearch', region_name=region)
    resource_arns = []

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
            resource_arns.append(domain_arn)

    return resource_arns


@register_terminate_function('OpenSearchService::Domain')
def remove_opensearch_domains(session, region, resource_arns: list[str]) -> None:
    opensearch = session.client('opensearch', region_name=region)

    for domain_arn in resource_arns:
        domain_name = domain_arn.split('/')[-1]
        opensearch.delete_domain(DomainName=domain_name)
