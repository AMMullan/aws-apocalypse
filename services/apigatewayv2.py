from config import CONFIG
from lib.utils import check_delete, paginate_and_search
from registry.decorator import register_resource


@register_resource('ApiGatewayV2::Api')
def remove_apigatewayv2_apis(session, region) -> list[str]:
    apigateway = session.client('apigatewayv2', region_name=region)
    removed_resources = []

    apis = list(
        paginate_and_search(
            apigateway,
            'get_apis',
            PaginationConfig={'PageSize': 100},
            SearchPath='Items[].[ApiId,Tags]',
        )
    )

    for api_id, api_tags in apis:
        if check_delete(api_tags):
            if not CONFIG['LIST_ONLY']:
                apigateway.delete_api(ApiId=api_id)

            removed_resources.append(f'arn:aws:apigateway:{region}::/apis/{api_id}')

    return removed_resources
