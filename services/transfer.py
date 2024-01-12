from config import CONFIG
from lib.utils import boto3_tag_list_to_dict, check_delete, paginate_and_search
from registry.decorator import register_resource


@register_resource('Transfer::Server')
def remove_transfer_servers(session, region) -> list[str]:
    transfer = session.client('transfer', region_name=region)
    removed_resources = []

    servers = list(
        paginate_and_search(
            transfer,
            'list_servers',
            PaginationConfig={'PageSize': 100},
            SearchPath='Servers[].[Arn,ServerId]',
        )
    )

    for server_arn, server_id in servers:
        tags = list(
            paginate_and_search(
                transfer,
                'list_tags_for_resource',
                Arn=server_arn,
                PaginationConfig={'PageSize': 50},
                SearchPath='Tags[]',
            )
        )

        if check_delete(boto3_tag_list_to_dict(tags)):
            if not CONFIG['LIST_ONLY']:
                transfer.delete_server(ServerId=server_id)

            removed_resources.append(server_arn)

    return removed_resources
