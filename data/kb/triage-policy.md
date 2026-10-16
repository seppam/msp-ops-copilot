# Service Desk Triage Policy

## Priority definitions
- Critical: outage affecting many users or an entire site, active security incident, or imminent data loss. Response target 15 minutes.
- High: one or more users fully blocked from working, or a service degraded for a whole team. Response target 1 hour.
- Medium: a degraded service with a workaround, a time-bound request with at least 3 working days of notice. Response target 4 business hours.
- Low: routine requests, questions, cosmetic issues. Response target 1 business day.

## Storage and backup alerts
- A disk above 90% full on a server that holds backups or databases is High, because backup failure puts data at risk.
- A disk above 98% full, or any backup that has failed twice in a row, is Critical.
- Workstation disks are Medium unless the user is blocked.

## Categories
- network: VPN, Wi-Fi, firewall, DNS, internet connectivity.
- email: mail delivery, spam, mailbox access, mail flow rules.
- hardware: laptops, printers, peripherals, new-hire equipment.
- security: phishing, malware, account compromise, access reviews.
- storage: disk space, file servers, backups.
- other: anything that does not fit above.

## Rules for replies
- Never promise a fix time. State the response target for the priority instead.
- Always ask for the affected user names and the time the problem started if missing.
