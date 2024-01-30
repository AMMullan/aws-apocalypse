from lib.utils import check_delete
from registry.decorator import register_query_function, register_terminate_function
from utils.aws import boto3_tag_list_to_dict


@register_query_function('CloudTrail::Trail')
def query_cloudtrail_trails(session, region) -> list[str]:
    cloudtrail = session.client('cloudtrail', region_name=region)

    trails = [
        trail['TrailARN']
        for trail in cloudtrail.describe_trails()['trailList']
        if not trail['IsOrganizationTrail'] and trail['HomeRegion'] == region
    ]

    return [
        trail_arn
        for trail_arn in trails
        if check_delete(
            boto3_tag_list_to_dict(
                cloudtrail.list_tags(ResourceIdList=[trail_arn])['ResourceTagList'][0][
                    'TagsList'
                ]
            )
        )
    ]


@register_terminate_function('CloudTrail::Trail')
def remove_cloudtrail_trails(session, region, resource_arns: list[str]) -> None:
    cloudtrail = session.client('cloudtrail', region_name=region)

    for trail_arn in resource_arns:
        cloudtrail.delete_trail(Name=trail_arn.split('/')[-1])
