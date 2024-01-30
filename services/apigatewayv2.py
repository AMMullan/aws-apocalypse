from utils.general import check_delete
from registry.decorator import register_query_function, register_terminate_function
from utils.aws import boto3_paginate


@register_query_function('ApiGatewayV2::Api')
def query_apigatewayv2_apis(session, region) -> list[str]:
    apigateway = session.client('apigatewayv2', region_name=region)
    apis = list(
        boto3_paginate(
            apigateway,
            'get_apis',
            search='Items[].[ApiId,Tags]',
        )
    )

    return [
        f'arn:aws:apigateway:{region}::/apis/{api_id}'
        for api_id, api_tags in apis
        if check_delete(api_tags)
    ]


@register_terminate_function('ApiGatewayV2::Api')
def remove_apigatewayv2_apis(session, region, resource_arns: list[str]) -> None:
    apigateway = session.client('apigatewayv2', region_name=region)

    for api_arn in resource_arns:
        api_id = api_arn.split('/')[-1]
        apigateway.delete_api(ApiId=api_id)
