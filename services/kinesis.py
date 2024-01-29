from lib.utils import boto3_tag_list_to_dict, check_delete, paginate_and_search
from registry.decorator import register_query_function, register_terminate_function


@register_query_function('Kinesis:Stream')
def query_kinesis_datastreams(session, region) -> list[str]:
    kinesis = session.client('kinesis', region_name=region)
    resource_arns = []

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
            resource_arns.append(stream_arn)

    return resource_arns


@register_terminate_function('Kinesis:Stream')
def remove_kinesis_datastreams(session, region, resource_arns: list[str]) -> None:
    kinesis = session.client('kinesis', region_name=region)

    for stream_arn in resource_arns:
        kinesis.delete_stream(EnforceConsumerDeletion=True, StreamARN=stream_arn)
        kinesis.get_waiter('stream_not_exists').wait(StreamARN=stream_arn)
