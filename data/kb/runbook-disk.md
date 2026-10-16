# Server Disk Space Runbook

## Disk above 90% full
1. Identify the largest folders with a disk-usage tool. Do not delete anything before the owner confirms.
2. Check for old backup sets, log files and temporary files that exceed the retention policy.
3. Verify the next scheduled backup has enough free space to complete.
4. If cleanup is not enough, raise a capacity expansion request and attach the usage report.

## Backup safety
Do not run cleanup on the backup volume itself without the backup administrator's approval.
