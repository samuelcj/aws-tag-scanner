import boto3
from botocore.exceptions import ClientError

# Initialize Boto3 client for resourcegroupstaggingapi
tagging_client = boto3.client('resourcegroupstaggingapi', region_name='us-east-1')

# Function to scan resources and print those missing one or both tags
def scan_resources_missing_tags(required_tags=None):
    if required_tags is None:
        required_tags = ["AppName", "AppCode"]  # Default required tags

    try:
        # Paginate through resources
        paginator = tagging_client.get_paginator('get_resources')
        for page in paginator.paginate():
            for resource in page['ResourceTagMappingList']:
                resource_arn = resource['ResourceARN']
                
                # Extract tags as a dictionary
                tags = {tag['Key']: tag['Value'] for tag in resource.get('Tags', [])}
                
                # Check if any required tag is missing
                missing_tags = [tag for tag in required_tags if tag not in tags]
                
                if missing_tags:
                    print(f"Resource {resource_arn} is missing tags: {', '.join(missing_tags)}")
                    
    except ClientError as e:
        print(f"Error scanning resources: {e}")

# Execute the function
if __name__ == '__main__':
    scan_resources_missing_tags(["AppName", "AppCode"])  # Specify required tags

