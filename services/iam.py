from config import CONFIG
from lib.utils import boto3_tag_list_to_dict, check_delete
from registry.decorator import register_resource


@register_resource('IAM::User')
def remove_iam_users(session, region) -> list[str]:
    if region != 'global':
        return

    iam = session.resource('iam')
    iam_c = session.client('iam')
    removed_resources = []

    for user in iam.users.all():
        user_arn = user.arn
        user_tags = iam_c.list_user_tags(UserName=user.name)['Tags']

        if not check_delete(boto3_tag_list_to_dict(user_tags)):
            continue

        if not CONFIG['LIST_ONLY']:
            for policy in user.attached_policies.all():
                policy.detach_user(UserName=user.name)

            for policy in user.policies.all():
                policy.delete()

            for group in user.groups.all():
                group.remove_user(UserName=user.name)

            user.delete()

        removed_resources.append(user_arn)

    return removed_resources


@register_resource('IAM::Role')
def remove_iam_roles(session, region) -> list[str]:
    if region != 'global':
        return

    iam = session.resource('iam')
    iam_c = session.client('iam')
    removed_resources = []

    for role in iam.roles.all():
        role_arn = role.arn
        role_tags = iam_c.list_role_tags(RoleName=role.name)['Tags']

        if role.path.startswith(('/aws-reserved/', '/aws-service-role/')):
            continue

        if not check_delete(boto3_tag_list_to_dict(role_tags)):
            continue

        if not CONFIG['LIST_ONLY']:
            for policy in role.attached_policies.all():
                policy.detach_role(RoleName=role.name)

            for policy in role.policies.all():
                policy.delete()

            for instance_profile in role.instance_profiles.all():
                instance_profile.remove_role(RoleName=role.name)

            role.delete()

        removed_resources.append(role_arn)

    return removed_resources


@register_resource('IAM::InstanceProfile')
def remove_iam_instance_profiles(session, region) -> list[str]:
    if region != 'global':
        return

    iam = session.resource('iam')
    removed_resources = []

    for instance_profile in iam.instance_profiles.all():
        profile_arn = instance_profile.arn

        if not CONFIG['LIST_ONLY']:
            instance_profile.delete()

        removed_resources.append(profile_arn)

    return removed_resources


@register_resource('IAM::Group')
def remove_iam_groups(session, region) -> list[str]:
    if region != 'global':
        return

    iam = session.resource('iam')
    removed_resources = []

    for group in iam.groups.all():
        group_arn = group.arn

        if not CONFIG['LIST_ONLY']:
            group.delete()

        removed_resources.append(group_arn)

    return removed_resources


@register_resource('IAM::Policy')
def remove_iam_policies(session, region) -> list[str]:
    if region != 'global':
        return

    iam = session.resource('iam')
    iam_c = session.client('iam')
    removed_resources = []

    for policy in iam.policies.filter(Scope='Local'):
        policy_arn = policy.arn
        policy_tags = iam_c.list_policy_tags(PolicyArn=policy_arn)['Tags']

        if not check_delete(boto3_tag_list_to_dict(policy_tags)):
            continue

        if not CONFIG['LIST_ONLY']:
            policy.delete()

        removed_resources.append(policy_arn)

    return removed_resources
