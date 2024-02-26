import botocore.exceptions

from registry import DeleteResponse
from registry.decorator import register_query_function, register_terminate_function
from utils.aws import boto3_paginate, get_account_id
from utils.general import check_delete


@register_query_function('SQS::Queue')
def query_sqs_queues(session, region) -> list[str]:
    account_id = get_account_id(session)
    sqs = session.client('sqs', region_name=region)
    resource_arns = []

    queues = [
        queue_url
        for queue_url in boto3_paginate(
            sqs,
            'list_queues',
            search='QueueUrls[]',
        )
        if queue_url is not None
    ]

    for queue_url in queues:
        queue_arn = f"arn:aws:sqs:{region}:{account_id}:{queue_url.split('/')[-1]}"
        try:
            queue_tags = sqs.list_queue_tags(QueueUrl=queue_url).get('Tags', {})
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'AWS.SimpleQueueService.NonExistentQueue':
                continue
            raise e

        if check_delete(queue_tags):
            resource_arns.append(queue_arn)

    return resource_arns


@register_terminate_function('SQS::Queue')
def remove_sqs_queues(session, region, resource_arns: list[str]) -> DeleteResponse:
    sqs = session.client('sqs', region_name=region)

    response = DeleteResponse()

    for queue_arn in resource_arns:
        account_id = queue_arn.split(':')[4]
        region = queue_arn.split(':')[3]
        queue_name = queue_arn.split(':')[-1]
        queue_url = f'https://sqs.{region}.amazonaws.com/{account_id}/{queue_name}'

        try:
            sqs.delete_queue(QueueUrl=queue_url)
            response.successful.append(queue_arn)
        except botocore.exceptions.ClientError as e:
            error_code = e.response['Error']['Code']
            response.failures[error_code].append(queue_arn)

    return response
