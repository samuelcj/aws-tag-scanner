import boto3
import pandas as pd
from botocore.exceptions import ClientError

# AWS Clients
tagging_client = boto3.client("resourcegroupstaggingapi", region_name="us-east-1")
ec2_client = boto3.client("ec2", region_name="us-east-1")
s3_client = boto3.client("s3", region_name="us-east-1")

# Get AWS Account ID (Needed for EC2 ARNs)
sts_client = boto3.client("sts")
account_id = sts_client.get_caller_identity()["Account"]

# Required tags to check
REQUIRED_TAGS = ["AppName", "AppCode"]

# Function to scan resources without any tags OR missing required tags
def scan_resources_missing_tags(output_file="missing_tags_scanner.xlsx"):
    missing_tag_data = []
    existing_resources = set()  # Track resources to prevent duplicates

    try:
        # 📌 1. Scan resources using Resource Groups Tagging API
        paginator = tagging_client.get_paginator("get_resources")
        for page in paginator.paginate():
            for resource in page["ResourceTagMappingList"]:
                resource_arn = resource["ResourceARN"]
                tags = {tag["Key"]: tag["Value"] for tag in resource.get("Tags", [])}

                missing_tags = [tag for tag in REQUIRED_TAGS if tag not in tags]

                if not tags or missing_tags:  # No tags OR missing required tags
                    missing_tag_data.append({
                        "Resource ARN": resource_arn,
                        "Missing Tags": ", ".join(missing_tags) if missing_tags else "No Tags"
                    })
                    existing_resources.add(resource_arn)

        # 📌 2. Scan EC2 Instances (Ensure Full ARN)
        ec2_instances = ec2_client.describe_instances()["Reservations"]
        for reservation in ec2_instances:
            for instance in reservation["Instances"]:
                instance_id = instance["InstanceId"]
                instance_arn = f"arn:aws:ec2:us-east-1:{account_id}:instance/{instance_id}"

                if instance_arn not in existing_resources:
                    tags = {tag["Key"]: tag["Value"] for tag in instance.get("Tags", [])} if "Tags" in instance else {}

                    missing_tags = [tag for tag in REQUIRED_TAGS if tag not in tags]

                    if not tags or missing_tags:
                        missing_tag_data.append({
                            "Resource ARN": instance_arn,
                            "Missing Tags": ", ".join(missing_tags) if missing_tags else "No Tags"
                        })

        # 📌 3. Scan S3 Buckets (Ensure Full ARN)
        s3_buckets = s3_client.list_buckets()["Buckets"]
        for bucket in s3_buckets:
            bucket_name = bucket["Name"]
            bucket_arn = f"arn:aws:s3:::{bucket_name}"

            if bucket_arn not in existing_resources:
                tags = None
                try:
                    tags = {tag["Key"]: tag["Value"] for tag in s3_client.get_bucket_tagging(Bucket=bucket_name)["TagSet"]}
                except ClientError as e:
                    if e.response["Error"]["Code"] == "NoSuchTagSet":
                        tags = {}

                missing_tags = [tag for tag in REQUIRED_TAGS if tag not in tags]

                if not tags or missing_tags:
                    missing_tag_data.append({
                        "Resource ARN": bucket_arn,
                        "Missing Tags": ", ".join(missing_tags) if missing_tags else "No Tags"
                    })

        # Save results to Excel
        if missing_tag_data:
            df = pd.DataFrame(missing_tag_data)
            df.to_excel(output_file, index=False)
            print(f"Resources without tags or missing required tags saved to {output_file}")
        else:
            print("All resources have the required tags.")

    except ClientError as e:
        print(f"Error scanning resources: {e}")

# Run the function
if __name__ == "__main__":
    scan_resources_missing_tags("missing_tags_scanner.xlsx")

