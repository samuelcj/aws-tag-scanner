import boto3
import pandas as pd
from botocore.exceptions import ClientError

# Initialize Boto3 client for resourcegroupstaggingapi
tagging_client = boto3.client('resourcegroupstaggingapi', region_name='us-east-1')

# Function to scan resources and list those without any tags
def scan_resources_without_tags(output_file="resources_without_tags.xlsx"):
    resources_without_tags = []  # Store results here

    try:
        # Use paginator to handle large datasets
        paginator = tagging_client.get_paginator('get_resources')
        
        for page in paginator.paginate():
            for resource in page['ResourceTagMappingList']:
                resource_arn = resource['ResourceARN']
                tags = resource.get('Tags', [])

                # If no tags exist, add resource to the list
                if not tags:
                    resources_without_tags.append({"Resource ARN": resource_arn})

        # Convert results to a DataFrame and save to Excel
        if resources_without_tags:
            df = pd.DataFrame(resources_without_tags)
            df.to_excel(output_file, index=False)
            print(f"Resources without tags saved to {output_file}")
        else:
            print("All resources have tags.")

    except ClientError as e:
        print(f"Error scanning resources: {e}")

# Execute the function
if __name__ == '__main__':
    scan_resources_without_tags("resources_without_tags.xlsx")

