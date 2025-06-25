# RDS Snapshot Automation

This project provides automated RDS snapshot creation and cross-region copying using AWS Lambda and manual console approaches.

## Author
```
Ishmael Gyamfi (June 2025)
```

## Overview

The solution creates RDS snapshots and copies them to a different AWS region for disaster recovery and backup purposes. It includes proper error handling and KMS encryption support.

## Table of Contents

- [Prerequisites](#prerequisites)
- [IAM Permissions](#iam-permissions)
- [Approach 1: Lambda Automation](#approach-1-lambda-automation)
- [Approach 2: Console Manual Process](#approach-2-console-manual-process)
- [Common Errors and Troubleshooting](#common-errors-and-troubleshooting)
- [KMS Cross-Region Issues](#kms-cross-region-issues)
- [Best Practices](#best-practices)

## Prerequisites

- AWS CLI configured or appropriate IAM roles
- RDS instance running in source region
- KMS key available in destination region (for encrypted snapshots)
- Python 3.9+ (for Lambda approach)

## IAM Permissions

The following IAM policy is required for both approaches:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "rds:CreateDBSnapshot",
                "rds:CopyDBSnapshot",
                "rds:DescribeDBSnapshots",
                "rds:DescribeDBInstances"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "kms:Decrypt",
                "kms:DescribeKey",
                "kms:Encrypt",
                "kms:GenerateDataKey",
                "kms:ReEncrypt*"
            ],
            "Resource": "*"
        }
    ]
}
```

## Approach 1: Lambda Automation

### Setup

1. **Configure the Lambda function:**
   - Update variables in `lambda_function.py`:
     ```python
     source_region = 'us-east-1'  # Your source region
     destination_region = 'us-west-2'  # Your destination region
     db_instance_identifier = 'your-db-instance'
     account_id = 'your-aws-account-id'
     ```

2. **Deploy Lambda:**
   - Runtime: Python 3.9+
   - Timeout: 15 minutes (snapshots can take time)
   - Memory: 128 MB (sufficient for this task)

3. **Set up triggers:**
   - CloudWatch Events/EventBridge for scheduled execution
   - Manual invocation for testing

### Lambda Function Features

- Automatic timestamp-based naming
- Waiter implementation for snapshot availability
- Cross-region copying with KMS support
- Comprehensive error handling

## Approach 2: Console Manual Process

### Step-by-Step Console Process

1. **Create Snapshot:**
   - Navigate to RDS Console → Snapshots
   - Click "Create snapshot"
   - Select your DB instance
   - Enter snapshot identifier: `manual-snapshot-YYYYMMDD-HHMMSS`
   - Click "Create snapshot"

2. **Wait for Completion:**
   - Monitor snapshot status until "Available"
   - This can take 5-30 minutes depending on DB size

3. **Copy to Destination Region:**
   - Switch to destination region in console
   - Go to Snapshots → "Copy snapshot"
   - Select source region and snapshot
   - Configure KMS encryption if needed
   - Enter new snapshot identifier
   - Click "Copy snapshot"

### Console Advantages
- Visual feedback and progress monitoring
- Easy troubleshooting through UI
- No code deployment required

### Console Disadvantages
- Manual process prone to human error
- Not suitable for regular automation
- Time-consuming for frequent backups

## Common Errors and Troubleshooting

### 1. Snapshot Creation Failures

**Error:** `InvalidDBInstanceState`
```
DB instance is not in available state
```
**Solution:** Ensure DB instance is in "Available" state, not "Backing up" or "Modifying"

**Error:** `SnapshotQuotaExceeded`
```
Cannot create more than 100 manual snapshots
```
**Solution:** Delete old snapshots or request quota increase

### 2. Cross-Region Copy Failures

**Error:** `InvalidParameterValue`
```
Invalid source snapshot identifier
```
**Solution:** Use full ARN format:
```python
snapshot_arn = f'arn:aws:rds:{source_region}:{account_id}:snapshot:{snapshot_name}'
```

### 3. Lambda Timeout Issues

**Error:** `Task timed out after X seconds`
**Solution:** 
- Increase Lambda timeout to 15 minutes
- Implement asynchronous processing with SQS/SNS
- Use Step Functions for complex workflows

### 4. Permission Errors

**Error:** `AccessDenied`
```
User is not authorized to perform: rds:CopyDBSnapshot
```
**Solution:** Verify IAM policy includes all required permissions

## KMS Cross-Region Issues

### Common KMS Errors

**Error:** `KMSKeyNotAccessibleFault`
```
The request failed because the specified KMS key isn't accessible
```

**Error:** `InvalidParameterValue`
```
Invalid KMS key identifier
```

### KMS Solutions

1. **Use Destination Region KMS Key:**
   ```python
   # Correct - use destination region KMS key
   KmsKeyId='arn:aws:kms:us-west-2:123456789012:key/abcd1234-...'
   ```

2. **Create KMS Key in Destination Region:**
   ```bash
   aws kms create-key --region us-west-2 --description "RDS Cross-region copy key"
   ```

3. **Grant Cross-Account Access (if needed):**
   ```json
   {
     "Effect": "Allow",
     "Principal": {"AWS": "arn:aws:iam::ACCOUNT-ID:root"},
     "Action": [
       "kms:Decrypt",
       "kms:DescribeKey"
     ],
     "Resource": "*"
   }
   ```

### KMS Best Practices

- Always use KMS key from destination region
- Store KMS key ARN in environment variables
- Use AWS managed keys (`alias/aws/rds`) for simplicity
- Test KMS permissions before automation

## Best Practices

### Naming Conventions
```python
# Good naming with timestamps
snapshot_name = f'rds-backup-{db_name}-{timestamp}'
copy_name = f'rds-copy-{db_name}-{timestamp}'
```

### Error Handling
```python
try:
    # RDS operations
except ClientError as e:
    error_code = e.response['Error']['Code']
    if error_code == 'DBSnapshotAlreadyExists':
        # Handle duplicate snapshot
    elif error_code == 'InvalidDBInstanceState':
        # Handle invalid state
```

### Monitoring
- Set up CloudWatch alarms for Lambda failures
- Use SNS notifications for success/failure
- Log all operations with timestamps

### Cost Optimization
- Implement snapshot lifecycle management
- Delete old snapshots automatically
- Use appropriate storage classes

### Security
- Use least privilege IAM policies
- Encrypt snapshots with customer-managed KMS keys
- Enable VPC endpoints for private communication

## Troubleshooting Checklist

- [ ] Verify IAM permissions
- [ ] Check DB instance state
- [ ] Confirm KMS key accessibility
- [ ] Validate region configurations
- [ ] Review CloudWatch logs
- [ ] Test with smaller DB instances first
- [ ] Ensure sufficient snapshot quota

## Support

For additional help:
- Check AWS RDS documentation
- Review CloudWatch logs for detailed error messages
- Use AWS Support for complex KMS issues
- Test in development environment first