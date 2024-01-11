import time

from config import CONFIG
from lib.utils import boto3_tag_list_to_dict, check_delete, paginate_and_search
from registry.decorator import register_resource


@register_resource('EFS::FileSystem')
def remove_efs_filesystems(session, region) -> list[str]:
    efs = session.client('efs', region_name=region)
    removed_resources = []

    filesystems = list(
        paginate_and_search(
            efs,
            'describe_file_systems',
            PaginationConfig={'PageSize': 100},
            SearchPath='FileSystems[].[FileSystemId,FileSystemArn,Tags]',
        )
    )

    for fs_id, fs_arn, fs_tags in filesystems:
        if check_delete(boto3_tag_list_to_dict(fs_tags)):
            if not CONFIG['LIST_ONLY']:
                mount_targets = [
                    target['MountTargetId']
                    for target in efs.describe_mount_targets(FileSystemId=fs_id)[
                        'MountTargets'
                    ]
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

            removed_resources.append(fs_arn)

    return removed_resources
