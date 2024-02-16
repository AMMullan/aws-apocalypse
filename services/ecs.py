import time

from registry.decorator import register_query_function, register_terminate_function
from utils.aws import boto3_paginate, boto3_tag_list_to_dict
from utils.general import batch, check_delete


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
def remove_ecs_clusters(session, region, resource_arns: list[str]) -> None:
    ecs = session.client('ecs', region_name=region)

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

        ecs.delete_cluster(cluster=cluster_arn)


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
def remove_ecs_task_definitions(session, region, resource_arns: list[str]) -> None:
    ecs = session.client('ecs', region_name=region)
    for task_batch in batch(resource_arns, 10):
        # Deregister Task Definition First
        for task in task_batch:
            ecs.deregister_task_definition(taskDefinition=task)

        # Then Delete It
        ecs.delete_task_definitions(taskDefinitions=task_batch)
