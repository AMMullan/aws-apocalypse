from lib.utils import (
    check_delete,
    get_account_id,
    paginate_and_search,
)
from registry.decorator import register_query_function, register_terminate_function


@register_query_function('SQS::Queue')
def query_sqs_queues(session, region) -> list[str]:
    account_id = get_account_id(session)
    sqs = session.client('sqs', region_name=region)
    resource_arns = []

    queues = [
        queue_url
        for queue_url in paginate_and_search(
            sqs,
            'list_queues',
            PaginationConfig={'PageSize': 500},
            SearchPath='QueueUrls[]',
        )
        if queue_url is not None
    ]

    for queue_url in queues:
        queue_arn = f"arn:aws:sqs:{region}:{account_id}:{queue_url.split('/')[-1]}"
        try:
            queue_tags = sqs.list_queue_tags(QueueUrl=queue_url).get('Tags', {})
        except Exception as e:
            if e.response['Error']['Code'] == 'AWS.SimpleQueueService.NonExistentQueue':
                continue
            raise e

        if check_delete(queue_tags):
            resource_arns.append(queue_arn)

    return resource_arns


@register_terminate_function('SQS::Queue')
def remove_sqs_queues(session, region, resource_arns: list[str]) -> None:
    sqs = session.client('sqs', region_name=region)

    for queue_arn in resource_arns:
        account_id = queue_arn.split(':')[4]
        region = queue_arn.split(':')[3]
        queue_name = queue_arn.split(':')[-1]

        queue_url = f'https://sqs.{region}.amazonaws.com/{account_id}/{queue_name}'

        sqs.delete_queue(QueueUrl=queue_url)
