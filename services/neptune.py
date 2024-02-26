import botocore.exceptions

from registry import DeleteResponse
from registry.decorator import register_query_function, register_terminate_function
from utils.aws import boto3_paginate, boto3_tag_list_to_dict
from utils.general import check_delete


@register_query_function('Neptune::DBInstance')
def query_neptune_instances(session, region) -> list[str]:
    neptune = session.client('neptune', region_name=region)
    resource_arns = []

    instances = list(
        boto3_paginate(
            neptune,
            'describe_db_instances',
            search='DBInstances[].[DBInstanceArn,Engine]',
        )
    )

    for instance_arn, engine in instances:
        instance_tags = neptune.list_tags_for_resource(ResourceName=instance_arn)[
            'TagList'
        ]

        if check_delete(boto3_tag_list_to_dict(instance_tags)) and engine == 'neptune':
            resource_arns.append(instance_arn)

    return resource_arns


@register_terminate_function('Neptune::DBInstance')
def remove_neptune_instances(
    session, region, resource_arns: list[str]
) -> DeleteResponse:
    neptune = session.client('neptune', region_name=region)

    response = DeleteResponse()

    for db_arn in resource_arns:
        instance_id = db_arn.split('/')[-1]

        try:
            neptune.delete_db_instance(
                DBInstanceIdentifier=instance_id,
                SkipFinalSnapshot=True,
                DeleteAutomatedBackups=True,
            )
            neptune.get_waiter('db_instance_deleted').wait(
                DBInstanceIdentifier=instance_id
            )
            response.successful.append(db_arn)
        except botocore.exceptions.ClientError as e:
            error_code = e.response['Error']['Code']
            response.failures[error_code].append(db_arn)

    return response


@register_query_function('Neptune::DBCluster')
def query_neptune_clusters(session, region) -> list[str]:
    neptune = session.client('neptune', region_name=region)
    resource_arns = []

    cluster = list(
        boto3_paginate(
            neptune,
            'describe_db_clusters',
            search='DBClusters[].[DBClusterArn,Engine]',
        )
    )

    for cluster_arn, engine in cluster:
        cluster_tags = neptune.list_tags_for_resource(ResourceName=cluster_arn)[
            'TagList'
        ]

        if check_delete(boto3_tag_list_to_dict(cluster_tags)) and engine == 'neptune':
            resource_arns.append(cluster_arn)

    return resource_arns


@register_terminate_function('Neptune::DBCluster')
def remove_neptune_clusters(
    session, region, resource_arns: list[str]
) -> DeleteResponse:
    neptune = session.client('neptune', region_name=region)

    response = DeleteResponse()

    for cluster_arn in resource_arns:
        cluster_id = cluster_arn.split('/')[-1]

        try:
            neptune.delete_db_cluster(
                DBClusterIdentifier=cluster_id,
                SkipFinalSnapshot=True,
                DeleteAutomatedBackups=True,
            )
            neptune.get_waiter('db_cluster_deleted').wait(
                DBClusterIdentifier=cluster_id, WaiterConfig={'Delay': 10}
            )
            response.successful.append(cluster_arn)
        except botocore.exceptions.ClientError as e:
            error_code = e.response['Error']['Code']
            response.failures[error_code].append(cluster_arn)

    return response
