import boto3
import os
from datetime import datetime

source_region = 'source-region'
destination_region = 'destination-region'
db_instance_identifier = 'mainline-pro-db'
account_id = 'add-your-aws-account-id-here'

# Generate unique names using current date & time
timestamp = datetime.utcnow().strftime('%Y%m%d-%H%M%S')
snapshot_name = f'rds-auto-snapshot-mainline-{timestamp}'
copy_name = f'rds-auto-copy-mainline-{timestamp}'

rds = boto3.client('rds', region_name=source_region)

def lambda_handler(event, context):
    try:
        # Step 1: Create snapshot
        create_response = rds.create_db_snapshot(
            DBInstanceIdentifier=db_instance_identifier,
            DBSnapshotIdentifier=snapshot_name
        )
        print("Snapshot creation initiated:", snapshot_name)

        # Step 2: Wait for snapshot to become 'available'
        print("⏳ Waiting for snapshot to become available...")
        waiter = rds.get_waiter('db_snapshot_available')
        waiter.wait(
            DBSnapshotIdentifier=snapshot_name,
            WaiterConfig={'Delay': 30, 'MaxAttempts': 10}
        )
        print("Snapshot is now available!")

        # Step 3: Copy snapshot to destination region
        snapshot_arn = f'arn:aws:rds:{source_region}:{account_id}:snapshot:{snapshot_name}'
        dest_rds = boto3.client('rds', region_name=destination_region)

        copy_response = dest_rds.copy_db_snapshot(
            SourceDBSnapshotIdentifier=snapshot_arn,
            TargetDBSnapshotIdentifier=copy_name,
            SourceRegion=source_region,
            KmsKeyId='arn:aws:kms:eu-central-1:412381770444:key/c6d78a6d-854d-4e15-9fc7-b4ee1c15131c'
        )

        print("Snapshot copy initiated:", copy_name)

        return {
            "statusCode": 200,
            "body": f"Snapshot {snapshot_name} created and copied as {copy_name} to {destination_region}"
        }

    except Exception as e:
        print("Error occurred:", str(e))
        return {
            "statusCode": 500,
            "body": f"Failed: {str(e)}"
        }