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

## 2. What happens after triage (phase 1)

Every ticket is assigned straight to the right team's PIC (person in charge): ops by default, or comsec, the network team or the business team when the triage points there. **Escalation always goes through the ops PIC**, who decides whether to involve the Team Leader or the project team. The system never contacts the Team Leader or the project team itself.

| Outcome | What the system does automatically | What stays with the PIC |
|---|---|---|
| Every ticket | Assign the PIC of the right team. Send ONE formal email to the requester: the ticket is in the system, here is the PIC, please wait for the PIC's follow-up email | Check the ticket |
| Information missing | Same email also asks for the missing items, with a line "if you already provided this, please ignore". Vague reports (priority unknown or 3+ gaps) also give the PIC first checks: 1) system availability, 2) network from the requester's site and from another site, 3) if only that site fails, escalate to the network team | Decide whether the answers are enough |
| Information complete | No questions: straight to the PIC | |
| Triage points to comsec / network / business team | Assign directly to that team's PIC | Handle it. If it needs escalating, it goes through the ops PIC |
| P1, review, project handover | Assign (ops by default) and flag "escalation candidate" to the OPS PIC, even when another team holds the ticket | The ops PIC checks first, then escalates to the Team Leader |
| needs_human, escalate, delete request, possible prompt injection | Assign to the ops PIC. Acknowledgement only (no questions), and tell the PIC no data may change without the Team Leader's approval | The ops PIC checks, then escalates to the Team Leader |
| Nothing specific to ask, but a confirmation is needed (T03 type) | Flag "confirm directly" | Ask the requester directly. No draft is generated |
| Documented workaround exists in the knowledge base | Draft a workaround message for the PIC. It is not sent | Review and send |
| No documented answer | No draft: saves LLM calls | Handle directly |
| AI fails (rate limit, invalid output, outage) | Normal manual queue, alert the ops lead | |

Rules behind the table:
1. **Assignment is direct, escalation is not.** The system assigns straight to the right team, but every escalation goes through the ops PIC. It never alerts the Team Leader or the project team on its own.
2. **Waiting for the requester never stops work.** The SLA clock starts at assignment and a real outage cannot wait for an email reply, so assignment and the questions go out together.
3. **Dangerous cases get no questions and no automatic follow-up.**
4. **Automation fails open to humans.** If the AI step breaks, the ticket still reaches the ops queue and someone is told.
5. **Drafts exist only when the system has documented knowledge.** Otherwise the PIC handles it directly.
6. Phase 1 sends the requester email automatically. The risk is a question about something the requester already gave (the model's missing-information precision measured 31 to 80%), so every email carries the ignore line and is recorded in the ticket. Review by sampling.

## 3. Requester email

One formal email per ticket from a fixed template (`ask_back.py`, `requester_email`). The model only chooses which items are missing, so the tone is consistent and the email can never promise a fix time. Local testing uses Mailpit (nothing leaves the machine).

## 3b. Template improvement loop

If the PIC keeps having to confirm the same thing, or the same item keeps being missing for a menu, the form should change. `template_insights.py` counts these per menu and, once a pattern reaches a threshold (default 3), proposes a change: add a required field, add an example, or add a template question. The ops team reviews and edits the form. Nothing changes automatically.

## 4. Earning more autonomy

Approval gates can be removed one at a time, only when measured results justify it on the labelled set:
- Phase 1 (now): automatic PIC assignment and requester email. Escalation, follow-ups with other teams and workaround messages stay with the PIC.
- Direct assignment already follows the triage's routing, whose agreement with the labelled set is only about 57 to 67%. Watch the reroute rate (tickets handed back to ops) and fall back to ops-first for any route that misroutes often.
Dangerous cases never move beyond flagging the PIC.

## 5. Open points

- Who is on duty as PIC and how the rotation works (the mock uses a placeholder).
- Ask-back reminder timing and what happens when the requester never answers.
- Whether the SLA clock pauses while waiting for the requester.
- Real mail delivery needs an SMTP account and real recipients, which is out of scope for the mock project.
