from lib.utils import check_delete
from registry.decorator import register_query_function, register_terminate_function
from utils.aws import boto3_paginate, boto3_tag_list_to_dict


@register_query_function('DocDB::DBInstance')
def query_docdb_instances(session, region) -> list[str]:
    docdb = session.client('docdb', region_name=region)
    resource_arns = []

    instances = list(
        boto3_paginate(
            docdb,
            'describe_db_instances',
            search='DBInstances[].[DBInstanceArn,Engine]',
        )
    )

    for instance_arn, engine in instances:
        instance_tags = docdb.list_tags_for_resource(ResourceName=instance_arn)[
            'TagList'
        ]

        if check_delete(boto3_tag_list_to_dict(instance_tags)) and engine == 'docdb':
            resource_arns.append(instance_arn)

    return resource_arns


@register_terminate_function('DocDB::DBInstance')
def remove_docdb_instances(session, region, resource_arns: list[str]) -> None:
    docdb = session.client('docdb', region_name=region)

    for db_arn in resource_arns:
        instance_id = db_arn.split(':')[-1]

        docdb.delete_db_instance(
            DBInstanceIdentifier=instance_id,
            SkipFinalSnapshot=True,
            DeleteAutomatedBackups=True,
        )
        docdb.get_waiter('db_instance_deleted').wait(DBInstanceIdentifier=instance_id)


@register_query_function('DocDB::DBCluster')
def query_docdb_clusters(session, region) -> list[str]:
    docdb = session.client('docdb', region_name=region)
    resource_arns = []

    cluster = list(
        boto3_paginate(
            docdb,
            'describe_db_clusters',
            search='DBClusters[].[DBClusterArn,Engine]',
        )
    )

    for cluster_arn, engine in cluster:
        cluster_tags = docdb.list_tags_for_resource(ResourceName=cluster_arn)['TagList']

        if check_delete(boto3_tag_list_to_dict(cluster_tags)) and engine == 'docdb':
            resource_arns.append(cluster_arn)

    return resource_arns


@register_terminate_function('DocDB::DBCluster')
def remove_docdb_clusters(session, region, resource_arns: list[str]) -> None:
    docdb = session.client('docdb', region_name=region)

    for cluster_arn in resource_arns:
        cluster_id = cluster_arn.split(':')[-1]
        docdb.delete_db_cluster(
            DBClusterIdentifier=cluster_id,
            SkipFinalSnapshot=True,
            DeleteAutomatedBackups=True,
        )
        docdb.get_waiter('db_cluster_deleted').wait(
            DBClusterIdentifier=cluster_id, WaiterConfig={'Delay': 10}
        )
