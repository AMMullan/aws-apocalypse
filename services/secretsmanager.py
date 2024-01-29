from lib.utils import boto3_tag_list_to_dict, check_delete, paginate_and_search
from registry.decorator import register_query_function, register_terminate_function


@register_query_function('SecretsManager::Secret')
def query_secretsmanager_secret(session, region) -> list[str]:
    secretsmanager = session.client('secretsmanager', region_name=region)
    secrets = list(
        paginate_and_search(
            secretsmanager,
            'list_secrets',
            PaginationConfig={'PageSize': 100},
            SearchPath='SecretList[].[ARN,Tags]',
        )
    )

    return [
        secret_arn
        for secret_arn, secret_tags in secrets
        if check_delete(boto3_tag_list_to_dict(secret_tags))
    ]


@register_terminate_function('SecretsManager::Secret')
def remove_secretsmanager_secret(session, region, resource_arns: list[str]) -> None:
    secretsmanager = session.client('secretsmanager', region_name=region)

    for secret_arn in resource_arns:
        secretsmanager.delete_secret(
            SecretId=secret_arn, ForceDeleteWithoutRecovery=True
        )
