import botocore.exceptions

from registry import DeleteResponse
from registry.decorator import register_query_function, register_terminate_function
from utils.aws import boto3_paginate, boto3_tag_list_to_dict
from utils.general import check_delete


@register_query_function('SecretsManager::Secret')
def query_secretsmanager_secret(session, region) -> list[str]:
    secretsmanager = session.client('secretsmanager', region_name=region)
    secrets = list(
        boto3_paginate(
            secretsmanager,
            'list_secrets',
            search='SecretList[].[ARN,Tags]',
        )
    )

    return [
        secret_arn
        for secret_arn, secret_tags in secrets
        if check_delete(boto3_tag_list_to_dict(secret_tags))
    ]


@register_terminate_function('SecretsManager::Secret')
def remove_secretsmanager_secret(
    session, region, resource_arns: list[str]
) -> DeleteResponse:
    secretsmanager = session.client('secretsmanager', region_name=region)

    response = DeleteResponse()

    for secret_arn in resource_arns:
        try:
            secretsmanager.delete_secret(
                SecretId=secret_arn, ForceDeleteWithoutRecovery=True
            )
            response.successful.append(secret_arn)
        except botocore.exceptions.ClientError as e:
            error_code = e.response['Error']['Code']
            response.failures[error_code].append(secret_arn)

    return response
