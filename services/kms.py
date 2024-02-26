import botocore.exceptions

from registry import DeleteResponse
from registry.decorator import register_query_function, register_terminate_function
from utils.aws import boto3_paginate, boto3_tag_list_to_dict
from utils.general import check_delete


@register_query_function('KMS::Key')
def query_kms_keys(session, region) -> list[str]:
    kms = session.client('kms', region_name=region)
    resource_arns = []

    instances = list(
        boto3_paginate(
            kms,
            'list_keys',
            search='Keys[].[KeyId,KeyArn]',
        )
    )

    for key_id, key_arn in instances:
        key_detail = kms.describe_key(KeyId=key_id)['KeyMetadata']

        if (
            key_detail['KeyManager'] != 'CUSTOMER'
            or key_detail['KeyState'] == 'PendingDeletion'
        ):
            continue

        key_tags = list(
            boto3_paginate(
                kms,
                'list_resource_tags',
                KeyId=key_id,
                search='Tags[]',
            )
        )
        if not check_delete(boto3_tag_list_to_dict(key_tags)):
            continue

        resource_arns.append(key_arn)

    return resource_arns


@register_terminate_function('KMS::Key')
def remove_kms_keys(session, region, resource_arns: list[str]) -> DeleteResponse:
    kms = session.client('kms', region_name=region)

    response = DeleteResponse()

    for key_arn in resource_arns:
        key_id = key_arn.split('/')[-1]

        aliases = list(
            boto3_paginate(
                kms,
                'list_aliases',
                KeyId=key_id,
                search='Aliases[].AliasName',
            )
        )

        try:
            for alias in aliases:
                kms.delete_alias(AliasName=alias)

            kms.schedule_key_deletion(KeyId=key_id, PendingWindowInDays=7)
            response.successful.append(key_arn)
        except botocore.exceptions.ClientError as e:
            error_code = e.response['Error']['Code']
            response.failures[error_code].append(key_arn)

    return response
