from utils.general import check_delete
from registry.decorator import register_query_function, register_terminate_function
from utils.aws import boto3_paginate, boto3_tag_list_to_dict


@register_query_function('DynamoDB::Table')
def query_ddb_tables(session, region) -> list[str]:
    ddb = session.client('dynamodb', region_name=region)
    resource_arns = []

    tables = list(
        boto3_paginate(
            ddb,
            'list_tables',
            search='TableNames[]',
        )
    )

    for table_name in tables:
        table_arn = ddb.describe_table(TableName=table_name)['Table']['TableArn']
        table_tags = ddb.list_tags_of_resource(ResourceArn=table_arn)['Tags']

        if check_delete(boto3_tag_list_to_dict(table_tags)):
            resource_arns.append(table_arn)

    return resource_arns


@register_terminate_function('DynamoDB::Table')
def remove_ddb_tables(session, region, resource_arns: list[str]) -> None:
    ddb = session.client('dynamodb', region_name=region)

    for table_arn in resource_arns:
        table_name = table_arn.split('/')[-1]
        ddb.delete_table(TableName=table_name)
