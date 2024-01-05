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
            SearchPath='Functions[].[FunctionName,FunctionArn]',
        )
    )
    for function in functions:
        function_tags = lmbda.list_tags(Resource=function[1])['Tags']

        if check_delete(function_tags):
            if not CONFIG['LIST_ONLY']:
                lmbda.delete_function(FunctionName=function[0])

            removed_resources.append(function[1])

    return removed_resources
