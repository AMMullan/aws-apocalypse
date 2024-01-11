from config import CONFIG
from lib.utils import boto3_tag_list_to_dict, check_delete
from registry.decorator import register_resource


@register_resource('Elasticsearch::Domain')
def remove_opensearch_domains(session, region) -> list[str]:
    es = session.client('es', region_name=region)
    removed_items = []

    domains = [
        [es_domain['ARN'], es_domain['DomainName']]
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
    for domain_arn, domain_name in domains:
        domain_tags = es.list_tags(ARN=domain_arn)['TagList']
        if check_delete(boto3_tag_list_to_dict(domain_tags)):
            if not CONFIG['LIST_ONLY']:
                es.delete_elasticsearch_domain(DomainName=domain_name)

            removed_items.append(domain_arn)

    return removed_items
