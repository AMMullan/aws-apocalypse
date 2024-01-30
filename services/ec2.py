from lib.utils import boto3_tag_list_to_dict, check_delete, get_account_id
from registry.decorator import register_query_function, register_terminate_function
from utils.aws import boto3_paginate


@register_query_function('EC2::Image')
def query_ec2_images(session, region) -> list[str]:
    account_id = get_account_id(session)
    ec2 = session.client('ec2', region_name=region)
    images = list(
        boto3_paginate(
            ec2,
            'describe_images',
            Owners=['self'],
            search='Images[].[ImageId,Tags]',
        )
    )

    return [
        f'arn:aws:ec2:{region}:{account_id}:image/{image_id}'
        for image_id, image_tags in images
        if check_delete(boto3_tag_list_to_dict(image_tags))
    ]


@register_terminate_function('EC2::Image')
def remove_ec2_images(session, region, resource_arns: list[str]) -> None:
    account_id = get_account_id(session)
    ec2 = session.client('ec2', region_name=region)

    image_ids = [image_arn.split('/')[-1] for image_arn in resource_arns]
    image_detail = ec2.describe_images(ImageIds=image_ids)['Images']

    snapshot_ids = []
    for image in image_detail:
        snapshot_ids.extend(
            mapping['Ebs']['SnapshotId']
            for mapping in image.get('BlockDeviceMappings', [])
            if mapping.get('Ebs')
        )

        image_id = image['ImageId']
        ec2.deregister_image(ImageId=image_id)

    # Remove AMI Snapshots after removal
    snapshot_arns = [
        f'arn:aws:ec2:{region}:{account_id}:image/{snapshot_id}'
        for snapshot_id in snapshot_ids
    ]
    remove_ec2_snapshots(session, region, snapshot_arns)


@register_query_function("EC2::Instance")
def query_ec2_instances(session, region) -> list[str]:
    account_id = get_account_id(session)
    ec2 = session.client('ec2', region_name=region)

    if instances := list(
        boto3_paginate(
            ec2,
            'describe_instances',
            Filters=[
                {
                    'Name': 'instance-state-name',
                    'Values': ['running', 'stopped'],
                }
            ],
            search='Reservations[].Instances[].[InstanceId,Tags]',
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
    # TODO - Do we need to batch the terminate instances ??
    account_id = get_account_id(session)
    ec2 = session.client('ec2', region_name=region)

    instance_ids = [instance_arn.split('/')[-1] for instance_arn in resource_arns]
    retained_volume_arns = [
        f'arn:aws:ec2:{region}:{account_id}:volume/{volume_id}'
        for volume_id, volume_tags in boto3_paginate(
            ec2,
            'describe_volumes',
            Filters=[
                {
                    'Name': 'attachment.instance-id',
                    'Values': instance_ids,
                },
                {'Name': 'attachment.delete-on-termination', 'Values': ['false']},
            ],
            search='Volumes[].[VolumeId,Tags]',
        )
        if check_delete(boto3_tag_list_to_dict(volume_tags))
    ]

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

    remove_ec2_volumes(session, region, retained_volume_arns)


@register_query_function("EC2::NetworkInterface")
def query_ec2_network_interfaces(session, region) -> list[str]:
    account_id = get_account_id(session)
    ec2 = session.client('ec2', region_name=region)
    interfaces = list(
        boto3_paginate(
            ec2,
            'describe_network_interfaces',
            search='NetworkInterfaces[].[NetworkInterfaceId,TagSet]',
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
        boto3_paginate(
            ec2,
            'describe_security_groups',
            search='SecurityGroups[].[GroupId,GroupName,Tags]',
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
        boto3_paginate(
            ec2,
            'describe_snapshots',
            OwnerIds=['self'],
            search='Snapshots[].[SnapshotId,Tags]',
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
        boto3_paginate(
            ec2,
            'describe_volumes',
            Filters=[{'Name': 'status', 'Values': ['available']}],
            search='Volumes[].[VolumeId,Tags]',
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
        boto3_paginate(
            ec2,
            'describe_launch_templates',
            search='LaunchTemplates[].[LaunchTemplateId,Tags]',
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
        boto3_paginate(
            ec2,
            'describe_vpcs',
            search='Vpcs[].[VpcId,Tags]',
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
        boto3_paginate(
            ec2,
            'describe_dhcp_options',
            search='DhcpOptions[].[DhcpOptionsId,Tags]',
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


@register_query_function('EC2::EIP')
def query_ec2_addresses(session, region) -> list[str]:
    account_id = get_account_id(session)
    ec2 = session.client('ec2', region_name=region)
    addresses = ec2.describe_addresses()['Addresses']
    return [
        f'arn:aws:ec2:{region}:{account_id}:eip-allocation/{address["AllocationId"]}'
        for address in addresses
        if not address.get('AssociationId')
    ]


@register_terminate_function('EC2::EIP')
def remove_ec2_addresses(session, region, resource_arns: list[str]) -> None:
    ec2 = session.client('ec2', region_name=region)

    for eip_arn in resource_arns:
        allocation_id = eip_arn.split('/')[-1]
        ec2.release_address(AllocationId=allocation_id)
