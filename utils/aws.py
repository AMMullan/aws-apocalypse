from dataclasses import dataclass

import botocore.exceptions

MAX_PAGESIZE = 1000

# NB: There are some in this list that MAY seem odd, like sfn.* - we're using the class
#     name here, not the service name as seen in boto3. I've commented where these differ
API_MAX_PAGE_SIZE = {
    'acm.list_certificates': MAX_PAGESIZE,
    'apigateway.get_resources': MAX_PAGESIZE,
    'apigateway.get_rest_apis': MAX_PAGESIZE,
    'apigatewayv2.get_apis': MAX_PAGESIZE,
    'autoscaling.describe_auto_scaling_groups': 100,
    'autoscaling.describe_launch_configurations': 100,
    'backup.list_backup_plans': MAX_PAGESIZE,
    'backup.list_protected_resources': MAX_PAGESIZE,
    'batch.describe_job_queues': MAX_PAGESIZE,
    'cloudformation.list_stacks': None,
    'cloudfront.list_distributions': MAX_PAGESIZE,
    'cloudtrail.lookup_events': MAX_PAGESIZE,
    'cloudwatch.describe_alarms': 100,
    'cloudwatch.get_metric_data': MAX_PAGESIZE,
    'cloudwatchlogs.describe_log_groups': 50,  # Differs from API docs (logs)
    'codepipeline.list_pipelines': MAX_PAGESIZE,
    'docdb.describe_db_clusters': 100,
    'docdb.describe_db_instances': 100,
    'dynamodb.list_tables': 100,
    'ec2.describe_dhcp_options': MAX_PAGESIZE,
    'ec2.describe_iam_instance_profile_associations': MAX_PAGESIZE,
    'ec2.describe_images': MAX_PAGESIZE,
    'ec2.describe_instance_types': 100,
    'ec2.describe_instances': MAX_PAGESIZE,
    'ec2.describe_launch_template_versions': 200,
    'ec2.describe_launch_templates': 200,
    'ec2.describe_network_interfaces': MAX_PAGESIZE,
    'ec2.describe_route_tables': 100,
    'ec2.describe_security_group_rules': MAX_PAGESIZE,
    'ec2.describe_security_groups': MAX_PAGESIZE,
    'ec2.describe_snapshots': MAX_PAGESIZE,
    'ec2.describe_subnets': MAX_PAGESIZE,
    'ec2.describe_volumes': MAX_PAGESIZE,
    'ec2.describe_vpcs': MAX_PAGESIZE,
    'ecr.describe_repositories': MAX_PAGESIZE,
    'ecs.list_clusters': 100,
    'ecs.list_services': 100,
    'ecs.list_task_definitions': 100,
    'ecs.list_tasks': 100,
    'efs.describe_file_systems': MAX_PAGESIZE,
    'elasticache.describe_cache_clusters': 100,
    'elasticache.describe_serverless_caches': 100,
    'elasticache.describe_snapshots': 50,
    'elasticbeanstalk.describe_environments': MAX_PAGESIZE,
    'elasticbeanstalk.list_platform_versions': MAX_PAGESIZE,
    'elasticloadbalancing.describe_load_balancers': 400,  # Differs from API docs (elb)
    'elasticloadbalancingv2.describe_load_balancers': 400,  # Differs from API docs (elbv2)
    'elasticloadbalancingv2.describe_target_groups': 400,  # Differs from API docs (elbv2)
    'eventbridge.list_rules': 100,  # Differs from API docs (events)
    'fsx.describe_file_systems': MAX_PAGESIZE,
    'iam.get_account_authorization_details': MAX_PAGESIZE,
    'iam.list_attached_role_policies': MAX_PAGESIZE,
    'iam.list_entities_for_policy': MAX_PAGESIZE,
    'iam.list_instance_profiles': MAX_PAGESIZE,
    'iam.list_instance_profiles_for_role': MAX_PAGESIZE,
    'iam.list_policies': MAX_PAGESIZE,
    'iam.list_roles': MAX_PAGESIZE,
    'iam.list_users': MAX_PAGESIZE,
    'identitystore.list_group_memberships': 100,
    'identitystore.list_groups': 100,
    'kinesis.list_streams': MAX_PAGESIZE,
    'kms.list_keys': MAX_PAGESIZE,
    'lambda.list_functions': MAX_PAGESIZE,
    'lambda.list_layers': 50,
    'neptune.describe_db_clusters': 100,
    'neptune.describe_db_instances': 100,
    'organizations.list_accounts_for_parent': 20,
    'pricing.get_products': 100,
    'rds.describe_db_cluster_snapshots': 100,
    'rds.describe_db_clusters': 100,
    'rds.describe_db_instances': 100,
    'rds.describe_db_snapshots': 100,
    'redshift.describe_clusters': 100,
    'resourcegroupstaggingapi.get_resources': 100,
    'route53.list_hosted_zones': MAX_PAGESIZE,
    'route53.list_resource_record_sets': MAX_PAGESIZE,
    's3.list_objects_v2': MAX_PAGESIZE,
    'secretsmanager.list_secrets': 100,
    'sfn.list_state_machines': MAX_PAGESIZE,  # Differs from API docs (stepfunctions)
    'sns.list_topics': None,
    'sqs.list_queues': MAX_PAGESIZE,
    'ssm.describe_instance_information': 50,
    'ssoadmin.list_account_assignments': 100,
    'ssoadmin.list_accounts_for_provisioned_permission_set': 100,
    'ssoadmin.list_managed_policies_in_permission_set': 100,
    'ssoadmin.list_permission_sets': 100,
    'ssoadmin.list_permission_sets_provisioned_to_account': 100,
    'ssoadmin.list_tags_for_resource': None,
    'storagegateway.list_volumes': MAX_PAGESIZE,
    'transfer.list_servers': MAX_PAGESIZE,
}


@dataclass
class InvalidServiceMethodException(Exception):
    client: str
    method: str

    def __str__(self):
        # We're only assigning variables here to keep the error clean
        client = self.client
        method = self.method

        context_info = f'{client=}, {method=}'
        return f'[ERROR] Invalid Client/Method: {context_info  }'


def boto3_paginate(client, method: str, search: str | None = None, **kwargs):
    """Pagination for AWS APIs

    Args:
        client: a boto3 client (i.e. boto3.client('ec2'))
        method: the API method to call
        search (str | None, optional): JMESPath Search Filter
        **kwargs: any additional parameters for API call

    Returns:
        Either a pagintor, or a filtered list of results
    """

    service = client.__class__.__name__.lower()
    api_call = f'{service}.{method}'

    if api_call not in API_MAX_PAGE_SIZE:
        print(f'Unknown: {service}.{method}')

    pagination_config = kwargs.pop('PaginationConfig', None)
    if not pagination_config:
        if api_call in API_MAX_PAGE_SIZE and API_MAX_PAGE_SIZE[api_call]:
            pagination_config = {
                'PaginationConfig': {'PageSize': API_MAX_PAGE_SIZE[api_call]}
            }
        else:
            pagination_config = {}

    if not getattr(client, method, None):
        raise InvalidServiceMethodException(service, method)

    try:
        paginator = client.get_paginator(method).paginate(**kwargs, **pagination_config)
    except botocore.exceptions.OperationNotPageableError:
        # Do we want to do anything more here?
        raise

    return paginator.search(search) if search else paginator
