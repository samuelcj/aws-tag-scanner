import boto3
import pandas as pd
from botocore.exceptions import ClientError
from datetime import datetime

# Initialize AWS session
session = boto3.session.Session()

# Get AWS Account ID
account_id = session.client("sts").get_caller_identity()["Account"]

# Required tags to check
REQUIRED_TAGS = {"AppName", "AppCode"}

# Define global services
GLOBAL_SERVICES = {"s3", "iam", "cloudfront", "route53", "organizations"}

# Scan global resources that may have no tags
def scan_global_resources(missing_tag_data, existing_resources):
    print("Scanning global resources...")

    # 1. Scan S3 Buckets
    s3_client = session.client("s3")
    for bucket in s3_client.list_buckets()["Buckets"]:
        bucket_name = bucket["Name"]
        bucket_arn = f"arn:aws:s3:::{bucket_name}"
        if bucket_arn in existing_resources:
            continue

        try:
            tags = {tag["Key"]: tag["Value"] for tag in s3_client.get_bucket_tagging(Bucket=bucket_name)["TagSet"]}
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchTagSet":
                tags = {}

        if not tags:
            missing_tag_data.append({"Resource ARN": bucket_arn, "Missing Tags": "No Tags", "Region": "Global (S3)"})
        else:
            missing_tags = REQUIRED_TAGS - tags.keys()
            if missing_tags:
                missing_tag_data.append({"Resource ARN": bucket_arn, "Missing Tags": ", ".join(missing_tags), "Region": "Global (S3)"})
        existing_resources.add(bucket_arn)

    # 2. Scan IAM Roles
    iam_client = session.client("iam")
    for role in iam_client.list_roles()["Roles"]:
        role_arn = role["Arn"]
        if role_arn in existing_resources:
            continue

        tags = {tag["Key"]: tag["Value"] for tag in iam_client.list_role_tags(RoleName=role["RoleName"]).get("Tags", [])}
        if not tags:
            missing_tag_data.append({"Resource ARN": role_arn, "Missing Tags": "No Tags", "Region": "Global (IAM)"})
        else:
            missing_tags = REQUIRED_TAGS - tags.keys()
            if missing_tags:
                missing_tag_data.append({"Resource ARN": role_arn, "Missing Tags": ", ".join(missing_tags), "Region": "Global (IAM)"})
        existing_resources.add(role_arn)

    # 3. Scan CloudFront Distributions
    cf_client = session.client("cloudfront")
    for dist in cf_client.list_distributions().get("DistributionList", {}).get("Items", []):
        dist_arn = f"arn:aws:cloudfront::{account_id}:distribution/{dist['Id']}"
        if dist_arn in existing_resources:
            continue

        try:
            tags = {tag["Key"]: tag["Value"] for tag in cf_client.list_tags_for_resource(Resource=dist_arn)["Tags"]["Items"]}
        except ClientError:
            tags = {}

        if not tags:
            missing_tag_data.append({"Resource ARN": dist_arn, "Missing Tags": "No Tags", "Region": "Global (CloudFront)"})
        else:
            missing_tags = REQUIRED_TAGS - tags.keys()
            if missing_tags:
                missing_tag_data.append({"Resource ARN": dist_arn, "Missing Tags": ", ".join(missing_tags), "Region": "Global (CloudFront)"})
        existing_resources.add(dist_arn)

    # 4. Scan Route 53 Hosted Zones
    r53_client = session.client("route53")
    for zone in r53_client.list_hosted_zones()["HostedZones"]:
        zone_arn = f"arn:aws:route53::{account_id}:hostedzone/{zone['Id'].split('/')[-1]}"
        if zone_arn in existing_resources:
            continue

        try:
            tags = {tag["Key"]: tag["Value"] for tag in r53_client.list_tags_for_resource(ResourceType="hostedzone", ResourceId=zone["Id"].split("/")[-1])["ResourceTagSet"]["Tags"]}
        except ClientError:
            tags = {}

        if not tags:
            missing_tag_data.append({"Resource ARN": zone_arn, "Missing Tags": "No Tags", "Region": "Global (Route53)"})
        else:
            missing_tags = REQUIRED_TAGS - tags.keys()
            if missing_tags:
                missing_tag_data.append({"Resource ARN": zone_arn, "Missing Tags": ", ".join(missing_tags), "Region": "Global (Route53)"})
        existing_resources.add(zone_arn)

# Scan regional resources
def scan_regional_resources(missing_tag_data, existing_resources):
    regions = [r["RegionName"] for r in session.client("ec2", region_name="us-east-1").describe_regions()["Regions"]]

    for region in regions:
        print(f"Scanning region: {region}")
        tagging_client = session.client("resourcegroupstaggingapi", region_name=region)
        ec2_client = session.client("ec2", region_name=region)

        # Scan all resources using the Tagging API
        paginator = tagging_client.get_paginator("get_resources")
        for page in paginator.paginate():
            for resource in page["ResourceTagMappingList"]:
                resource_arn = resource["ResourceARN"]

                # Skip global resources
                if resource_arn.split(":")[2] in GLOBAL_SERVICES or resource_arn in existing_resources:
                    continue

                tags = {tag["Key"]: tag["Value"] for tag in resource.get("Tags", [])}
                if not tags:
                    missing_tag_data.append({"Resource ARN": resource_arn, "Missing Tags": "No Tags", "Region": f"{region} ({resource_arn.split(':')[2].upper()})"})
                else:
                    missing_tags = REQUIRED_TAGS - tags.keys()
                    if missing_tags:
                        missing_tag_data.append({"Resource ARN": resource_arn, "Missing Tags": ", ".join(missing_tags), "Region": f"{region} ({resource_arn.split(':')[2].upper()})"})
                existing_resources.add(resource_arn)

        # Scan EC2 Instances
        for reservation in ec2_client.describe_instances().get("Reservations", []):
            for instance in reservation["Instances"]:
                instance_id = instance["InstanceId"]
                instance_arn = f"arn:aws:ec2:{region}:{account_id}:instance/{instance_id}"

                if instance_arn in existing_resources:
                    continue

                tags = {tag["Key"]: tag["Value"] for tag in instance.get("Tags", [])}
                if not tags:
                    missing_tag_data.append({"Resource ARN": instance_arn, "Missing Tags": "No Tags", "Region": f"{region} (EC2)"})
                else:
                    missing_tags = REQUIRED_TAGS - tags.keys()
                    if missing_tags:
                        missing_tag_data.append({"Resource ARN": instance_arn, "Missing Tags": ", ".join(missing_tags), "Region": f"{region} (EC2)"})
                existing_resources.add(instance_arn)

# Main function to run the scan
def scan_resources_missing_tags(output_file_prefix="multi_region_missing_tags_scanner"):
    missing_tag_data = []
    existing_resources = set()

    # Scan Global & Regional Resources
    scan_global_resources(missing_tag_data, existing_resources)
    scan_regional_resources(missing_tag_data, existing_resources)

    # Save results to Excel
    if missing_tag_data:
        output_file = f"{output_file_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        pd.DataFrame(missing_tag_data).to_excel(output_file, index=False)
        print(f"Resources without tags or missing required tags saved to {output_file}")
    else:
        print("All resources have the required tags.")

# Run script
if __name__ == "__main__":
    scan_resources_missing_tags()
