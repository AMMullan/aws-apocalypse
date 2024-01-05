import boto3

from config import CONFIG


def get_account_id(session: boto3.session.Session) -> str:
    return session.client('sts').get_caller_identity()['Account']


def get_enabled_regions(session: boto3.session.Session) -> list:
    if not isinstance(session, boto3.session.Session):
        raise TypeError('Not a boto3 Session Object')

    # Get a list of available regions
    ec2 = session.client('ec2', region_name='us-east-1')
    response = ec2.describe_regions(
        Filters=[
            {'Name': 'opt-in-status', 'Values': ['opt-in-not-required', 'opted-in']}
        ]
    )
    return [region.get('RegionName') for region in response.get('Regions')]


def boto3_tag_list_to_dict(tags_list: list) -> dict:
    return {tag['Key'].lower(): tag['Value'] for tag in tags_list} if tags_list else {}


def paginate_and_search(client, method, **kwargs):
    search_path = kwargs.pop('SearchPath')
    paginator = client.get_paginator(method)
    return paginator.paginate(**kwargs).search(search_path)


def check_delete(tags: dict):
    if not CONFIG['ALLOW_EXCEPTIONS']:
        return True

    if tags.get(CONFIG['EXCEPTION_TAG'], 'false').lower() != 'true':
        return True
