from config import CONFIG
from lib.utils import boto3_tag_list_to_dict, check_delete
from registry.decorator import register_resource


@register_resource('CloudTrail::Trail')
def remove_cloudtrail_trails(session, region) -> list[str]:
    cloudtrail = session.client('cloudtrail', region_name=region)
    removed_resources = []

    trails = [
        [trail['Name'], trail['TrailARN']]
        for trail in cloudtrail.describe_trails()['trailList']
        if not trail['IsOrganizationTrail'] and trail['HomeRegion'] == region
    ]

    for trail_name, trail_arn in trails:
        trail_tags = cloudtrail.list_tags(ResourceIdList=[trail_arn])[
            'ResourceTagList'
        ][0]['TagsList']

        if check_delete(boto3_tag_list_to_dict(trail_tags)):
            if not CONFIG['LIST_ONLY']:
                cloudtrail.delete_trail(Name=trail_name)

            removed_resources.append(trail_arn)

    return removed_resources
