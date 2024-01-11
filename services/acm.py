from config import CONFIG
from lib.utils import boto3_tag_list_to_dict, check_delete, paginate_and_search
from registry.decorator import register_resource


@register_resource('CertificateManager::Certificate')
def remove_acm_certificates(session, region) -> list[str]:
    acm = session.client('acm', region_name=region)
    removed_resources = []

    certificates = list(
        paginate_and_search(
            acm,
            'list_certificates',
            PaginationConfig={'PageSize': 100},
            SearchPath='CertificateSummaryList[].CertificateArn',
        )
    )

    for cert_arn in certificates:
        cert_tags = acm.list_tags_for_certificate(CertificateArn=cert_arn)['Tags']

        if check_delete(boto3_tag_list_to_dict(cert_tags)):
            if not CONFIG['LIST_ONLY']:
                acm.delete_certificate(CertificateArn=cert_arn)

            removed_resources.append(cert_arn)

    return removed_resources
