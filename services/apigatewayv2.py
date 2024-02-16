import botocore.exceptions

from registry import DeleteResponse
from registry.decorator import register_query_function, register_terminate_function
from utils.aws import boto3_paginate
from utils.general import check_delete


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
def remove_apigatewayv2_apis(
    session, region, resource_arns: list[str]
) -> DeleteResponse:
    apigateway = session.client('apigatewayv2', region_name=region)

    response = DeleteResponse()

    for api_arn in resource_arns:
        api_id = api_arn.split('/')[-1]

        try:
            apigateway.delete_api(ApiId=api_id)
            response.successful.append(api_arn)
        except botocore.exceptions.ClientError as e:
            error_code = e.response['Error']['Code']
            response.failures[error_code].append(api_arn)

    return response
