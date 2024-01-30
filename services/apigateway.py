from lib.utils import check_delete
from registry.decorator import register_query_function, register_terminate_function
from utils.aws import boto3_paginate


@register_query_function('ApiGateway::RestApi')
def query_apigateway_rest_apis(session, region) -> list[str]:
    apigateway = session.client('apigateway', region_name=region)
    apis = list(
        boto3_paginate(
            apigateway,
            'get_rest_apis',
            search='items[].[id,tags]',
        )
    )

    return [
        f'arn:aws:apigateway:{region}::/restapis/{api_id}'
        for api_id, api_tags in apis
        if check_delete(api_tags)
    ]


@register_terminate_function('ApiGateway::RestApi')
def remove_apigateway_rest_apis(session, region, resource_arns: list[str]) -> None:
    apigateway = session.client('apigateway', region_name=region)

    for api_arn in resource_arns:
        api_id = api_arn.split('/')[-1]
        apigateway.delete_rest_api(restApiId=api_id)
