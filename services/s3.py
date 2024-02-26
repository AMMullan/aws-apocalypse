import botocore.exceptions

from registry import DeleteResponse
from registry.decorator import register_query_function, register_terminate_function
from utils.aws import boto3_tag_list_to_dict
from utils.general import check_delete


def get_bucket_region(s3, bucket_name):
    return s3.head_bucket(Bucket=bucket_name)['ResponseMetadata']['HTTPHeaders'][
        'x-amz-bucket-region'
    ]


@register_query_function('S3::Bucket')
def query_s3_buckets(session, region) -> list[str]:
    s3 = session.client('s3')

    resource_arns = []

    buckets = [
        bucket
        for bucket, region_name in {
            bucket['Name']: get_bucket_region(s3, bucket['Name'])
            for bucket in s3.list_buckets()['Buckets']
        }.items()
        if region_name == region
    ]

    # Now use a boto3 resource object, quicker for this service.
    s3 = session.resource('s3')
    for bucket_name in buckets:
        bucket = s3.Bucket(bucket_name)
        try:
            bucket_tags = bucket.Tagging().tag_set
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchTagSet':
                bucket_tags = {}
            else:
                raise

        if check_delete(boto3_tag_list_to_dict(bucket_tags)):
            resource_arns.append(f'arn:aws:s3:::{bucket_name}')

    return resource_arns


@register_terminate_function('S3::Bucket')
def remove_s3_buckets(session, region, resource_arns: list[str]) -> DeleteResponse:
    s3 = session.resource('s3')

    response = DeleteResponse()

    for bucket_arn in resource_arns:
        bucket_name = bucket_arn.split(':')[-1]

        try:
            bucket = s3.Bucket(bucket_name)
            bucket.Policy().delete()
            bucket.object_versions.all().delete()
            bucket.delete()
            response.successful.append(bucket_arn)
        except botocore.exceptions.ClientError as e:
            error_code = e.response['Error']['Code']
            response.failures[error_code].append(bucket_arn)

    return response
