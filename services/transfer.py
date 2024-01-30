from utils.general import check_delete
from registry.decorator import register_query_function, register_terminate_function
from utils.aws import boto3_paginate, boto3_tag_list_to_dict


@register_query_function('Transfer::Server')
def query_transfer_servers(session, region) -> list[str]:
    transfer = session.client('transfer', region_name=region)
    resource_arns = []

    servers = list(
        boto3_paginate(
            transfer,
            'list_servers',
            search='Servers[].Arn',
        )
    )

    for server_arn in servers:
        tags = list(
            boto3_paginate(
                transfer,
                'list_tags_for_resource',
                Arn=server_arn,
                search='Tags[]',
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
