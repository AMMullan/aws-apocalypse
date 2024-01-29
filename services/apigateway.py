from lib.utils import check_delete, paginate_and_search
from registry.decorator import register_query_function, register_terminate_function


@register_query_function('ApiGateway::RestApi')
def query_apigateway_rest_apis(session, region) -> list[str]:
    apigateway = session.client('apigateway', region_name=region)
    apis = list(
        paginate_and_search(
            apigateway,
            'get_rest_apis',
            PaginationConfig={'PageSize': 100},
            SearchPath='items[].[id,tags]',
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
