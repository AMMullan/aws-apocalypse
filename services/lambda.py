from config import CONFIG
from lib.utils import check_delete, paginate_and_search
from registry.decorator import register_resource


@register_resource('Lambda::Function')
def remove_lambda_functions(session, region):
    lmbda = session.client('lambda', region_name=region)
    removed_resources = []

    functions = list(
        paginate_and_search(
            lmbda,
            'list_functions',
            PaginationConfig={'PageSize': 500},
            SearchPath='Functions[].FunctionArn',
        )
    )
    for function_arn in functions:
        function_name = function_arn.split('/')[-1]
        function_tags = lmbda.list_tags(Resource=function_arn)['Tags']

        if check_delete(function_tags):
            if not CONFIG['LIST_ONLY']:
                lmbda.delete_function(FunctionName=function_name)

            removed_resources.append(function_arn)

    return removed_resources


@register_resource('Lambda::Layer')
def remove_lambda_layers(session, region):
    lmbda = session.client('lambda', region_name=region)
    removed_resources = []

    layers = list(
        paginate_and_search(
            lmbda,
            'list_layers',
            PaginationConfig={'PageSize': 50},
            SearchPath='Layers[].[LayerName,LayerArn]',
        )
    )
    for layer in layers:
        layer_name, layer_arn = layer
        layer_versions = list(
            paginate_and_search(
                lmbda,
                'list_layer_versions',
                LayerName=layer_name,
                PaginationConfig={'PageSize': 50},
                SearchPath='LayerVersions[].Version',
            )
        )
        for layer_version in layer_versions:
            if not CONFIG['LIST_ONLY']:
                lmbda.delete_layer_version(
                    LayerName=layer_name, VersionNumber=layer_version
                )

                removed_resources.append(f'{layer_arn}:{layer_version}')

    return removed_resources
