# Target design: AI-assisted application support desk

This is the design the mock project is growing toward. It borrows from ITIL practice and from what commercial triage tools advertise (vendor claims, not independent evidence). The synthesis is ours and is a hypothesis to test with the golden set.

## Principles
1. **Humans decide, the system recommends.** Priority, handover to a project team and any data change stay with the ops team and Team Leader.
2. **The SLA clock starts at assignment**, so the biggest win is sending a complete ticket to the right team the first time.
3. **Evidence over claims.** Every behaviour is scored against a labelled ticket set before it is trusted.
4. **Least power.** The AI can read and add notes. It cannot delete or edit business data.
5. **Ticket text is data, never instructions.**

## Flow
1. **Intake check.** Compare the ticket with the ticket template (steps, record, error, time, affected users). If something is missing, draft a question to the requester instead of assigning.
2. **Enrichment.** Look up the menu in the impact matrix, the requester's role in the access matrix, similar tickets (duplicates), known errors and workarounds, and recent changes in the change log.
3. **Recommendation.** Suggest type (bug, data, change impact, request), priority (impact x urgency, raised when several people report the same issue), the team to route to (ops, comsec, network, project team, business for change requests) and the resolution path (fix now, workaround, ask user, route, escalate).
4. **Human decision** by the PIC who received the ticket. Escalations go through the ops PIC to the Team Leader. The recommendation is posted as a clearly labelled draft note with its sources.
5. **Resolution within the SLA:** ask the user, fix now (for example a data correction), or give a workaround while a bug waits for a fix.
6. **Handover pack** for the project team when the Team Leader decides: summary, menu, reproduction steps, expected vs actual, evidence, analysis, suspected cause, proposed fix, related change, customer impact. A bug is a handover candidate only when it was reproduced, narrowed down and a fix was proposed.
7. **Learning loop.** Resolved tickets with a root cause become known-error entries. Outdated policy documents are flagged by owner and review date.

## Measures
- Routing accuracy and reroute rate (tickets sent to the wrong team).
- Missing-information detection (did we ask when we should, and only then).
- Priority agreement with the labelled set, reported per class.
- Resolution-path agreement.
- Safety: injection and dangerous-request cases must not change the outcome.
- Retrieval: right menu section ranked first (measured: MiniLM 14/26, Gemini embeddings 24/26 on the current set).

## Build order
1. Retrieval on the application knowledge base with a multilingual embedding model (decided by the retrieval evaluation).
2. New triage output schema (type, priority, route, resolution path, missing information, reasons) and an evaluation script against `data/golden/tickets.csv`.
3. Intake check and ask-back drafts.
4. Duplicate detection, known-error search, change-log correlation.
5. Handover pack.
6. Safety tests (injection, delete request, access issues).
7. Scheduled runs with n8n.

## Limits
Fictional data, 30 labelled tickets, labels agreed in conversation, not a full inter-annotator review. Results show feasibility, not production accuracy.
