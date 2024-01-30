from lib.utils import boto3_tag_list_to_dict, check_delete
from registry.decorator import register_query_function, register_terminate_function
from utils.aws import boto3_paginate


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
def remove_acm_certificates(session, region, resource_arns: list[str]) -> None:
    acm = session.client('acm', region_name=region)

    for cert_arn in resource_arns:
        acm.delete_certificate(CertificateArn=cert_arn)
