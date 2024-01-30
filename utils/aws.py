from dataclasses import dataclass

import boto3
import botocore.exceptions

from . import API_MAX_PAGE_SIZE


@dataclass
class InvalidServiceMethodException(Exception):
    client: str
    method: str

    def __str__(self):
        # We're only assigning variables here to keep the error clean
        client = self.client
        method = self.method

        context_info = f'{client=}, {method=}'
        return f'[ERROR] Invalid Client/Method: {context_info  }'


def boto3_paginate(client, method: str, search: str | None = None, **kwargs):
    """Pagination for AWS APIs

    Args:
        client: a boto3 client (i.e. boto3.client('ec2'))
        method: the API method to call
        search (str | None, optional): JMESPath Search Filter
        **kwargs: any additional parameters for API call

    Returns:
        Either a pagintor, or a filtered list of results
    """

    service = client.__class__.__name__.lower()
    api_call = f'{service}.{method}'

    if api_call not in API_MAX_PAGE_SIZE:
        print(f'Unknown: {service}.{method}')

    pagination_config = kwargs.pop('PaginationConfig', None)
    if not pagination_config:
        if api_call in API_MAX_PAGE_SIZE and API_MAX_PAGE_SIZE[api_call]:
            pagination_config = {
                'PaginationConfig': {'PageSize': API_MAX_PAGE_SIZE[api_call]}
            }
        else:
            pagination_config = {}

    if not getattr(client, method, None):
        raise InvalidServiceMethodException(service, method)

    try:
        paginator = client.get_paginator(method).paginate(**kwargs, **pagination_config)
    except botocore.exceptions.OperationNotPageableError:
        # Do we want to do anything more here?
        raise

    return paginator.search(search) if search else paginator


def get_account_id(session: boto3.session.Session) -> str:
    return session.client('sts').get_caller_identity()['Account']


def get_enabled_regions(session: boto3.session.Session) -> list:
    if not isinstance(session, boto3.session.Session):
        raise TypeError('Not a boto3 Session Object')

    # Get a list of available regions
    ec2 = session.client('ec2', region_name='us-east-1')

    return [
        region['RegionName']
        for region in ec2.describe_regions(
            Filters=[
                {'Name': 'opt-in-status', 'Values': ['opt-in-not-required', 'opted-in']}
            ]
        )['Regions']
    ]


def boto3_tag_list_to_dict(tags_list: list) -> dict:
    # Check if the list contains KMS tags
    if tags_list and any('TagKey' in tag for tag in tags_list):
        return {tag.get("TagKey"): tag.get("TagValue") for tag in tags_list}

    return (
        {
            tag.get("key"): tag.get("value")
            for tag in ({k.lower(): v for k, v in tag.items()} for tag in tags_list)
            if "key" in tag
        }
        if tags_list
        else {}
    )
