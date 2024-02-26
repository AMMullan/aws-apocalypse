import botocore.exceptions

from registry import DeleteResponse
from registry.decorator import register_query_function, register_terminate_function
from utils.aws import boto3_paginate, boto3_tag_list_to_dict
from utils.general import check_delete


@register_query_function('Kinesis:Stream')
def query_kinesis_datastreams(session, region) -> list[str]:
    kinesis = session.client('kinesis', region_name=region)
    resource_arns = []

    instances = list(
        boto3_paginate(
            kinesis,
            'list_streams',
            search='StreamSummaries[].[StreamARN,StreamName]',
        )
    )

    for stream_arn, stream_name in instances:
        stream_tags = kinesis.list_tags_for_stream(StreamName=stream_name)['Tags']

        if check_delete(boto3_tag_list_to_dict(stream_tags)):
            resource_arns.append(stream_arn)

    return resource_arns


@register_terminate_function('Kinesis:Stream')
def remove_kinesis_datastreams(
    session, region, resource_arns: list[str]
) -> DeleteResponse:
    kinesis = session.client('kinesis', region_name=region)

    response = DeleteResponse()

    for stream_arn in resource_arns:
        try:
            kinesis.delete_stream(EnforceConsumerDeletion=True, StreamARN=stream_arn)
            kinesis.get_waiter('stream_not_exists').wait(StreamARN=stream_arn)
            response.successful.append(stream_arn)
        except botocore.exceptions.ClientError as e:
            error_code = e.response['Error']['Code']
            response.failures[error_code].append(stream_arn)

    return response
