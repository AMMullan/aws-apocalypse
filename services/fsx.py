from lib.utils import boto3_tag_list_to_dict, check_delete, paginate_and_search
from registry.decorator import register_query_function, register_terminate_function


@register_query_function('FSx::FileSystem')
def query_fsx_filesystems(session, region) -> list[str]:
    fsx = session.client('fsx', region_name=region)
    filesystems = list(
        paginate_and_search(
            fsx,
            'describe_file_systems',
            PaginationConfig={'PageSize': 100},
            SearchPath='FileSystems[].[ResourceARN,Tags]',
        )
    )

    return [
        fs_arn
        for fs_arn, fs_tags in filesystems
        if check_delete(boto3_tag_list_to_dict(fs_tags))
    ]


@register_terminate_function('FSx::FileSystem')
def remove_fsx_filesystems(session, region, resource_arns: list[str]) -> None:
    fsx = session.client('fsx', region_name=region)

    fsx_ids = [arn.split('/')[-1] for arn in resource_arns]
    filesystems = list(
        paginate_and_search(
            fsx,
            'describe_file_systems',
            FileSystemIds=fsx_ids,
            PaginationConfig={'PageSize': 100},
            SearchPath='FileSystems[].[FileSystemId,FileSystemType]',
        )
    )
    for fs_id, fs_type in filesystems:
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

        fsx.delete_file_system(FileSystemId=fs_id, **delete_params)
