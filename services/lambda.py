from lib.utils import check_delete
from registry.decorator import register_query_function, register_terminate_function
from utils.aws import boto3_paginate


@register_query_function('Lambda::Function')
def query_lambda_functions(session, region) -> list[str]:
    lmbda = session.client('lambda', region_name=region)
    resource_arns = []

    functions = list(
        boto3_paginate(
            lmbda,
            'list_functions',
            search='Functions[].FunctionArn',
        )
    )
    for function_arn in functions:
        function_tags = lmbda.list_tags(Resource=function_arn)['Tags']

        if check_delete(function_tags):
            resource_arns.append(function_arn)

    return resource_arns


@register_terminate_function('Lambda::Function')
def remove_lambda_functions(session, region, resource_arns: list[str]) -> None:
    lmbda = session.client('lambda', region_name=region)

    for function_arn in resource_arns:
        function_name = function_arn.split('/')[-1]
        lmbda.delete_function(FunctionName=function_name)


@register_query_function('Lambda::Layer')
def query_lambda_layers(session, region) -> list[str]:
    lmbda = session.client('lambda', region_name=region)
    resource_arns = []

    layers = list(
        boto3_paginate(
            lmbda,
            'list_layers',
            search='Layers[].[LayerName,LayerArn]',
        )
    )
    for layer_name, layer_arn in layers:
        layer_versions = list(
            boto3_paginate(
                lmbda,
                'list_layer_versions',
                LayerName=layer_name,
                search='LayerVersions[].Version',
            )
        )
        resource_arns.extend(
            f'{layer_arn}:{layer_version}' for layer_version in layer_versions
        )
    return resource_arns


@register_terminate_function('Lambda::Layer')
def remove_lambda_layers(session, region, resource_arns: list[str]) -> None:
    lmbda = session.client('lambda', region_name=region)

    for layer_arn in resource_arns:
        layer_name = layer_arn.split('/')[-2]
        layer_version = layer_arn.split('/')[-1]

        lmbda.delete_layer_version(LayerName=layer_name, VersionNumber=layer_version)
