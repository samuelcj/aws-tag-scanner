# AWS Resource Tag Scanner

## Overview
This script scans AWS resources across your account and identifies:
- Resources that are **missing all tags**
- Resources that **lack either or both** of the required tags (`SnowAppName`, `SnowAppCode`)
- Outputs the results in an Excel file (`missing_tags_scanner.xlsx`)

## Features
- Uses **Boto3** to interact with AWS services
- Supports **EC2 instances, S3 buckets, and other tagged resources**
- **Pagination** ensures all resources are scanned
- Outputs full **ARNs** for better tracking

## Prerequisites
Ensure you have the following installed:
- Python 3.x
- Boto3 (`pip install boto3`)
- Pandas (`pip install pandas`)

## AWS Permissions
The script requires the following AWS permissions:
```json
{
  "Effect": "Allow",
  "Action": [
    "tag:GetResources",
    "ec2:DescribeInstances",
    "s3:ListAllMyBuckets",
    "s3:GetBucketTagging",
    "sts:GetCallerIdentity"
  ],
  "Resource": "*"
}
```

## Setup & Usage
### 1. Clone the Repository
```sh
git clone <your-repo-url>
cd <your-repo-folder>
```

### 2. Install Dependencies
```sh
pip install -r requirements.txt  # If you add a requirements.txt file
```

### 3. Run the Script
```sh
python scan_missing_tags.py
```

### 4. Output
After execution, the results will be saved in:
```sh
missing_tags_scanner.xlsx
```

## Notes
- Ensure your AWS credentials are properly configured using `aws configure` or environment variables.
- Modify `REQUIRED_TAGS` in the script to scan for other required tags.

## License
This project is open-source and licensed under the MIT License.


