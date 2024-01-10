from config import CONFIG
from lib.utils import boto3_tag_list_to_dict, check_delete, paginate_and_search
from registry.decorator import register_resource


@register_resource('DynamoDB::Table')
def remove_ddb_tables(session, region) -> list[str]:
    ddb = session.client('dynamodb', region_name=region)
    removed_resources = []

    tables = list(
        paginate_and_search(
            ddb,
            'list_tables',
            PaginationConfig={'PageSize': 500},
            SearchPath='TableNames[]',
        )
    )

    for table_name in tables:
        table_arn = ddb.describe_table(TableName=table_name)['Table']['TableArn']
        table_tags = ddb.list_tags_of_resource(ResourceArn=table_arn)['Tags']

        if check_delete(boto3_tag_list_to_dict(table_tags)):
            if not CONFIG['LIST_ONLY']:
                ddb.delete_table(TableName=table_name)

            removed_resources.append(table_arn)

    return removed_resources
