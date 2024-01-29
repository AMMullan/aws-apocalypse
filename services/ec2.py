from lib.utils import (
    boto3_tag_list_to_dict,
    check_delete,
    get_account_id,
    paginate_and_search,
)
from registry.decorator import register_query_function, register_terminate_function


@register_query_function('EC2::Image')
def query_ec2_images(session, region) -> list[str]:
    account_id = get_account_id(session)
    ec2 = session.client('ec2', region_name=region)
    images = list(
        paginate_and_search(
            ec2,
            'describe_images',
            Owners=['self'],
            PaginationConfig={'PageSize': 500},
            SearchPath='Images[].[ImageId,Tags]',
        )
    )

    return [
        f'arn:aws:ec2:{region}:{account_id}:image/{image_id}'
        for image_id, image_tags in images
        if check_delete(boto3_tag_list_to_dict(image_tags))
    ]


@register_terminate_function('EC2::Image')
def remove_ec2_images(session, region, resource_arns: list[str]) -> None:
    # TODO - Find, and remove, snapshots after an AMI is deregistered
    ec2 = session.client('ec2', region_name=region)

    for image_arn in resource_arns:
        image_id = image_arn.split('/')[-1]
        ec2.deregister_image(ImageId=image_id)


@register_query_function("EC2::Instance")
def query_ec2_instances(session, region) -> list[str]:
    account_id = get_account_id(session)
    ec2 = session.client('ec2', region_name=region)

    if instances := list(
        paginate_and_search(
            ec2,
            'describe_instances',
            Filters=[
                {
                    'Name': 'instance-state-name',
                    'Values': ['running', 'stopped'],
                }
            ],
            PaginationConfig={'PageSize': 500},
            SearchPath='Reservations[].Instances[].[InstanceId,Tags]',
        )
    ):
        return [
            f'arn:aws:ec2:{region}:{account_id}:instance/{instance_id}'
            for instance_id, instance_tags in instances
            if check_delete(boto3_tag_list_to_dict(instance_tags))
        ]
    else:
        return []


@register_terminate_function("EC2::Instance")
def remove_ec2_instances(session, region, resource_arns: list[str]) -> None:
    # TODO - Find, and remove, secondary volumes AFTER deletion
    # TODO - Do we need to batch the terminate instances ??
    ec2 = session.client('ec2', region_name=region)

    instance_ids = [instance_arn.split('/')[-1] for instance_arn in resource_arns]
    for instance_id in instance_ids:
        ec2.modify_instance_attribute(
            InstanceId=instance_id,
            DisableApiTermination={'Value': False},
        )

        ec2.modify_instance_attribute(
            InstanceId=instance_id,
            DisableApiStop={'Value': False},
        )

    ec2.terminate_instances(InstanceIds=instance_ids)
    ec2.get_waiter('instance_terminated').wait(
        InstanceIds=instance_ids, WaiterConfig={'Delay': 10}
    )


@register_query_function("EC2::NetworkInterface")
def query_ec2_network_interfaces(session, region) -> list[str]:
    account_id = get_account_id(session)
    ec2 = session.client('ec2', region_name=region)
    interfaces = list(
        paginate_and_search(
            ec2,
            'describe_network_interfaces',
            PaginationConfig={'PageSize': 500},
            SearchPath='NetworkInterfaces[].[NetworkInterfaceId,TagSet]',
        )
    )

    return [
        f'arn:aws:ec2:{region}:{account_id}:network-interface/{interface_id}'
        for interface_id, interface_tags in interfaces
        if check_delete(boto3_tag_list_to_dict(interface_tags))
    ]


@register_terminate_function("EC2::NetworkInterface")
def remove_ec2_network_interfaces(session, region, resource_arns: list[str]) -> None:
    ec2 = session.client('ec2', region_name=region)

    for interface_arn in resource_arns:
        interface_id = interface_arn.split('/')[-1]
        ec2.delete_network_interface(NetworkInterfaceId=interface_id)


@register_query_function("EC2::SecurityGroup")
def query_ec2_security_groups(session, region) -> list[str]:
    account_id = get_account_id(session)
    ec2 = session.client('ec2', region_name=region)
    security_groups = list(
        paginate_and_search(
            ec2,
            'describe_security_groups',
            PaginationConfig={'PageSize': 500},
            SearchPath='SecurityGroups[].[GroupId,GroupName,Tags]',
        )
    )

    return [
        f'arn:aws:ec2:{region}:{account_id}:security-group/{group_id}'
        for group_id, group_name, group_tags in security_groups
        if group_name != 'default' and check_delete(boto3_tag_list_to_dict(group_tags))
    ]


@register_terminate_function("EC2::SecurityGroup")
def remove_ec2_security_groups(session, region, resource_arns: list[str]) -> None:
    ec2 = session.client('ec2', region_name=region)

    for group_arn in resource_arns:
        group_id = group_arn.split('/')[-1]

        group_detail = ec2.describe_security_groups(GroupIds=[group_id])[
            'SecurityGroups'
        ]
        if perms := group_detail.get('IpPermissions', []):
            ec2.revoke_security_group_ingress(GroupId=group_id, IpPermissions=perms)

        if perms := group_detail.get('IpPermissionsEgress', []):
            ec2.revoke_security_group_egress(GroupId=group_id, IpPermissions=perms)

        ec2.delete_security_group(GroupId=group_id)


@register_query_function("EC2::Snapshot")
def query_ec2_snapshots(session, region) -> list[str]:
    account_id = get_account_id(session)
    ec2 = session.client('ec2', region_name=region)
    snapshots = list(
        paginate_and_search(
            ec2,
            'describe_snapshots',
            OwnerIds=['self'],
            PaginationConfig={'PageSize': 500},
            SearchPath='Snapshots[].[SnapshotId,Tags]',
        )
    )

    return [
        f'arn:aws:ec2:{region}:{account_id}:snapshot/{snapshot_id}'
        for snapshot_id, snapshot_tags in snapshots
        if check_delete(boto3_tag_list_to_dict(snapshot_tags))
    ]


@register_terminate_function("EC2::Snapshot")
def remove_ec2_snapshots(session, region, resource_arns: list[str]) -> None:
    ec2 = session.client('ec2', region_name=region)

    for snapshot_arn in resource_arns:
        snapshot_id = snapshot_arn.split('/')[-1]
        ec2.delete_snapshot(SnapshotId=snapshot_id)


@register_query_function("EC2::Volume")
def query_ec2_volumes(session, region) -> list[str]:
    account_id = get_account_id(session)
    ec2 = session.client('ec2', region_name=region)
    volumes = list(
        paginate_and_search(
            ec2,
            'describe_volumes',
            Filters=[{'Name': 'status', 'Values': ['available']}],
            PaginationConfig={'PageSize': 500},
            SearchPath='Volumes[].[VolumeId,Tags]',
        )
    )

    return [
        f'arn:aws:ec2:{region}:{account_id}:volume/{volume_id}'
        for volume_id, volume_tags in volumes
        if check_delete(boto3_tag_list_to_dict(volume_tags))
    ]


@register_terminate_function("EC2::Volume")
def remove_ec2_volumes(session, region, resource_arns: list[str]) -> None:
    ec2 = session.client('ec2', region_name=region)

    for volume_arn in resource_arns:
        volume_id = volume_arn.split('/')[-1]
        ec2.delete_volume(VolumeId=volume_id)


@register_query_function('EC2::LaunchTemplate')
def query_launch_templates(session, region) -> list[str]:
    account_id = get_account_id(session)
    ec2 = session.client('ec2', region_name=region)
    templates = list(
        paginate_and_search(
            ec2,
            'describe_launch_templates',
            PaginationConfig={'PageSize': 200},
            SearchPath='LaunchTemplates[].[LaunchTemplateId,Tags]',
        )
    )

    return [
        f'arn:aws:ec2:{region}:{account_id}:launch-template/{template_id}'
        for template_id, template_tags in templates
        if check_delete(boto3_tag_list_to_dict(template_tags))
    ]


@register_terminate_function('EC2::LaunchTemplate')
def remove_launch_templates(session, region, resource_arns: list[str]) -> None:
    ec2 = session.client('ec2', region_name=region)

    for template_arn in resource_arns:
        template_id = template_arn.split('/')[-1]
        ec2.delete_launch_template(LaunchTemplateId=template_id)


@register_query_function('EC2::VPC')
def query_ec2_vpcs(session, region) -> list[str]:
    account_id = get_account_id(session)
    ec2 = session.client('ec2', region_name=region)

    vpcs = list(
        paginate_and_search(
            ec2,
            'describe_vpcs',
            PaginationConfig={'PageSize': 200},
            SearchPath='Vpcs[].[VpcId,Tags]',
        )
    )

    return [
        f'arn:aws:ec2:{region}:{account_id}:vpc/{vpc_id}'
        for vpc_id, vpc_tags in vpcs
        if check_delete(boto3_tag_list_to_dict(vpc_tags))
    ]


@register_terminate_function('EC2::VPC')
def remove_ec2_vpcs(session, region, resource_arns: list[str]) -> None:
    ec2 = session.resource('ec2', region_name=region)
    ec2_c = session.client('ec2', region_name=region)

    for vpc_arn in resource_arns:
        vpc_id = vpc_arn.split('/')[-1]
        vpc = ec2.Vpc(vpc_id)

        gateways = []
        eip_allocations = []
        for gateway in ec2_c.describe_nat_gateways(
            Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
        )['NatGateways']:
            if gateway['State'] == 'deleted':
                continue

            gateways.append(gateway['NatGatewayId'])
            eip_allocations.extend(
                address['AllocationId'] for address in gateway['NatGatewayAddresses']
            )

        for gateway_id in gateways:
            ec2_c.delete_nat_gateway(NatGatewayId=gateway_id)

        # Wait for NAT Gateways to be removed
        ec2_c.get_waiter('nat_gateway_deleted').wait(NatGatewayIds=gateways)

        for eip_allocation in eip_allocations:
            ec2_c.release_address(AllocationId=eip_allocation)

        # Delete VPC Endpoints
        endpoints = [
            endpoint['VpcEndpointId']
            for endpoint in ec2_c.describe_vpc_endpoints(
                Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
            )['VpcEndpoints']
        ]
        ec2_c.delete_vpc_endpoints(VpcEndpointIds=endpoints)

        for subnet in vpc.subnets.all():
            subnet.delete()

        for pcx in vpc.accepted_vpc_peering_connections.all():
            pcx.delete()

        for pcx in vpc.requested_vpc_peering_connections.all():
            pcx.delete()

        for igw in vpc.internet_gateways.all():
            igw.detach_from_vpc(VpcId=vpc_id)
            igw.delete()

        for acl in vpc.network_acls.all():
            if not acl.is_default:
                acl.delete()

        for route_table in vpc.route_tables.all():
            main = any(
                association['Main']
                for association in route_table.associations_attribute
            )
            if not main:
                route_table.delete()

        vpc.delete()


@register_query_function('EC2::DHCPOptions')
def query_ec2_dhcp_options(session, region) -> list[str]:
    account_id = get_account_id(session)
    ec2 = session.client('ec2', region_name=region)

    option_sets = list(
        paginate_and_search(
            ec2,
            'describe_dhcp_options',
            PaginationConfig={'PageSize': 200},
            SearchPath='DhcpOptions[].[DhcpOptionsId,Tags]',
        )
    )

    return [
        f'arn:aws:ec2:{region}:{account_id}:dhcp-options/{options_id}'
        for options_id, option_tags in option_sets
        if check_delete(boto3_tag_list_to_dict(option_tags))
    ]


@register_terminate_function('EC2::DHCPOptions')
def remove_ec2_dhcp_options(session, region, resource_arns: list[str]) -> None:
    ec2 = session.client('ec2', region_name=region)

    for set_arn in resource_arns:
        set_id = set_arn.split('/')[-1]
        ec2.delete_dhcp_options(DhcpOptionsId=set_id)
