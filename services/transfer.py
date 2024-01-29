from lib.utils import boto3_tag_list_to_dict, check_delete, paginate_and_search
from registry.decorator import register_query_function, register_terminate_function


@register_query_function('Transfer::Server')
def query_transfer_servers(session, region) -> list[str]:
    transfer = session.client('transfer', region_name=region)
    resource_arns = []

    servers = list(
        paginate_and_search(
            transfer,
            'list_servers',
            PaginationConfig={'PageSize': 100},
            SearchPath='Servers[].Arn',
        )
    )

    for server_arn in servers:
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
            resource_arns.append(server_arn)

    return resource_arns


@register_terminate_function('Transfer::Server')
def remove_transfer_servers(session, region, resource_arns: list[str]) -> None:
    transfer = session.client('transfer', region_name=region)

    for server_arn in resource_arns:
        server_id = server_arn.split('/')[-1]
        transfer.delete_server(ServerId=server_id)
