from lib.utils import boto3_tag_list_to_dict, check_delete, paginate_and_search
from registry.decorator import register_query_function, register_terminate_function


@register_query_function('ECR::Repository')
def query_ecr_repositories(session, region) -> list[str]:
    ecr = session.client('ecr', region_name=region)
    resource_arns = []

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
            resource_arns.append(repo_arn)

    return resource_arns


@register_terminate_function('ECR::Repository')
def remove_ecr_repositories(session, region, resource_arns: list[str]) -> None:
    ecr = session.client('ecr', region_name=region)

    for repo_arn in resource_arns:
        ecr.delete_repository(repositoryArn=repo_arn, force=True)
