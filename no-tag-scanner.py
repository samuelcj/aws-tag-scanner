import boto3
import pandas as pd
from botocore.exceptions import ClientError

# Initialize AWS clients
tagging_client = boto3.client("resourcegroupstaggingapi", region_name="us-east-1")
ec2_client = boto3.client("ec2", region_name="us-east-1")
s3_client = boto3.client("s3", region_name="us-east-1")

# Function to scan resources without tags
def scan_resources_without_tags(output_file="resources_without_tags.xlsx"):
    resources_without_tags = []

    try:
        # 📌 1. Use Resource Groups Tagging API (Covers many services)
        paginator = tagging_client.get_paginator("get_resources")
        for page in paginator.paginate():
            for resource in page["ResourceTagMappingList"]:
                resource_arn = resource["ResourceARN"]
                tags = resource.get("Tags", [])

                if not tags:  # If no tags exist
                    resources_without_tags.append({"Resource ARN": resource_arn, "Service": "Generic"})

        # 📌 2. Manually Check EC2 Instances
        ec2_instances = ec2_client.describe_instances()["Reservations"]
        for reservation in ec2_instances:
            for instance in reservation["Instances"]:
                instance_id = instance["InstanceId"]
                tags = instance.get("Tags", [])
                
                if not tags:
                    resources_without_tags.append({"Resource ARN": f"EC2 Instance: {instance_id}", "Service": "EC2"})

        # 📌 3. Manually Check S3 Buckets
        s3_buckets = s3_client.list_buckets()["Buckets"]
        for bucket in s3_buckets:
            bucket_name = bucket["Name"]
            tags = None
            try:
                tags = s3_client.get_bucket_tagging(Bucket=bucket_name)["TagSet"]
            except ClientError as e:
                if e.response["Error"]["Code"] == "NoSuchTagSet":
                    tags = []

            if not tags:
                resources_without_tags.append({"Resource ARN": f"S3 Bucket: {bucket_name}", "Service": "S3"})

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
import boto3
import pandas as pd
from botocore.exceptions import ClientError

# Initialize AWS clients
tagging_client = boto3.client("resourcegroupstaggingapi", region_name="us-east-1")
ec2_client = boto3.client("ec2", region_name="us-east-1")
s3_client = boto3.client("s3", region_name="us-east-1")

# Function to scan resources without tags
def scan_resources_without_tags(output_file="resources_without_tags.xlsx"):
    resources_without_tags = []

    try:
        # 📌 1. Use Resource Groups Tagging API (Covers many services)
        paginator = tagging_client.get_paginator("get_resources")
        for page in paginator.paginate():
            for resource in page["ResourceTagMappingList"]:
                resource_arn = resource["ResourceARN"]
                tags = resource.get("Tags", [])

                if not tags:  # If no tags exist
                    resources_without_tags.append({"Resource ARN": resource_arn, "Service": "Generic"})

        # 📌 2. Manually Check EC2 Instances
        ec2_instances = ec2_client.describe_instances()["Reservations"]
        for reservation in ec2_instances:
            for instance in reservation["Instances"]:
                instance_id = instance["InstanceId"]
                tags = instance.get("Tags", [])
                
                if not tags:
                    resources_without_tags.append({"Resource ARN": f"EC2 Instance: {instance_id}", "Service": "EC2"})

        # 📌 3. Manually Check S3 Buckets
        s3_buckets = s3_client.list_buckets()["Buckets"]
        for bucket in s3_buckets:
            bucket_name = bucket["Name"]
            tags = None
            try:
                tags = s3_client.get_bucket_tagging(Bucket=bucket_name)["TagSet"]
            except ClientError as e:
                if e.response["Error"]["Code"] == "NoSuchTagSet":
                    tags = []

            if not tags:
                resources_without_tags.append({"Resource ARN": f"S3 Bucket: {bucket_name}", "Service": "S3"})

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

