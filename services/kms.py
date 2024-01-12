from config import CONFIG
from lib.utils import boto3_tag_list_to_dict, check_delete, paginate_and_search
from registry.decorator import register_resource


@register_resource('KMS::Key')
def remove_kms_keys(session, region) -> list[str]:
    kms = session.client('kms', region_name=region)
    removed_resources = []

    instances = list(
        paginate_and_search(
            kms,
            'list_keys',
            PaginationConfig={'PageSize': 100},
            SearchPath='Keys[].[KeyId,KeyArn]',
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
            paginate_and_search(
                kms,
                'list_resource_tags',
                KeyId=key_id,
                PaginationConfig={'PageSize': 50},
                SearchPath='Tags[]',
            )
        )
        if not check_delete(boto3_tag_list_to_dict(key_tags)):
            continue

        if not CONFIG['LIST_ONLY']:
            aliases = list(
                paginate_and_search(
                    kms,
                    'list_aliases',
                    KeyId=key_id,
                    PaginationConfig={'PageSize': 50},
                    SearchPath='Aliases[].AliasName',
                )
            )
            for alias in aliases:
                kms.delete_alias(AliasName=alias)

            kms.schedule_key_deletion(KeyId=key_id, PendingWindowInDays=7)

        removed_resources.append(key_arn)

    return removed_resources
