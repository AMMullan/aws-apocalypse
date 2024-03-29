import botocore.exceptions

from registry import DeleteResponse
from registry.decorator import register_query_function, register_terminate_function
from utils.aws import boto3_paginate, boto3_tag_list_to_dict
from utils.general import check_delete


@register_query_function('StepFunctions::StateMachine')
def query_state_machines(session, region) -> list[str]:
    sfn = session.client('stepfunctions', region_name=region)
    resource_arns = []

    machines = list(
        boto3_paginate(
            sfn,
            'list_state_machines',
            search='stateMachines[].[stateMachineArn, creationDate]',
        )
    )

    for machine_arn, created in machines:
        repo_tags = sfn.list_tags_for_resource(resourceArn=machine_arn)['tags']

        if check_delete(boto3_tag_list_to_dict(repo_tags)):
            resource_arns.append(machine_arn)

    return resource_arns


@register_terminate_function('StepFunctions::StateMachine')
def remove_state_machines(session, region, resource_arns: list[str]) -> DeleteResponse:
    sfn = session.client('stepfunctions', region_name=region)

    response = DeleteResponse()

    for machine_arn in resource_arns:
        try:
            sfn.delete_state_machine(stateMachineArn=machine_arn)
            response.successful.append(machine_arn)
        except botocore.exceptions.ClientError as e:
            error_code = e.response['Error']['Code']
            response.failures[error_code].append(machine_arn)

    return response
