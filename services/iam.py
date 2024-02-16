import botocore.exceptions

from registry.decorator import register_query_function, register_terminate_function
from utils.aws import boto3_tag_list_to_dict
from utils.general import check_delete


@register_query_function('IAM::User')
def query_iam_users(session, region) -> list[str]:
    iam = session.resource('iam')
    iam_c = session.client('iam')
    resource_arns = []

    for user in iam.users.all():
        user_tags = iam_c.list_user_tags(UserName=user.name)['Tags']

        if not check_delete(boto3_tag_list_to_dict(user_tags)):
            continue

        resource_arns.append(user.arn)

    return resource_arns


@register_terminate_function('IAM::User')
def remove_iam_users(session, region, resource_arns: list[str]) -> None:
    iam = session.resource('iam')

    for user_arn in resource_arns:
        username = user_arn.split('/')[-1]
        user = iam.User(username)

        for policy in user.attached_policies.all():
            policy.detach_user(UserName=user.name)

        for policy in user.policies.all():
            policy.delete()

        for group in user.groups.all():
            group.remove_user(UserName=user.name)

        user.delete()


@register_query_function('IAM::Role')
def query_iam_roles(session, region) -> list[str]:
    iam = session.resource('iam')
    iam_c = session.client('iam')
    resource_arns = []

    for role in iam.roles.all():
        role_tags = iam_c.list_role_tags(RoleName=role.name)['Tags']

        if role.path.startswith(('/aws-reserved/', '/aws-service-role/')):
            continue

        if not check_delete(boto3_tag_list_to_dict(role_tags)):
            continue

        role_arn = role.arn
        resource_arns.append(role_arn)

    return resource_arns


@register_terminate_function('IAM::Role')
def remove_iam_roles(session, region, resource_arns: list[str]) -> None:
    iam = session.resource('iam')

    for role_arn in resource_arns:
        role_name = role_arn.split('/')[-1]
        role = iam.Role(role_name)

        for policy in role.attached_policies.all():
            try:
                policy.detach_role(RoleName=role.name)
            except botocore.exceptions.ClientError as e:
                error_code = e.response['Error']['Code']

                print(
                    f'Failed To Detach Role Policy ({policy.policy_name}) From {role_arn} | {error_code}'
                )
                break
        else:
            for policy in role.policies.all():
                policy.delete()

            for instance_profile in role.instance_profiles.all():
                instance_profile.remove_role(RoleName=role.name)

            role.delete()


@register_query_function('IAM::InstanceProfile')
def query_iam_instance_profiles(session, region) -> list[str]:
    iam = session.resource('iam')
    return [instance_profile.arn for instance_profile in iam.instance_profiles.all()]


@register_terminate_function('IAM::InstanceProfile')
def remove_iam_instance_profiles(session, region, resource_arns: list[str]) -> None:
    iam = session.resource('iam')

    for profile_arn in resource_arns:
        profile_name = profile_arn.split('/')[-1]

        profile = iam.InstanceProfile(profile_name)
        profile.delete()


@register_query_function('IAM::Group')
def query_iam_groups(session, region) -> list[str]:
    iam = session.resource('iam')
    return [group.arn for group in iam.groups.all()]


@register_terminate_function('IAM::Group')
def remove_iam_groups(session, region, resource_arns: list[str]) -> None:
    iam = session.resource('iam')

    for group_arn in resource_arns:
        group_name = group_arn.split('/')[-1]
        group = iam.Group(group_name)

        for policy in group.attached_policies.all():
            try:
                policy.detach_role(RoleName=group_name)
            except botocore.exceptions.ClientError as e:
                error_code = e.response['Error']['Code']
                print(
                    f'Failed To Detach Group Policy ({policy.policy_name}) From {group_arn} | {error_code}'
                )
                break
        else:
            group.delete()


@register_query_function('IAM::Policy')
def query_iam_policies(session, region) -> list[str]:
    iam = session.resource('iam')
    iam_c = session.client('iam')
    resource_arns = []

    for policy in iam.policies.filter(Scope='Local'):
        policy_arn = policy.arn
        policy_tags = iam_c.list_policy_tags(PolicyArn=policy_arn)['Tags']

        if not check_delete(boto3_tag_list_to_dict(policy_tags)):
            continue

        resource_arns.append(policy_arn)

    return resource_arns


@register_terminate_function('IAM::Policy')
def remove_iam_policies(session, region, resource_arns: list[str]) -> None:
    iam = session.resource('iam')

    for policy_arn in resource_arns:
        policy = iam.Policy(policy_arn)
        try:
            policy.delete()
        except botocore.exceptions.ClientError as e:
            error_code = e.response['Error']['Code']
            print(f'Failed To Delete Policy ({policy_arn}) | {error_code}')
