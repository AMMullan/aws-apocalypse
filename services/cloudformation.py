import botocore.exceptions

from registry import DeleteResponse
from registry.decorator import register_query_function, register_terminate_function
from utils.aws import boto3_paginate, boto3_tag_list_to_dict
from utils.general import check_delete


@register_query_function('CloudFormation::Stack')
def query_cloudformation_stacks(session, region) -> list[str]:
    cf = session.client('cloudformation', region_name=region)

    resource_arns = []

    stacks = boto3_paginate(
        cf,
        'list_stacks',
        StackStatusFilter=[
            'CREATE_COMPLETE',
        ],
        search='StackSummaries[].StackName',
    )
    for stack_name in stacks:
        stack = cf.describe_stacks(StackName=stack_name)['Stacks'][0]
        stack_tags = stack['Tags']
        stack_arn = stack['StackId']

        if check_delete(boto3_tag_list_to_dict(stack_tags)):
            resource_arns.append(stack_arn)

    return resource_arns


@register_terminate_function('CloudFormation::Stack')
def remove_cloudformation_stacks(
    session, region, resource_arns: list[str]
) -> DeleteResponse:
    cf = session.client('cloudformation', region_name=region)

    response = DeleteResponse()

    for stack_arn in resource_arns:
        stack_name = stack_arn.split('/')[-2]

        try:
            cf.delete_stack(StackName=stack_name)
            response.successful.append(stack_arn)
        except botocore.exceptions.ClientError as e:
            error_code = e.response['Error']['Code']
            response.failures[error_code].append(stack_arn)

    return response
