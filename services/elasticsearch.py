import botocore.exceptions

from registry import DeleteResponse
from registry.decorator import register_query_function, register_terminate_function
from utils.aws import boto3_tag_list_to_dict
from utils.general import check_delete


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
def remove_opensearch_domains(
    session, region, resource_arns: list[str]
) -> DeleteResponse:
    es = session.client('es', region_name=region)

    response = DeleteResponse()

    for domain_arn in resource_arns:
        domain_name = domain_arn.split('/')

        try:
            es.delete_elasticsearch_domain(DomainName=domain_name)
            response.successful.append(domain_arn)
        except botocore.exceptions.ClientError as e:
            error_code = e.response['Error']['Code']
            response.failures[error_code].append(domain_arn)

    return response
