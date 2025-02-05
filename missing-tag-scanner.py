import boto3
import pandas as pd
from botocore.exceptions import ClientError

# Initialize Boto3 client for resourcegroupstaggingapi
tagging_client = boto3.client('resourcegroupstaggingapi', region_name='us-east-1')

# Function to scan resources and save missing tags to an Excel file
def scan_resources_missing_tags(required_tags=None, output_file="missing_tags.xlsx"):
    if required_tags is None:
        required_tags = ["AppName", "AppCode"]  # Default required tags

    missing_tag_data = []  # Store results here

    try:
        # Paginate through resources
        paginator = tagging_client.get_paginator('get_resources')
        for page in paginator.paginate():
            for resource in page['ResourceTagMappingList']:
                resource_arn = resource['ResourceARN']
                
                # Extract tags as a dictionary
                tags = {tag['Key']: tag['Value'] for tag in resource.get('Tags', [])}
                
                # Check which required tags are missing
                missing_tags = [tag for tag in required_tags if tag not in tags]
                
                if missing_tags:
                    missing_tag_data.append({"Resource ARN": resource_arn, "Missing Tags": ", ".join(missing_tags)})
                    
        # Convert results to a DataFrame and save to Excel
        if missing_tag_data:
            df = pd.DataFrame(missing_tag_data)
            df.to_excel(output_file, index=False)
            print(f"Results saved to {output_file}")
        else:
            print("All resources have the required tags.")

    except ClientError as e:
        print(f"Error scanning resources: {e}")

# Execute the function
if __name__ == '__main__':
    scan_resources_missing_tags(["AppName", "AppCode"], "missing_tags.xlsx")  # Specify required tags & output file

