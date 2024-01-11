from config import CONFIG
from lib.utils import boto3_tag_list_to_dict, check_delete, paginate_and_search
from registry.decorator import register_resource


@register_resource('DocDB::DBInstance')
def remove_docdb_instances(session, region) -> list[str]:
    docdb = session.client('docdb', region_name=region)
    removed_items = []

    instances = list(
        paginate_and_search(
            docdb,
            'describe_db_instances',
            PaginationConfig={'PageSize': 100},
            SearchPath='DBInstances[].[DBInstanceIdentifier,DBInstanceArn]',
        )
    )

    for instance_id, instance_arn in instances:
        instance_tags = docdb.list_tags_for_resource(ResourceName=instance_arn)[
            'TagList'
        ]

        if check_delete(boto3_tag_list_to_dict(instance_tags)):
            if not CONFIG['LIST_ONLY']:
                docdb.delete_db_instance(
                    DBInstanceIdentifier=instance_id,
                    SkipFinalSnapshot=True,
                    DeleteAutomatedBackups=True,
                )
                docdb.get_waiter('db_instance_deleted').wait(
                    DBInstanceIdentifier=instance_id
                )

            removed_items.append(instance_arn)

    return removed_items


@register_resource('DocDB::DBCluster')
def remove_docdb_clusters(session, region) -> list[str]:
    docdb = session.client('docdb', region_name=region)
    removed_items = []

    cluster = list(
        paginate_and_search(
            docdb,
            'describe_db_clusters',
            PaginationConfig={'PageSize': 100},
            SearchPath='DBClusters[].[DBClusterIdentifier,DBClusterArn]',
        )
    )

    for cluster_id, cluster_arn in cluster:
        cluster_tags = docdb.list_tags_for_resource(ResourceName=cluster_arn)['TagList']

        if check_delete(boto3_tag_list_to_dict(cluster_tags)):
            if not CONFIG['LIST_ONLY']:
                docdb.delete_db_cluster(
                    DBClusterIdentifier=cluster_id,
                    SkipFinalSnapshot=True,
                    DeleteAutomatedBackups=True,
                )
                docdb.get_waiter('db_cluster_deleted').wait(
                    DBClusterIdentifier=cluster_id, WaiterConfig={'Delay': 10}
                )

            removed_items.append(cluster_arn)

    return removed_items
