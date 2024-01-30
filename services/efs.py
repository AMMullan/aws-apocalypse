import time

from lib.utils import boto3_tag_list_to_dict, check_delete
from registry.decorator import register_query_function, register_terminate_function
from utils.aws import boto3_paginate


@register_query_function('EFS::FileSystem')
def query_efs_filesystems(session, region) -> list[str]:
    efs = session.client('efs', region_name=region)
    filesystems = list(
        boto3_paginate(
            efs,
            'describe_file_systems',
            search='FileSystems[].[FileSystemArn,Tags]',
        )
    )

    return [
        fs_arn
        for fs_arn, fs_tags in filesystems
        if check_delete(boto3_tag_list_to_dict(fs_tags))
    ]


@register_terminate_function('EFS::FileSystem')
def remove_efs_filesystems(session, region, resource_arns: list[str]) -> None:
    efs = session.client('efs', region_name=region)

    for fs_arn in resource_arns:
        fs_id = fs_arn.split('/')[-1]

        mount_targets = [
            target['MountTargetId']
            for target in efs.describe_mount_targets(FileSystemId=fs_id)['MountTargets']
        ]

        # Delete Mount Targets
        for target_id in mount_targets:
            efs.delete_mount_target(MountTargetId=target_id)

        # Monitor Status
        while True:
            if efs.describe_mount_targets(FileSystemId=fs_id)['MountTargets']:
                time.sleep(5)
                continue
            break

        # Remove Filesystem
        efs.delete_file_system(FileSystemId=fs_id)
