from config import CONFIG
from lib.utils import boto3_tag_list_to_dict, check_delete, paginate_and_search
from registry.decorator import register_resource


@register_resource('FSx::FileSystem')
def remove_fsx_filesystems(session, region) -> list[str]:
    fsx = session.client('fsx', region_name=region)
    removed_resources = []

    filesystems = list(
        paginate_and_search(
            fsx,
            'describe_file_systems',
            PaginationConfig={'PageSize': 100},
            SearchPath='FileSystems[].[FileSystemId,ResourceARN,FileSystemType,Tags]',
        )
    )

    for fs_id, fs_arn, fs_type, fs_tags in filesystems:
        # We're currently only supporting WINDOWS filesystems
        delete_params = {}
        match fs_type:
            case 'WINDOWS':
                delete_params['WindowsConfiguration'] = {'SkipFinalBackup': True}
            case 'OPENZFS':
                delete_params['OpenZFSConfiguration'] = {'SkipFinalBackup': True}
            case 'LUSTRE':
                ...
            case _:
                # We only support the above filesystem types
                continue

        if check_delete(boto3_tag_list_to_dict(fs_tags)):
            if not CONFIG['LIST_ONLY']:
                # Remove Filesystem
                fsx.delete_file_system(FileSystemId=fs_id, **delete_params)

            removed_resources.append(fs_arn)

    return removed_resources
