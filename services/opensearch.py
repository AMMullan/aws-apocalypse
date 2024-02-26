import botocore.exceptions

from registry import DeleteResponse
from registry.decorator import register_query_function, register_terminate_function
from utils.aws import boto3_tag_list_to_dict
from utils.general import check_delete


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
def remove_opensearch_domains(
    session, region, resource_arns: list[str]
) -> DeleteResponse:
    opensearch = session.client('opensearch', region_name=region)

    response = DeleteResponse()

    for domain_arn in resource_arns:
        domain_name = domain_arn.split('/')[-1]

        try:
            opensearch.delete_domain(DomainName=domain_name)
            response.successful.append(domain_arn)
        except botocore.exceptions.ClientError as e:
            error_code = e.response['Error']['Code']
            response.failures[error_code].append(domain_arn)

    return response
