from config import CONFIG
from lib.utils import boto3_tag_list_to_dict, check_delete, paginate_and_search
from registry.decorator import register_resource


@register_resource('ECR::Repository')
def remove_ecr_repositories(session, region) -> list[str]:
    ecr = session.client('ecr', region_name=region)
    removed_resources = []

    repositories = list(
        paginate_and_search(
            ecr,
            'describe_repositories',
            PaginationConfig={'PageSize': 500},
            SearchPath='repositories[].repositoryArn',
        )
    )

    for repo_arn in repositories:
        repo_tags = ecr.list_tags_for_resource(resourceArn=repo_arn)['tags']

        if check_delete(boto3_tag_list_to_dict(repo_tags)):
            if not CONFIG['LIST_ONLY']:
                ecr.delete_repository(repositoryArn=repo_arn, force=True)

            removed_resources.append(repo_arn)

    return removed_resources
