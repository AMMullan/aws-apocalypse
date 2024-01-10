import time

from config import CONFIG
from lib.utils import boto3_tag_list_to_dict, check_delete, paginate_and_search
from registry.decorator import register_resource


# Would we want/need to remove services independent ?
def remove_ecs_services(session, region) -> list[str]:
    ...


@register_resource('ECS::Cluster')
def remove_ecs_clusters(session, region) -> list[str]:
    ecs = session.client('ecs', region_name=region)
    removed_resources = []

    clusters = list(
        paginate_and_search(
            ecs,
            'list_clusters',
            PaginationConfig={'PageSize': 100},
            SearchPath='clusterArns[]',
        )
    )
    for cluster_arn in clusters:
        tags = ecs.list_tags_for_resource(resourceArn=cluster_arn)['tags']

        if not check_delete(boto3_tag_list_to_dict(tags)):
            continue

        if not CONFIG['LIST_ONLY']:
            services = list(
                paginate_and_search(
                    ecs,
                    'list_services',
                    cluster=cluster_arn,
                    PaginationConfig={'PageSize': 100},
                    SearchPath='serviceArns[]',
                )
            )
            for service_arn in services:
                ecs.delete_service(cluster=cluster_arn, service=service_arn, force=True)

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

        removed_resources.append(cluster_arn)

    return removed_resources
