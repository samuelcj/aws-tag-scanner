import boto3
from botocore.exceptions import ClientError

# Initialize Boto3 client for resourcegroupstaggingapi
tagging_client = boto3.client('resourcegroupstaggingapi', region_name='us-east-1')

# Function to check if the resource has the "AppName" tag
def check_resource_tags_without_AppName(resource_arn, tag_key="AppName"):
    try:
        # Get tags for a specific resource ARN
        response = tagging_client.get_resources(ResourceTypeFilters=[], TagFilters=[{"Key": tag_key}])
        
        for resource in response['ResourceTagMappingList']:
            for tag in resource['Tags']:
                if tag_key in tag:
                    return False  # Tag found, return False (do not print)
        return True  # Tag not found, return True (should print)
    except ClientError as e:
        print(f"Error getting tags for {resource_arn}: {e}")
        return True  # In case of error, assume the resource has no "AppName" tag

# Function to scan resources and print those without the "AppName" tag
def scan_resources_without_AppName(tag_key="AppName"):
    try:
        # Paginate through resources
        paginator = tagging_client.get_paginator('get_resources')
        for page in paginator.paginate():
            for resource in page['ResourceTagMappingList']:
                resource_arn = resource['ResourceARN']
                if check_resource_tags_without_AppName(resource_arn, tag_key):
                    print(f"Resource {resource_arn} does not have the '{tag_key}' tag.")
    except ClientError as e:
        print(f"Error scanning resources: {e}")

# Execute the function to scan resources
if __name__ == '__main__':
    scan_resources_without_AppName("AppName") 
