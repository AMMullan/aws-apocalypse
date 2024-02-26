import botocore.exceptions

from registry import DeleteResponse
from registry.decorator import register_query_function, register_terminate_function
from utils.aws import boto3_paginate, boto3_tag_list_to_dict
from utils.general import check_delete


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
def remove_sns_topics(session, region, resource_arns: list[str]) -> DeleteResponse:
    sns = session.client('sns', region_name=region)

    response = DeleteResponse()

    for topic_arn in resource_arns:
        try:
            sns.delete_topic(TopicArn=topic_arn)
            response.successful.append(topic_arn)
        except botocore.exceptions.ClientError as e:
            error_code = e.response['Error']['Code']
            response.failures[error_code].append(topic_arn)

    return response
