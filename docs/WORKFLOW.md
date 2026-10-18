# Intake, follow-up and automation rules

How a ticket enters, what the system may do on its own, and what always needs a person. The aim is that the AI helps the ops team reach the SLA, and that a failure never leaves a ticket stuck.

## 1. Submission template

The requester picks values from lists and fills labelled fields. Anything a person can choose is a list, because free text is where wrong labels and missing information come from.

| Field | Input | Required for |
|---|---|---|
| Category | list: aplikasi, network, lainnya | all |
| Application, Menu | lists, menu depends on application | aplikasi |
| Problem description | text | all |
| Steps to reproduce | text, example shown | aplikasi |
| Example document number | text (invoice, DO, SO number) | aplikasi |
| Error message or screenshot | text or attachment | aplikasi |
| Start time | date and time | aplikasi, network |
| Affected users | one person / a team / everyone | aplikasi, network |
| Business deadline | optional: today, this week, none | optional |

A field filled with "-", "tidak tahu" or empty counts as missing. Rules for this live in `intake.py` and are checked by code before the model is involved: free, instant, and the same every time. The model only judges what code cannot, such as whether the text really describes the steps.

The rendered ticket is plain `Label: value` lines in the Odoo task description, readable by people and parseable by code.

## 2. What happens after triage

| Outcome | Automatic (information only) | Needs a person to approve |
|---|---|---|
| Any ticket | Acknowledge receipt to the requester, with no promise about timing or fix | |
| Missing information | Hold assignment | Send the drafted ask-back email |
| Route to comsec / network / business / service request | | Assign with a context pack |
| Support team handles it | | Assign to an ops engineer, send the drafted workaround message |
| P1, review, or project handover | Alert the Team Leader | The handover decision itself |
| needs_human, escalate, delete request, possible prompt injection | Alert the Team Leader and hold the ticket | Everything else |
| AI fails (rate limit, invalid output, outage) | Fall back to the normal manual queue and alert the ops lead | |

Rules behind the table:
1. **Nothing that changes business data, assigns work or sets customer expectations is automatic.** The plan is produced by `actions.py` as data; nothing is sent from there.
2. **Dangerous cases get no automatic follow-up.** Deletion requests, injection attempts and anything marked escalate only notify the Team Leader.
3. **Automation fails open to humans.** If the AI step breaks, the ticket still reaches the ops queue and someone is told. It is never blocked or dropped.
4. **The SLA clock starts at assignment**, so slow or wrong assignment costs the most. The ask-back email goes out before assignment so the assignee can start immediately.

## 3. Follow-up emails

Wording is a fixed template controlled by the ops team. The model only chooses which items are missing, which keeps the tone consistent and removes the risk of the model promising something. Emails are reviewed before sending. Local testing uses a mail catcher (nothing leaves the machine).

## 4. Earning more autonomy

Approval gates can be removed one at a time, only when measured results justify it on the labelled set:
- Level 0 (now): everything except acknowledgements and Team Leader alerts is a draft.
- Level 1: automatic ask-back emails for pure missing-information cases. Needs high precision on `missing_info` (currently 31 to 80% depending on model and run, so not yet).
- Level 2: automatic routing for the categories with proven accuracy.
Dangerous cases never move beyond a notification.

## 5. Open points

- Ask-back reminder timing and what happens when the requester never answers.
- Whether the SLA clock pauses while waiting for the requester.
- Real mail delivery needs an SMTP account and real recipients, which is out of scope for the mock project.
