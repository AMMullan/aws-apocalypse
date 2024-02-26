import time

import botocore.exceptions

from registry import DeleteResponse
from registry.decorator import register_query_function, register_terminate_function
from utils.aws import boto3_paginate, boto3_tag_list_to_dict
from utils.general import check_delete


@register_query_function('ECS::Cluster')
def query_ecs_clusters(session, region) -> list[str]:
    ecs = session.client('ecs', region_name=region)
    resource_arns = []

    clusters = list(
        boto3_paginate(
            ecs,
            'list_clusters',
            search='clusterArns[]',
        )
    )
    for cluster_arn in clusters:
        tags = ecs.list_tags_for_resource(resourceArn=cluster_arn)['tags']

        if not check_delete(boto3_tag_list_to_dict(tags)):
            continue

        resource_arns.append(cluster_arn)

    return resource_arns


@register_terminate_function('ECS::Cluster')
def remove_ecs_clusters(session, region, resource_arns: list[str]) -> DeleteResponse:
    ecs = session.client('ecs', region_name=region)

    response = DeleteResponse()

    for cluster_arn in resource_arns:
        services = list(
            boto3_paginate(
                ecs,
                'list_services',
                cluster=cluster_arn,
                search='serviceArns[]',
            )
        )
        for service_arn in services:
            ecs.delete_service(cluster=cluster_arn, service=service_arn, force=True)

        if services:
            # Monitor service removal
            while True:
                print(f'Draining ECS Cluster (may take a few minutes): {cluster_arn}')
                service_status = ecs.describe_services(
                    cluster=cluster_arn, services=services
                )['services']
                if [
                    service['serviceArn']
                    for service in service_status
                    if service['status'] in ['DRAINING']
                ]:
                    time.sleep(5)
                else:
                    break

        try:
            ecs.delete_cluster(cluster=cluster_arn)
            response.successful.append(cluster_arn)
        except botocore.exceptions.ClientError as e:
            error_code = e.response['Error']['Code']
            response.failures[error_code].append(cluster_arn)

    return response


@register_query_function('ECS::TaskDefinition')
def query_ecs_task_definitions(session, region) -> list[str]:
    ecs = session.client('ecs', region_name=region)

    resource_arns = []

    definitions = boto3_paginate(
        ecs, 'list_task_definitions', search='taskDefinitionArns[]'
    )
    for def_arn in definitions:
        definition = ecs.describe_task_definition(
            taskDefinition=def_arn, include=['TAGS']
        )
        tags = definition['tags']
        if not check_delete(boto3_tag_list_to_dict(tags)):
            continue

        resource_arns.append(def_arn)

    return resource_arns


@register_terminate_function('ECS::TaskDefinition')
def remove_ecs_task_definitions(
    session, region, resource_arns: list[str]
) -> DeleteResponse:
    ecs = session.client('ecs', region_name=region)

    response = DeleteResponse()

    for task_arn in resource_arns:
        # Deregister Task Definition First
        ecs.deregister_task_definition(taskDefinition=task_arn)

        # Then Delete It
        try:
            ecs.delete_task_definitions(taskDefinitions=[task_arn])
            response.successful.append(task_arn)
        except botocore.exceptions.ClientError as e:
            error_code = e.response['Error']['Code']
            response.failures[error_code].append(task_arn)

    return response
