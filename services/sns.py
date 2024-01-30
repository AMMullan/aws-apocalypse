from utils.general import check_delete
from registry.decorator import register_query_function, register_terminate_function
from utils.aws import boto3_paginate, boto3_tag_list_to_dict


@register_query_function('SNS::Topic')
def query_sns_topics(session, region) -> list[str]:
    sns = session.client('sns', region_name=region)
    resource_arns = []

    topics = list(
        boto3_paginate(
            sns,
            'list_topics',
            search='Topics[].TopicArn',
        )
    )

    for topic_arn in topics:
        topic_tags = sns.list_tags_for_resource(ResourceArn=topic_arn)['Tags']

        if check_delete(boto3_tag_list_to_dict(topic_tags)):
            resource_arns.append(topic_arn)

    return resource_arns


@register_terminate_function('SNS::Topic')
def remove_sns_topics(session, region, resource_arns: list[str]) -> None:
    sns = session.client('sns', region_name=region)

    for topic_arn in resource_arns:
        sns.delete_topic(TopicArn=topic_arn)
