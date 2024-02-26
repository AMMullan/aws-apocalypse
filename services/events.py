import botocore.exceptions

from registry import DeleteResponse
from registry.decorator import register_query_function, register_terminate_function
from utils.aws import boto3_paginate, boto3_tag_list_to_dict
from utils.general import check_delete


@register_query_function('Events::Rule')
def query_eventbridge_rule(session, region) -> list[str]:
    events = session.client('events', region_name=region)

    resource_arns = []

    rules = boto3_paginate(events, 'list_rules', search='Rules[].Arn')
    for rule_arn in rules:
        rule_tags = events.list_tags_for_resource(ResourceARN=rule_arn)['Tags']

        if check_delete(boto3_tag_list_to_dict(rule_tags)):
            resource_arns.append(rule_arn)

    return resource_arns


@register_terminate_function('Events::Rule')
def remove_eventbridge_rule(
    session, region, resource_arns: list[str]
) -> DeleteResponse:
    events = session.client('events', region_name=region)

    response = DeleteResponse()

    for rule_arn in resource_arns:
        rule_name = rule_arn.split('/')[-1]
        try:
            if target_ids := [
                target['Id']
                for target in events.list_targets_by_rule(Rule=rule_name)['Targets']
            ]:
                events.remove_targets(Rule=rule_name, Ids=target_ids)
            events.delete_rule(Name=rule_name, Force=True)
            response.successful.append(rule_arn)
        except botocore.exceptions.ClientError as e:
            error_code = e.response['Error']['Code']
            response.failures[error_code].append(rule_arn)

    return response
