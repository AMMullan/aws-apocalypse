from config import CONFIG
from lib.utils import boto3_tag_list_to_dict, check_delete, paginate_and_search
from registry.decorator import register_resource


@register_resource('SNS::Topic')
def remove_sns_topics(session, region) -> list[str]:
    sns = session.client('sns', region_name=region)
    removed_resources = []

    topics = list(
        paginate_and_search(
            sns,
            'list_topics',
            SearchPath='Topics[].TopicArn',
        )
    )

    for topic_arn in topics:
        topic_tags = sns.list_tags_for_resource(ResourceArn=topic_arn)['Tags']

        if check_delete(boto3_tag_list_to_dict(topic_tags)):
            if not CONFIG['LIST_ONLY']:
                sns.delete_topic(TopicArn=topic_arn)

            removed_resources.append(topic_arn)

    return removed_resources
