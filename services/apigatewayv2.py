from lib.utils import check_delete, paginate_and_search
from registry.decorator import register_query_function, register_terminate_function


@register_query_function('ApiGatewayV2::Api')
def query_apigatewayv2_apis(session, region) -> list[str]:
    apigateway = session.client('apigatewayv2', region_name=region)
    apis = list(
        paginate_and_search(
            apigateway,
            'get_apis',
            PaginationConfig={'PageSize': 100},
            SearchPath='Items[].[ApiId,Tags]',
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
