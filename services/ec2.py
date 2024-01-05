from config import CONFIG
from lib.utils import (
    boto3_tag_list_to_dict,
    check_delete,
    get_account_id,
    paginate_and_search,
)
from registry.decorator import register_resource


@register_resource('EC2::Image')
def remove_ec2_images(session, region) -> list[str]:
    account_id = get_account_id(session)
    ec2 = session.client('ec2', region_name=region)
    removed_resources = []

    images = list(
        paginate_and_search(
            ec2,
            'describe_images',
            Owners=['self'],
            PaginationConfig={'PageSize': 500},
            SearchPath='Images[].[ImageId,Tags]',
        )
    )

    for image_id, image_tags in images:
        if check_delete(boto3_tag_list_to_dict(image_tags)):
            if not CONFIG['LIST_ONLY']:
                ec2.deregister_image(ImageId=image_id)

            removed_resources.append(
                f'arn:aws:ec2:{region}:{account_id}:image/{image_id}'
            )

    return removed_resources


@register_resource("EC2::Instance")
def remove_ec2_instances(session, region) -> list[str]:
    account_id = get_account_id(session)
    ec2 = session.client('ec2', region_name=region)
    removed_resources = []

    instances = list(
        paginate_and_search(
            ec2,
            'describe_instances',
            Filters=[{'Name': 'instance-state-name', 'Values': ['running', 'stopped']}],
            PaginationConfig={'PageSize': 500},
            SearchPath='Reservations[].Instances[].[InstanceId,Tags]',
        )
    )

    if not instances:
        return []

    for instance_id, instance_tags in instances:
        if not check_delete(boto3_tag_list_to_dict(instance_tags)):
            continue

        if not CONFIG['LIST_ONLY']:
            ec2.modify_instance_attribute(
                InstanceId=instance_id,
                DisableApiTermination={'Value': False},
            )

            ec2.modify_instance_attribute(
                InstanceId=instance_id,
                DisableApiStop={'Value': False},
            )

            ec2.terminate_instances(InstanceIds=[instance_id])
            ec2.get_waiter('instance_terminated').wait(InstanceIds=[instance_id])

        removed_resources.append(
            f'arn:aws:ec2:{region}:{account_id}:instance/{instance_id}'
        )

    return removed_resources


@register_resource("EC2::NetworkInterface")
def remove_ec2_network_interfaces(session, region) -> list[str]:
    account_id = get_account_id(session)
    ec2 = session.client('ec2', region_name=region)
    removed_resources = []

    interfaces = list(
        paginate_and_search(
            ec2,
            'describe_network_interfaces',
            PaginationConfig={'PageSize': 500},
            SearchPath='NetworkInterfaces[].[NetworkInterfaceId,TagSet]',
        )
    )

    for interface_id, interface_tags in interfaces:
        if check_delete(boto3_tag_list_to_dict(interface_tags)):
            if not CONFIG['LIST_ONLY']:
                ec2.delete_network_interface(NetworkInterfaceId=interface_id)

            removed_resources.append(
                f'arn:aws:ec2:{region}:{account_id}:network-interface/{interface_id}'
            )

    return removed_resources


@register_resource("EC2::SecurityGroup")
def remove_ec2_security_groups(session, region) -> list[str]:
    account_id = get_account_id(session)
    ec2 = session.client('ec2', region_name=region)
    removed_resources = []

    security_groups = list(
        paginate_and_search(
            ec2,
            'describe_security_groups',
            PaginationConfig={'PageSize': 500},
            SearchPath='SecurityGroups[].[GroupId,GroupName,IpPermissions,IpPermissionsEgress,Tags]',
        )
    )

    if not CONFIG['LIST_ONLY']:
        for (
            group_id,
            _,
            ip_permissions,
            ip_permissions_egress,
            group_tags,
        ) in security_groups:
            if ip_permissions:
                ec2.revoke_security_group_ingress(
                    GroupId=group_id, IpPermissions=ip_permissions
                )

            if ip_permissions_egress:
                ec2.revoke_security_group_egress(
                    GroupId=group_id, IpPermissions=ip_permissions_egress
                )

    for group_id, group_name, _, _, group_tags in security_groups:
        if group_name != 'default' and check_delete(boto3_tag_list_to_dict(group_tags)):
            if not CONFIG['LIST_ONLY']:
                ec2.delete_security_group(GroupId=group_id)

            removed_resources.append(
                f'arn:aws:ec2:{region}:{account_id}:security-group/{group_id}'
            )

    return removed_resources


@register_resource("EC2::Snapshot")
def remove_ec2_snapshots(session, region) -> list[str]:
    account_id = get_account_id(session)
    ec2 = session.client('ec2', region_name=region)
    removed_items = []

    snapshots = list(
        paginate_and_search(
            ec2,
            'describe_snapshots',
            OwnerIds=['self'],
            PaginationConfig={'PageSize': 500},
            SearchPath='Snapshots[].[SnapshotId,Tags]',
        )
    )

    for snapshot_id, snapshot_tags in snapshots:
        if check_delete(boto3_tag_list_to_dict(snapshot_tags)):
            if not CONFIG['LIST_ONLY']:
                ec2.delete_snapshot(SnapshotId=snapshot_id)

            removed_items.append(
                f'arn:aws:ec2:{region}:{account_id}:snapshot/{snapshot_id}'
            )

    return removed_items


@register_resource("EC2::Volume")
def remove_ec2_volumes(session, region) -> list[str]:
    account_id = get_account_id(session)
    ec2 = session.client('ec2', region_name=region)
    removed_items = []

    volumes = list(
        paginate_and_search(
            ec2,
            'describe_volumes',
            Filters=[{'Name': 'status', 'Values': ['available']}],
            PaginationConfig={'PageSize': 500},
            SearchPath='Volumes[].[VolumeId,Tags]',
        )
    )

    for volume_id, volume_tags in volumes:
        if check_delete(boto3_tag_list_to_dict(volume_tags)):
            if not CONFIG['LIST_ONLY']:
                ec2.delete_volume(VolumeId=volume_id)

            removed_items.append(
                f'arn:aws:ec2:{region}:{account_id}:volume/{volume_id}'
            )

    return removed_items
