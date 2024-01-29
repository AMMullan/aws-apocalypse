from lib.utils import boto3_tag_list_to_dict, check_delete, paginate_and_search
from registry.decorator import register_query_function, register_terminate_function


@register_query_function('AutoScaling::AutoScalingGroup')
def query_autoscaling_groups(session, region) -> list[str]:
    autoscaling = session.client('autoscaling', region_name=region)
    groups = list(
        paginate_and_search(
            autoscaling,
            'describe_auto_scaling_groups',
            PaginationConfig={'PageSize': 100},
            SearchPath='AutoScalingGroups[].[AutoScalingGroupARN,Tags]',
        )
    )

    return [
        group_arn
        for group_arn, group_tags in groups
        if check_delete(boto3_tag_list_to_dict(group_tags))
    ]


@register_terminate_function('AutoScaling::AutoScalingGroup')
def remove_autoscaling_groups(session, region, resource_arns: list[str]) -> None:
    autoscaling = session.client('autoscaling', region_name=region)

    for group_arn in resource_arns:
        autoscaling.delete_auto_scaling_group(
            AutoScalingGroupName=group_arn.split('/')[-1]
        )


@register_query_function('AutoScaling::LaunchConfiguration')
def query_autoscaling_launch_configs(session, region) -> list[str]:
    autoscaling = session.client('autoscaling', region_name=region)
    return list(
        paginate_and_search(
            autoscaling,
            'describe_launch_configurations',
            PaginationConfig={'PageSize': 100},
            SearchPath='LaunchConfigurations[].LaunchConfigurationARN',
        )
    )


@register_terminate_function('AutoScaling::LaunchConfiguration')
def remove_autoscaling_launch_configs(
    session, region, resource_arns: list[str]
) -> None:
    autoscaling = session.client('autoscaling', region_name=region)

    for config_arn in resource_arns:
        autoscaling.delete_launch_configuration(
            LaunchConfigurationName=config_arn.split('/')[-1]
        )
