from config import CONFIG
from lib.utils import boto3_tag_list_to_dict, check_delete, paginate_and_search
from registry.decorator import register_resource


@register_resource('SecretsManager::Secret')
def remove_secretsmanager_secret(session, region) -> list[str]:
    secretsmanager = session.client('secretsmanager', region_name=region)
    removed_resources = []

    secrets = list(
        paginate_and_search(
            secretsmanager,
            'list_secrets',
            PaginationConfig={'PageSize': 100},
            SearchPath='SecretList[].[ARN,Tags]',
        )
    )

    for secret_arn, secret_tags in secrets:
        if check_delete(boto3_tag_list_to_dict(secret_tags)):
            if not CONFIG['LIST_ONLY']:
                secretsmanager.delete_secret(
                    SecretId=secret_arn, ForceDeleteWithoutRecovery=True
                )

            removed_resources.append(secret_arn)

    return removed_resources
