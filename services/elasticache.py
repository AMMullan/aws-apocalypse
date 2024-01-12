from config import CONFIG
from lib.utils import boto3_tag_list_to_dict, check_delete, paginate_and_search
from registry.decorator import register_resource


@register_resource('ElastiCache::CacheCluster')
def remove_elasticache_clusters(session, region) -> list[str]:
    elasticache = session.client('elasticache', region_name=region)
    removed_resources = []

    clusters = list(
        paginate_and_search(
            elasticache,
            'describe_cache_clusters',
            PaginationConfig={'PageSize': 100},
            SearchPath='CacheClusters[].[ARN,CacheClusterId]',
        )
    )
    for cluster_arn, cluster_id in clusters:
        try:
            cluster_tags = elasticache.list_tags_for_resource(ResourceName=cluster_arn)[
                'TagList'
            ]
        except elasticache.exceptions.CacheClusterNotFoundFault:
            continue

        if check_delete(boto3_tag_list_to_dict(cluster_tags)):
            if not CONFIG['LIST_ONLY']:
                elasticache.delete_cache_cluster(CacheClusterId=cluster_id)

            removed_resources.append(cluster_arn)

    return removed_resources


@register_resource('ElastiCache::ServerlessCache')
def remove_elasticache_serverless_clusters(session, region) -> list[str]:
    elasticache = session.client('elasticache', region_name=region)
    removed_resources = []

    clusters = list(
        paginate_and_search(
            elasticache,
            'describe_serverless_caches',
            PaginationConfig={'PageSize': 100},
            SearchPath='ServerlessCaches[].[ARN,ServerlessCacheName]',
        )
    )
    for cluster_arn, cluster_name in clusters:
        try:
            cluster_tags = elasticache.list_tags_for_resource(ResourceName=cluster_arn)[
                'TagList'
            ]
        except elasticache.exceptions.CacheClusterNotFoundFault:
            continue

        if check_delete(boto3_tag_list_to_dict(cluster_tags)):
            if not CONFIG['LIST_ONLY']:
                elasticache.delete_serverless_cache(ServerlessCacheName=cluster_name)

            removed_resources.append(cluster_arn)

    return removed_resources
