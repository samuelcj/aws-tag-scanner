import boto3
from botocore.exceptions import ClientError

# Initialize Boto3 client for resourcegroupstaggingapi
tagging_client = boto3.client('resourcegroupstaggingapi')

# Function to check if the resource has the "AppName" tag
def check_resource_tags(resource_arn, tag_key="AppName"):
    try:
        # Get tags for a specific resource ARN
        response = tagging_client.get_tags(ResourceARNList=[resource_arn])
        
        for resource in response['ResourceTagMappingList']:
            for tag in resource['Tags']:
                if tag_key in tag:
                    print(f"Resource {resource_arn} has '{tag_key}' tag: {tag[tag_key]}")
                    return  # Tag found, no need to continue checking.
        print(f"Resource {resource_arn} does not have the '{tag_key}' tag.")
    except ClientError as e:
        print(f"Error getting tags for {resource_arn}: {e}")

# Function to scan resources in the AWS account
def scan_resources_for_tags(tag_key="AppName"):
    try:
        # Paginate through resources
        paginator = tagging_client.get_paginator('get_resources')
        for page in paginator.paginate():
            for resource in page['ResourceTagMappingList']:
                resource_arn = resource['ResourceARN']
                check_resource_tags(resource_arn, tag_key)
    except ClientError as e:
        print(f"Error scanning resources: {e}")

# Execute the function to scan resources
if __name__ == '__main__':
    scan_resources_for_tags("SnowAppName")  # You can specify another tag key if needed

