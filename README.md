[![Maintained by Allan Mullan](https://img.shields.io/badge/maintained%20by-Allan%20Mullan-%235849a6.svg)](https://github.com/AMMullan)

# AWS Apocalypse
*NB: This script is still under active development but at present is in a functional state.*

AWS Apocalypse is a Python alternative to [cloud-nuke](https://github.com/gruntwork-io/cloud-nuke). It is designed to mimic the CLI arguments and core functionality, whilst making it simpler to extend and maintain. The rich output is also similar to cloud-nuke.

> #### BEWARE!
> When executed as `apocalypse.py aws`, this tool is **HIGHLY DESTRUCTIVE** and
> deletes all resources in all regions! This mode should never be used in a production environment! Executing this script is will **permanently delete all resources** in your AWS
> account and is **irreversible**.

It is useful for situations where you have an AWS account you use for testing and need to clean up leftover resources so you're not charged for them.

In addition, Apocalypse offers non-destructive inspecting functionality.

Apocalypse supports inspecting and deleting the following AWS resources:

| Service                 | Resource Type        | Resource String
|-------------------------|----------------------|----------------------------------
| ACM                     | Certificates | CertificateManager::Certificate
| API Gateway             | Rest APIs            | ApiGateway::RestApi
| API Gateway             | v2 APIs (HTTPS)      | ApiGatewayV2::Api
| Auto Scaling            | Auto Scaling Groups | AutoScaling::AutoScalingGroup
| Auto Scaling            | Launch Configurations | AutoScaling::LaunchConfiguration
| CloudFormation          | Stack | CloudFormation::Stack
| CloudTrail              | Trails | CloudTrail::Trail
| CloudWatch              | Dashboard | CloudWatch::Dashboard
| CloudWatch              | Log groups | Logs::LogGroup
| CloudWatch              | Alarms | CloudWatch::Alarm
| DocumentDB              | DB Clusters | DocDB::DBCluster
| DocumentDB              | DB Instances | DocDB::DBInstance
| DynamoDB                | Tables | DynamoDB::Table
| EC2                     | Classic ELBs | ElasticLoadBalancing::LoadBalancer
| EC2                     | ALB/NLBs | ElasticLoadBalancingV2::LoadBalancer
| EC2                     | Target Groups | ElasticLoadBalancingV2::TargetGroup
| EC2                     | EBS Volumes | EC2::Volume
| EC2                     | EC2 Instances | EC2::Instance
| EC2                     | AMIs | EC2::Image
| EC2                     | Snapshots | EC2::Snapshot
| EC2                     | Elastic IPs | EC2::EIP
| EC2                     | Launch Templates |EC2::LaunchTemplate
| EC2                     | VPCs |EC2::VPC
| ECR                     | Repositories | ECR::Repository
| ECS                     | Clusters | ECS::Cluster
| ECS                     | Task Definitions | ECS::TaskDefinition
| EFS                     | File systems | EFS::FileSystem
| Elasticache             | Clusters | ElastiCache::CacheCluster
| Elasticache             | Serverless Caches | ElastiCache::ServerlessCache
| Elasticsearch           | Domain | Elasticsearch::Domain
| Events                  | Rule | Events::Rule
| FSx                     | File systems | FSx::FileSystem
| IAM                     | Users | IAM::User
| IAM                     | Roles | IAM::Role
| IAM                     | Instance Profiles | IAM::InstanceProfile
| IAM                     | Groups | IAM::Group
| IAM                     | Policies | IAM::Policy
| Kinesis                 | Streams | Kinesis:Stream
| KMS                     | Customer-Managed Keys (and associated key aliases) | KMS::Key
| Lambda                  | Functions | Lambda::Function
| Lambda                  | Layers | Lambda::Layer
| Neptune                 | Clusters | Neptune::DBCluster
| Neptune                 | DB Instances | Neptune::DBInstance
| OpenSearch              | Domains | OpenSearchService::Domain
| RDS                     | RDS Clusters | RDS::Cluster
| RDS                     | RDS Databases | RDS::Instance
| S3                      | Buckets | S3::Bucket
| Secrets Manager         | Secrets | SecretsManager::Secret
| SNS                     | Topics | SNS::Topic
| SQS                     | Queues | SQS::Queue
| StepFunctions           | State Machines | StepFunctions::StateMachine
| Transfer Family         | Servers | Transfer::Server

> **NOTE: AWS Backup Resource:** Resources (such as AMIs) created by AWS Backup are
> managed specifically by AWS Backup and cannot be deleted through standard APIs calls for that resource. These resources are tagged by AWS Backup and are filtered out so that Apocalypse does not fail when trying to delete resources it cannot delete.

### Usage

When targeting specific services or resource types it's important to know that the **service** is the string BEFORE the colons, the **resource-type** is the whole resource type string.

When specifing explicit inclusion/exclusion of services or resource types via the CLI or Config, the case of the resource type string is not important.

You can pass either **inspect-aws** to Apocalypse to get a view of all, or targeted, resources in the AWS account or simply **aws** to nuke all/targeted resources. Passing the **\-\-list-resource-types** argument to either of these will simply give you a list of currently supported resource type strings.

Configuration Presedence is:
1. CLI Arguments
2. Config
3. Environment Variables

#### CLI Arguments
| Parameter  | Description | Allows Multiple |
|--|--|--|
| \-\-profile | AWS Profile | false
| \-\-config | Location of Apocalypse configuration file | false
| \-\-region | Specific Region to target | true
| \-\-exclude-region | Specific Region to Exclude from targeting | true
| \-\-output | Output format - **json** or **rich** (default) | false
| \-\-allow-exceptions | Whether to  allow exceptions | false
| \-\-exception-tag | Custom exception tag | true
| \-\-resource-type | Specific Resource Type to target | true
| \-\-exclude-resource-type | Specific Resource Type to exclude from targeting | true
| \-\-service | Specific Service to target | true
| \-\-exclude-service | Specific Service to exclude from targeting | true

#### Configuration File
```json
{
    "blacklisted_accounts": [],
    "whitelisted_accounts": [],
    "allow_exceptions": true,
    "custom_exception_tags": [],
    "regions": [],
    "exclude_regions": [],
    "services": [],
    "exclude_services": [],
    "exclude_resource_types": [],
    "resource_types": []
}
```
When using a configuration file you can specifically blacklist, or whitelist, accounts that Apocalypse can be executed in.

#### Environment Variables
| Variable Name | Example
|---------------|--------
| NUKE_COMMAND | *inspect-aws* or *aws*
| NUKE_REGIONS | *eu-west-1,us-east-1,global*
| NUKE_EXCLUDE_REGIONS | *global,ap-southeast-1*
| NUKE_ALLOW_EXCEPTIONS | *true* (leave for false)
| NUKE_EXCEPTION_TAGS | *DoNotDelete,another-tag*
| NUKE_SERVICES | *iam,ec2*
| NUKE_EXCLUDE_SERVICES | *ec2,lambda*
| NUKE_RESOURCE_TYPES | *ec2::instance,RDS::Cluster*
| NUKE_EXCLUDE_RESOURCE_TYPES | *ec2::instance,rds:Cluster*


## Extending
We use the **Registry** pattern to add a new service/resource type to Apocalypse. You simply need to create 2 new functions in an appropriate .py file in the **services/** folder. These functions need to be decorated with the *register_query_function* and *register_terminate_function* and ensure that the parameters match the existing ones (session and region for both, and resource_arns for the terminate function).

## Contributing
AWS Apocalypse is an open source project and, therefore, contributions from the community are highly encouraged.

There are a few areas that have yet to be done, like adding tests. I'm also sure that there are ways to make the service more maintainable.

For this project we use the [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html) library. A wrapper has been created to simplify pagination and this can be viewed in use in services such as EC2. **There may be a better way of getting the maximum number of items for specific resource types, please do let me know if you know of some**. If you create an additional resource type please ensure that you update the utils/aws/\_\_init\_\_.py file - if no PageSize is supported just add the string as **None** like the cloudformation.list_stacks one.
