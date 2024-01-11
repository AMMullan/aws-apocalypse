from config import CONFIG
from lib.utils import check_delete, paginate_and_search
from registry.decorator import register_resource


@register_resource('ApiGateway::RestApi')
def remove_apigateway_rest_apis(session, region) -> list[str]:
    apigateway = session.client('apigateway', region_name=region)
    removed_resources = []

    apis = list(
        paginate_and_search(
            apigateway,
            'get_rest_apis',
            PaginationConfig={'PageSize': 100},
            SearchPath='items[].[id,tags]',
        )
    )

    for api_id, api_tags in apis:
        if check_delete(api_tags):
            if not CONFIG['LIST_ONLY']:
                apigateway.delete_rest_api(restApiId=api_id)

            removed_resources.append(f'arn:aws:apigateway:{region}::/restapis/{api_id}')

    return removed_resources
