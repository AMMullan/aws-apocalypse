from config import CONFIG
from lib.utils import boto3_tag_list_to_dict, check_delete, paginate_and_search
from registry.decorator import register_resource


@register_resource('RDS::Instance')
def remove_rds_instances(session, region) -> list[str]:
    rds = session.client('rds', region_name=region)
    removed_items = []

    instances = list(
        paginate_and_search(
            rds,
            'describe_db_instances',
            PaginationConfig={'PageSize': 100},
            SearchPath='DBInstances[].[DBInstanceIdentifier,DBInstanceArn,TagList]',
        )
    )

    for instance_id, instance_arn, instance_tags in instances:
        if check_delete(boto3_tag_list_to_dict(instance_tags)):
            if not CONFIG['LIST_ONLY']:
                rds.delete_db_instance(
                    DBInstanceIdentifier=instance_id,
                    SkipFinalSnapshot=True,
                    DeleteAutomatedBackups=True,
                )
                rds.get_waiter('db_instance_deleted').wait(
                    DBInstanceIdentifier=instance_id
                )

            removed_items.append(instance_arn)

    return removed_items


@register_resource('RDS::Cluster')
def remove_rds_clusters(session, region) -> list[str]:
    rds = session.client('rds', region_name=region)
    removed_items = []

    cluster = list(
        paginate_and_search(
            rds,
            'describe_db_clusters',
            PaginationConfig={'PageSize': 100},
            SearchPath='DBClusters[].[DBClusterIdentifier,DBClusterArn,TagList]',
        )
    )

    for cluster_id, cluster_arn, cluster_tags in cluster:
        if check_delete(boto3_tag_list_to_dict(cluster_tags)):
            if not CONFIG['LIST_ONLY']:
                rds.delete_db_cluster(
                    DBClusterIdentifier=cluster_id,
                    SkipFinalSnapshot=True,
                    DeleteAutomatedBackups=True,
                )
                rds.get_waiter('db_cluster_deleted').wait(
                    DBClusterIdentifier=cluster_id, WaiterConfig={'Delay': 10}
                )

            removed_items.append(cluster_arn)

    return removed_items
