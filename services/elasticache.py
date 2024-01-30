from lib.utils import check_delete
from registry.decorator import register_query_function, register_terminate_function
from utils.aws import boto3_paginate, boto3_tag_list_to_dict


@register_query_function('ElastiCache::CacheCluster')
def query_elasticache_clusters(session, region) -> list[str]:
    elasticache = session.client('elasticache', region_name=region)
    resource_arns = []

    clusters = list(
        boto3_paginate(
            elasticache,
            'describe_cache_clusters',
            search='CacheClusters[].[ARN,CacheClusterId]',
        )
    )
    for cluster_arn, cluster_id in clusters:
        try:
            cluster_tags = elasticache.list_tags_for_resource(ResourceName=cluster_arn)[
                'TagList'
            ]
        except elasticache.exceptions.CacheClusterNotFoundFault:
            # This can happen if the script is run more than once a day
            continue

        if check_delete(boto3_tag_list_to_dict(cluster_tags)):
            resource_arns.append(cluster_arn)

    return resource_arns


@register_terminate_function('ElastiCache::CacheCluster')
def remove_elasticache_clusters(session, region, resource_arns: list[str]) -> None:
    elasticache = session.client('elasticache', region_name=region)

    for cluster_arn in resource_arns:
        cluster_id = cluster_arn.split(':')[-1]
        elasticache.delete_cache_cluster(CacheClusterId=cluster_id)


@register_query_function('ElastiCache::ServerlessCache')
def query_elasticache_serverless_clusters(session, region) -> list[str]:
    elasticache = session.client('elasticache', region_name=region)
    resource_arns = []

    clusters = list(
        boto3_paginate(
            elasticache,
            'describe_serverless_caches',
            search='ServerlessCaches[].[ARN,ServerlessCacheName]',
        )
    )
    for (cluster_arn,) in clusters:
        try:
            cluster_tags = elasticache.list_tags_for_resource(ResourceName=cluster_arn)[
                'TagList'
            ]
        except elasticache.exceptions.CacheClusterNotFoundFault:
            continue

        if check_delete(boto3_tag_list_to_dict(cluster_tags)):
            resource_arns.append(cluster_arn)

    return resource_arns


@register_terminate_function('ElastiCache::ServerlessCache')
def remove_elasticache_serverless_clusters(
    session, region, resource_arns: list[str]
) -> None:
    elasticache = session.client('elasticache', region_name=region)

    for cluster_arn in resource_arns:
        cluster_name = cluster_arn.split(':')[-1]
        elasticache.delete_serverless_cache(ServerlessCacheName=cluster_name)
