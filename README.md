[![Maintained by Allan Mullan](https://img.shields.io/badge/maintained%20by-Allan%20Mullan-%235849a6.svg)](https://github.com/AMMullan)

# AWS Apocalypse
*NB: This script is still under active development but at present is in a functional state.*

AWS Apocalypse is a Python alternative to [cloud-nuke](https://github.com/gruntwork-io/cloud-nuke). It is designed to mimic (as best I can) the same CLI arguments and core functionality, whilst making it simpler to extend and maintain.

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
| ECR                     | Repositories | ECR::Repository
| ECS                     | Clusters | ECS::Cluster
| EFS                     | File systems | EFS::FileSystem
| Elasticache             | Clusters | ElastiCache::CacheCluster
| Elasticache             | Serverless Caches | ElastiCache::ServerlessCache
| Elasticsearch           | Domain | Elasticsearch::Domain
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
| Transfer Family         | Servers | Transfer::Server

> **NOTE: AWS Backup Resource:** Resources (such as AMIs) created by AWS Backup are
> managed specifically by AWS Backup and cannot be deleted through standard APIs calls for that resource. These resources are tagged by AWS Backup and are filtered out so that Apocalypse does not fail when trying to delete resources it cannot delete.

### BEWARE!
When executed as `apocalypse.py aws`, this tool is **HIGHLY DESTRUCTIVE** and deletes all resources in all regions! This mode should never be used in a production environment!

### Usage

When targeting specific services or resource types it's important to know that the **service** is the string BEFORE the colons, the **resource-type** is the whole resource type string.

You can pass either **inspect-aws** to Apocalypse to get a view of all, or targeted, resources in the AWS account or simply **aws** to nuke all/targeted resources. Passing the **\-\-list-resource-types** argument to either of these will simply give you a list of currently supported resource type strings.

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
    "exclude_services": [],
    "exclude_resource_types": [],
    "resource_types": [],
    "services": []
}
```
When using a configuration file you can specifically blacklist, or whitelist, accounts that Apocalypse can be executed in.

## Extending
We use the **Registry** pattern to add a new service/resource type to Apocalypse. You simply need to create 2 new functions in an appropriate .py file in the **services/** folder. These functions need to be decorated with the *register_query_function* and *register_terminate_function* and ensure that the parameters match the existing ones (session and region for both, and resource_arns for the terminate function).
