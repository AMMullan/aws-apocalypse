from utils.general import check_delete
from registry.decorator import register_query_function, register_terminate_function
from utils.aws import boto3_tag_list_to_dict


@register_query_function('Elasticsearch::Domain')
def query_opensearch_domains(session, region) -> list[str]:
    es = session.client('es', region_name=region)
    resource_arns = []

    domains = [
        es_domain['ARN']
        for es_domain in es.describe_elasticsearch_domains(
            DomainNames=[
                domain['DomainName']
                for domain in es.list_domain_names(EngineType='Elasticsearch')[
                    'DomainNames'
                ]
            ]
        )['DomainStatusList']
        if not es_domain['Deleted']
    ]
    for domain_arn in domains:
        domain_tags = es.list_tags(ARN=domain_arn)['TagList']
        if check_delete(boto3_tag_list_to_dict(domain_tags)):
            resource_arns.append(domain_arn)

    return resource_arns


@register_terminate_function('Elasticsearch::Domain')
def remove_opensearch_domains(session, region, resource_arns: list[str]) -> None:
    es = session.client('es', region_name=region)

    for domain_arn in resource_arns:
        domain_name = domain_arn.split('/')
        es.delete_elasticsearch_domain(DomainName=domain_name)
