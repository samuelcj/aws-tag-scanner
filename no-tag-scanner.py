import boto3
import pandas as pd
from botocore.exceptions import ClientError

# AWS Clients
tagging_client = boto3.client("resourcegroupstaggingapi", region_name="us-east-1")
ec2_client = boto3.client("ec2", region_name="us-east-1")
s3_client = boto3.client("s3", region_name="us-east-1")

# AWS Account ID (Needed for constructing some ARNs)
sts_client = boto3.client("sts")
account_id = sts_client.get_caller_identity()["Account"]

# Function to scan resources without tags
def scan_resources_without_tags(output_file="resources_without_tags.xlsx"):
    resources_without_tags = []
    existing_resources = set()  # Track already scanned resources to prevent duplicates

    try:
        # 📌 1. Use Resource Groups Tagging API (Generic Scan)
        paginator = tagging_client.get_paginator("get_resources")
        for page in paginator.paginate():
            for resource in page["ResourceTagMappingList"]:
                resource_arn = resource["ResourceARN"]  # Get full ARN
                tags = resource.get("Tags", [])

                if not tags:  # If no tags exist
                    resources_without_tags.append({"Resource ARN": resource_arn, "Service": "Generic"})
                    existing_resources.add(resource_arn)  # Track to prevent duplicates

        # 📌 2. Scan EC2 Instances (Ensure Full ARN)
        ec2_instances = ec2_client.describe_instances()["Reservations"]
        for reservation in ec2_instances:
            for instance in reservation["Instances"]:
                instance_id = instance["InstanceId"]
                instance_arn = f"arn:aws:ec2:us-east-1:{account_id}:instance/{instance_id}"  # EC2 ARN Format

                if instance_arn not in existing_resources:  # Only add if not already included
                    tags = instance.get("Tags", [])
                    if not tags:
                        resources_without_tags.append({"Resource ARN": instance_arn, "Service": "EC2"})

        # 📌 3. Scan S3 Buckets (Ensure Full ARN)
        s3_buckets = s3_client.list_buckets()["Buckets"]
        for bucket in s3_buckets:
            bucket_name = bucket["Name"]
            bucket_arn = f"arn:aws:s3:::{bucket_name}"  # S3 ARN Format

            if bucket_arn not in existing_resources:  # Only add if not already included
                tags = None
                try:
                    tags = s3_client.get_bucket_tagging(Bucket=bucket_name)["TagSet"]
                except ClientError as e:
                    if e.response["Error"]["Code"] == "NoSuchTagSet":
                        tags = []

                if not tags:
                    resources_without_tags.append({"Resource ARN": bucket_arn, "Service": "S3"})

        # Save results to Excel
        if resources_without_tags:
            df = pd.DataFrame(resources_without_tags)
            df.to_excel(output_file, index=False)
            print(f"Resources without tags saved to {output_file}")
        else:
            print("All resources have tags.")

    except ClientError as e:
        print(f"Error scanning resources: {e}")

# Run the function
if __name__ == "__main__":
    scan_resources_without_tags("resources_without_tags.xlsx")

