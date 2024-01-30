from lib.utils import check_delete
from registry.decorator import register_query_function, register_terminate_function
from utils.aws import boto3_paginate, boto3_tag_list_to_dict


@register_query_function('RDS::Instance')
def query_rds_instances(session, region) -> list[str]:
    rds = session.client('rds', region_name=region)
    instances = list(
        boto3_paginate(
            rds,
            'describe_db_instances',
            search='DBInstances[].[DBInstanceArn,TagList,Engine]',
        )
    )

    return [
        instance_arn
        for instance_arn, instance_tags, engine in instances
        if check_delete(boto3_tag_list_to_dict(instance_tags))
        and engine not in ['neptune', 'docdb']
    ]


@register_terminate_function('RDS::Instance')
def remove_rds_instances(session, region, resource_arns: list[str]) -> None:
    rds = session.client('rds', region_name=region)

    for db_arn in resource_arns:
        instance_id = db_arn.split(':')[-1]
        rds.delete_db_instance(
            DBInstanceIdentifier=instance_id,
            SkipFinalSnapshot=True,
            DeleteAutomatedBackups=True,
        )
        rds.get_waiter('db_instance_deleted').wait(DBInstanceIdentifier=instance_id)


@register_query_function('RDS::Cluster')
def query_rds_clusters(session, region) -> list[str]:
    rds = session.client('rds', region_name=region)
    cluster = list(
        boto3_paginate(
            rds,
            'describe_db_clusters',
            search='DBClusters[].[DBClusterArn,TagList,Engine]',
        )
    )

    return [
        cluster_arn
        for cluster_arn, cluster_tags, engine in cluster
        if check_delete(boto3_tag_list_to_dict(cluster_tags))
        and engine not in ['neptune', 'docdb']
    ]


@register_terminate_function('RDS::Cluster')
def remove_rds_clusters(session, region, resource_arns: list[str]) -> None:
    rds = session.client('rds', region_name=region)

    for db_arn in resource_arns:
        cluster_id = db_arn.split(':')[-1]
        rds.delete_db_cluster(
            DBClusterIdentifier=cluster_id,
            SkipFinalSnapshot=True,
            DeleteAutomatedBackups=True,
        )
        rds.get_waiter('db_cluster_deleted').wait(
            DBClusterIdentifier=cluster_id, WaiterConfig={'Delay': 10}
        )
