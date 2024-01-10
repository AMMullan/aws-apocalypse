from config import CONFIG
from lib.utils import (
    check_delete,
    get_account_id,
    paginate_and_search,
)
from registry.decorator import register_resource


@register_resource('SQS::Queue')
def remove_sqs_queues(session, region) -> list[str]:
    account_id = get_account_id(session)
    sqs = session.client('sqs', region_name=region)
    removed_resources = []

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
            if not CONFIG['LIST_ONLY']:
                sqs.delete_queue(QueueUrl=queue_url)

            removed_resources.append(queue_arn)

    return removed_resources
