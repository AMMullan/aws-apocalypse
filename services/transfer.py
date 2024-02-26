import botocore.exceptions

from registry import DeleteResponse
from registry.decorator import register_query_function, register_terminate_function
from utils.aws import boto3_paginate, boto3_tag_list_to_dict
from utils.general import check_delete


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
def remove_transfer_servers(
    session, region, resource_arns: list[str]
) -> DeleteResponse:
    transfer = session.client('transfer', region_name=region)

    response = DeleteResponse()

    for server_arn in resource_arns:
        server_id = server_arn.split('/')[-1]

        try:
            transfer.delete_server(ServerId=server_id)
            response.successful.append(server_arn)
        except botocore.exceptions.ClientError as e:
            error_code = e.response['Error']['Code']
            response.failures[error_code].append(server_arn)

    return response
