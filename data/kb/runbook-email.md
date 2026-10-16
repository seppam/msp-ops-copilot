# Email Deliverability Runbook

## Outgoing mail lands in spam
1. Check the sending domain's SPF, DKIM and DMARC records. A missing or broken record is the most common cause.
2. Check whether the sending IP is on a public blocklist.
3. Review recent changes: new mail provider, changed DNS, new invoicing or marketing tool sending on the domain's behalf.
4. Send a test message to a mail-tester service and review the score.
5. If a third-party tool sends invoices, make sure it is included in the SPF record and signs with DKIM.

## Escalation
If the domain is blocklisted, notify the security lead before requesting delisting.
