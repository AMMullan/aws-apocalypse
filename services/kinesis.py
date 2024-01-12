from config import CONFIG
from lib.utils import boto3_tag_list_to_dict, check_delete, paginate_and_search
from registry.decorator import register_resource


@register_resource('Kinesis:Stream')
def remove_kinesis_datastreams(session, region) -> list[str]:
    kinesis = session.client('kinesis', region_name=region)
    removed_resources = []

    instances = list(
        paginate_and_search(
            kinesis,
            'list_streams',
            PaginationConfig={'PageSize': 100},
            SearchPath='StreamSummaries[].[StreamARN,StreamName]',
        )
    )

    for stream_arn, stream_name in instances:
        stream_tags = kinesis.list_tags_for_stream(StreamName=stream_name)['Tags']

        if check_delete(boto3_tag_list_to_dict(stream_tags)):
            if not CONFIG['LIST_ONLY']:
                kinesis.delete_stream(
                    EnforceConsumerDeletion=True, StreamARN=stream_arn
                )
                kinesis.get_waiter('stream_not_exists').wait(StreamARN=stream_arn)

            removed_resources.append(stream_arn)

    return removed_resources
