from config import CONFIG
from lib.utils import boto3_tag_list_to_dict, check_delete
from registry.decorator import register_resource


def get_bucket_region(s3, bucket_name):
    return s3.head_bucket(Bucket=bucket_name)['ResponseMetadata']['HTTPHeaders'][
        'x-amz-bucket-region'
    ]


@register_resource('S3::Bucket')
def remove_s3_buckets(session, region) -> list[str]:
    s3 = session.client('s3')

    removed_resources = []

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
        except Exception as e:
            if e.response['Error']['Code'] == 'NoSuchTagSet':
                bucket_tags = {}
            else:
                raise

        if not check_delete(boto3_tag_list_to_dict(bucket_tags)):
            continue

        if not CONFIG['LIST_ONLY']:
            bucket.object_versions.all().delete()
            bucket.delete()

        removed_resources.append(f'arn:aws:s3:::{bucket_name}')

    return removed_resources
