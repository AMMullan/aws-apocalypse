from config import CONFIG
from lib.utils import boto3_tag_list_to_dict, check_delete, paginate_and_search
from registry.decorator import register_resource


@register_resource('AutoScaling::AutoScalingGroup')
def remove_autoscaling_groups(session, region) -> list[str]:
    autoscaling = session.client('autoscaling', region_name=region)
    removed_resources = []

    groups = list(
        paginate_and_search(
            autoscaling,
            'describe_auto_scaling_groups',
            PaginationConfig={'PageSize': 100},
            SearchPath='AutoScalingGroups[].[AutoScalingGroupARN,Tags]',
        )
    )

    for group_arn, group_tags in groups:
        group_name = group_arn.split('/')[-1]

        if check_delete(boto3_tag_list_to_dict(group_tags)):
            if not CONFIG['LIST_ONLY']:
                autoscaling.delete_auto_scaling_group(AutoScalingGroupName=group_name)

            removed_resources.append(group_arn)

    return removed_resources


@register_resource('AutoScaling::LaunchConfiguration')
def remove_autoscaling_launch_configs(session, region) -> list[str]:
    autoscaling = session.client('autoscaling', region_name=region)
    removed_resources = []

    launch_congigs = list(
        paginate_and_search(
            autoscaling,
            'describe_launch_configurations',
            PaginationConfig={'PageSize': 100},
            SearchPath='LaunchConfigurations[].LaunchConfigurationARN',
        )
    )

    for config_arn in launch_congigs:
        config_name = config_arn.split('/')[-1]

        if not CONFIG['LIST_ONLY']:
            autoscaling.delete_launch_configuration(LaunchConfigurationName=config_name)

        removed_resources.append(config_arn)

    return removed_resources
