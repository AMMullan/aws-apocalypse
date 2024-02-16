import botocore.exceptions

from registry import DeleteResponse
from registry.decorator import register_query_function, register_terminate_function
from utils.aws import boto3_paginate, boto3_tag_list_to_dict
from utils.general import check_delete


@register_query_function('CertificateManager::Certificate')
def query_acm_certificates(session, region) -> list[str]:
    acm = session.client('acm', region_name=region)
    resource_arns = []

    certificates = list(
        boto3_paginate(
            acm,
            'list_certificates',
            search='CertificateSummaryList[].CertificateArn',
        )
    )

    for cert_arn in certificates:
        cert_tags = acm.list_tags_for_certificate(CertificateArn=cert_arn)['Tags']

        if check_delete(boto3_tag_list_to_dict(cert_tags)):
            resource_arns.append(cert_arn)

    return resource_arns


@register_terminate_function('CertificateManager::Certificate')
def remove_acm_certificates(
    session, region, resource_arns: list[str]
) -> DeleteResponse:
    acm = session.client('acm', region_name=region)

    response = DeleteResponse()

    for cert_arn in resource_arns:
        try:
            acm.delete_certificate(CertificateArn=cert_arn)
            response.successful.append(cert_arn)
        except botocore.exceptions.ClientError as e:
            error_code = e.response['Error']['Code']
            response.failures[error_code].append(cert_arn)

    return response
