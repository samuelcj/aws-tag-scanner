import boto3
import pandas as pd
from botocore.exceptions import ClientError
from datetime import datetime

# Get list of all regions
def get_all_regions():
    ec2_client = boto3.client("ec2", region_name="us-east-1")  # Use any region to get the list of all regions
    regions = ec2_client.describe_regions()
    return [region["RegionName"] for region in regions["Regions"]]

# AWS Clients initialization for required services
def get_clients(region):
    tagging_client = boto3.client("resourcegroupstaggingapi", region_name=region)
    ec2_client = boto3.client("ec2", region_name=region)
    return tagging_client, ec2_client  # No need for S3 client in region loop

# Get AWS Account ID (Needed for EC2 ARNs)
sts_client = boto3.client("sts")
account_id = sts_client.get_caller_identity()["Account"]

# Required tags to check (configurable)
REQUIRED_TAGS = ["AppName", "AppCode"]

# Function to scan resources without any tags OR missing required tags across multiple regions
def scan_resources_missing_tags(output_file_prefix="multi_region_missing_tags_scanner"):
    missing_tag_data = []
    existing_resources = set()  # Track resources to prevent duplicates

    regions = get_all_regions()  # Fetch all AWS regions

    try:
        # 📌 Scan S3 Buckets (Global Resource - Scan Only Once)
        s3_client = boto3.client("s3")  # S3 is global, so no region is needed
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
                        "Missing Tags": ", ".join(missing_tags) if missing_tags else "No Tags",
                        "Region": "Global (S3)"  # S3 buckets are global, so no specific region
                    })
                    existing_resources.add(bucket_arn)

        # 📌 Scan Other Resources (EC2, Tagging API) in Each Region
        for region in regions:
            print(f"Scanning region: {region}")
            tagging_client, ec2_client = get_clients(region)

            # 📌 1. Scan resources using Resource Groups Tagging API (Exclude S3 Buckets)
            paginator = tagging_client.get_paginator("get_resources")
            for page in paginator.paginate():
                for resource in page["ResourceTagMappingList"]:
                    resource_arn = resource["ResourceARN"]

                    # Skip S3 buckets (already scanned globally)
                    if ":s3:::" in resource_arn:
                        continue

                    tags = {tag["Key"]: tag["Value"] for tag in resource.get("Tags", [])}

                    missing_tags = [tag for tag in REQUIRED_TAGS if tag not in tags]

                    if not tags or missing_tags:  # No tags OR missing required tags
                        missing_tag_data.append({
                            "Resource ARN": resource_arn,
                            "Missing Tags": ", ".join(missing_tags) if missing_tags else "No Tags",
                            "Region": region
                        })
                        existing_resources.add(resource_arn)

            # 📌 2. Scan EC2 Instances (Ensure Full ARN)
            ec2_instances = ec2_client.describe_instances()["Reservations"]
            for reservation in ec2_instances:
                for instance in reservation["Instances"]:
                    instance_id = instance["InstanceId"]
                    instance_arn = f"arn:aws:ec2:{region}:{account_id}:instance/{instance_id}"

                    if instance_arn not in existing_resources:
                        tags = {tag["Key"]: tag["Value"] for tag in instance.get("Tags", [])} if "Tags" in instance else {}

                        missing_tags = [tag for tag in REQUIRED_TAGS if tag not in tags]

                        if not tags or missing_tags:
                            missing_tag_data.append({
                                "Resource ARN": instance_arn,
                                "Missing Tags": ", ".join(missing_tags) if missing_tags else "No Tags",
                                "Region": region
                            })

        # Save results to Excel with a timestamp
        if missing_tag_data:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"{output_file_prefix}_{timestamp}.xlsx"
            df = pd.DataFrame(missing_tag_data)
            df.to_excel(output_file, index=False)
            print(f"Resources without tags or missing required tags saved to {output_file}")
        else:
            print("All resources have the required tags.")

    except ClientError as e:
        print(f"Error scanning resources: {e}")

# Run the function
if __name__ == "__main__":
    scan_resources_missing_tags()
