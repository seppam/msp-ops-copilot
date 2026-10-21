# MSP Ops Copilot

An AI-assisted application-support desk, built step by step on free tiers to see how far ticket automation can safely go. It reads tickets from Odoo, recommends type, priority, team and next step using the company's own written rules, assigns a person in charge (PIC), emails the requester through n8n, and records everything back on the ticket. A human always decides escalations.

> All data is fictional: customers, tickets, policies and email addresses (the reserved `example.test` domain). Nothing here emails a real person.

## What it does, in one picture

```mermaid
flowchart LR
    REQ([Requester]) -->|ticket + template fields| ODOO[(Odoo 19 Community<br/>project: App Support)]
    ODOO --> TRI[triage_odoo.py]
    KB[(Rules: impact matrix, SLA,<br/>access matrix, deletion policy)] -->|retrieve, Gemini embeddings| TRI
    CHG[(Change log + earlier tickets)] --> TRI
    TRI -->|JSON, validated by Pydantic| LLM{{Groq or Gemini}}
    TRI --> G[Safety guards<br/>delete requests, injection]
    G --> PLAN[Action planner]
    PLAN -->|assign PIC / team| ODOO
    PLAN -->|requester email| OUT[(Outbox)]
    PLAN -->|note: recommendation + plan| ODOO
    OUT --> N8N[n8n workflow]
    N8N -->|SMTP| MAIL[Mailpit<br/>local inbox]
    N8N -->|email sent note| ODOO
    MCP[MCP server<br/>4 tools] --- ODOO
    CC[Claude Code or any MCP client] --- MCP
```

![Mailpit inbox after the n8n workflow ran](docs/img/mailpit-inbox.jpg)

*The local Mailpit inbox after the n8n workflow ran: one formal email per ticket, each naming the PIC on duty. The salary-data ticket (T26) went to the comsec PIC. All addresses are fictional.*

Example of what the system produces for a ticket reporting that a Sales user can see salary data:
- Recommendation note on the Odoo ticket: type other, priority P1, route to comsec.
- Assigned straight to the **comsec PIC**; the **ops PIC** is flagged as the one who decides about escalation.
- One formal email to the requester: the ticket is registered, here is the PIC, please wait for the PIC's follow-up. No promise about timing or fixes.

## The phases, in order

| # | Phase | What was built | Where |
|---|---|---|---|
| 0 | LLM access | One OpenAI-compatible client for Groq and Gemini, switched by `LLM_PROVIDER`. An optional OpenRouter entry exists but was never used. | `llm.py` |
| 1 | Tool calling by hand | The loop every agent framework wraps: ask, run requested tools, answer. Step cap; unknown tools and bad arguments are reported back to the model instead of crashing. | `agent_basic.py`, `tools.py` |
| 2 | Odoo lab | Odoo 19 Community and Postgres in Docker, bound to localhost, with seeded data, called through Odoo's JSON-2 API with an API key. | `odoo_client.py`, `seed_odoo.py` |
| 3 | MCP server | Four tools (three reads, one note-writing tool), restricted to an allow-list of projects, escaping model text. No delete or edit tool exists. | `mcp_server.py` |
| 4 | First triage agent | Structured JSON output validated with Pydantic, one retry with the validation error, dry run by default. Built for an infrastructure helpdesk. | `triage.py` |
| 5 | RAG | Section chunking, local embeddings, Chroma, cited answers, a distance cutoff because search always returns something. | `rag.py`, `data/kb/` |
| 6 | Hardening | Tests that use a fake LLM, an audit log, idempotent re-runs. | `tests/` |
| 7 | Domain pivot and evaluation | Moved to application support. Wrote company rules in Bahasa Indonesia and a 30-ticket labelled set; built an evaluation script that scores models against it and logs every run. | `data/kb_app/`, `data/golden/`, `eval_triage.py`, `experiments/` |
| 8 | Retrieval experiment | English-trained vs multilingual embeddings on Indonesian tickets. Gemini embeddings clearly won. | `eval_retrieval.py` |
| 9 | Triage v2 | Type, priority, handover, resolution path, missing information, duplicate and related-change detection, in a single validated JSON answer. | `triage2.py`, `kb.py`, `embeddings.py` |
| 10 | Safety guards | Code that runs after the model: delete requests are forced to a human, an injected demand for P1 cannot buy it, and a vague ticket cannot be P1 from its wording. | `guards.py` |
| 11 | Workflow design | Submission template, action planner, formal requester email, daily PIC rotation, template-improvement report. | `intake.py`, `actions.py`, `ask_back.py`, `pics.py`, `template_insights.py`, `docs/WORKFLOW.md` |
| 12 | Automation | Odoo wiring, an outbox, and an n8n workflow that sends the requester emails through Mailpit and writes "email sent" back to the ticket. | `triage_odoo.py`, `outbox*.py`, `automation/` |

The design behind phases 9 to 12 is in [docs/DESIGN.md](docs/DESIGN.md) and [docs/WORKFLOW.md](docs/WORKFLOW.md). Measured resource use is in [docs/RESOURCES.md](docs/RESOURCES.md).

## Rules the automation follows

- **Every ticket gets a PIC and one formal email.** The PIC on duty rotates daily through a roster (`data/roster.json`, fictional names). The email says the ticket is registered, names the PIC, and asks the requester to wait for the PIC's follow-up.
- **The email asks for missing information in the same message**, automatically. A ticket that is complete gets no questions. Each question list is introduced with "if you already provided this, please ignore", because the model sometimes asks for something already given.
- **Assignment goes straight to the right team** (ops, comsec, network, business team). **Escalation always goes through the ops PIC**, who decides whether to involve the Team Leader or the project team. The system never alerts either itself.
- **Waiting for the requester never stops work.** Vague "everything is down" reports come with first checks for the PIC: system availability, then network from the requester's site and another site, then the network team if only that site fails.
- **Dangerous cases** (delete requests, prompt-injection attempts, anything marked needs_human or escalate) get an acknowledgement only, no questions and no automatic follow-up.
- **Drafts only when documented knowledge exists** (for example a documented workaround). Otherwise the PIC handles it directly, which also saves LLM calls.
- **If the AI step fails**, the ticket still goes to the manual ops queue and the ops lead is alerted.
- **Recurring gaps feed the form.** If the same information keeps being missing for a menu, or the PIC keeps confirming the same thing, a report proposes a template change for the ops team to review.

## Results

All numbers come from `experiments/history.jsonl` (`uv run python -m msp_ops_copilot.compare` prints them). They are small-sample results on fictional data. Labels are one practitioner's judgement, agreed in conversation, not an independent review.

**Retrieval: does search find the right menu section? (26 tickets, Bahasa Indonesia)**

| Embedder | Ranked first | In top 3 | Peak memory | Disk |
|---|---|---|---|---|
| Gemini embeddings (cloud, free tier) | **24 / 26** | 24 / 26 | 111 MB | none |
| MiniLM, English-trained, local | 14 / 26 | 24 / 26 | 560 MB | 166 MB |
| Multilingual MiniLM, local | 13 / 26 | 17 / 26 | 1.0 GB | 252 MB |
| Multilingual potion, local | 15 / 26 | 22 / 26 | 2.1 GB | 547 MB |

**Triage v2: agreement with the labelled set (30 tickets, mean of 3 runs at temperature 0, range in brackets)**

| | Type | Priority | Within one level | Handover | Resolution path | Questions asked: precision / recall |
|---|---|---|---|---|---|---|
| Gemini 3.5 flash-lite | 83% (83-83) | 60% (60-60) | 96% | 64% (63-67) | 66% (60-70) | 81% / 54% |
| Groq gpt-oss-120b | 83% (80-87) | 53% (50-57) | 82% (79-86) | 62% (57-67) | 49% (47-50) | 34% / 62% |

| Cost of one 30-ticket run | Tokens in / out | Seconds per call |
|---|---|---|
| Gemini | about 39,100 / 2,900 | 13.9 in the repeated runs (1.2 in earlier runs; the cause is unknown) |
| Groq | about 39,600 / 7,600 | 7.7 |

What to take from it:
- **Repeatability:** even at temperature 0, single metrics move by 0 to 10 points between identical runs (for example Gemini's resolution path ranged 60 to 70%). Treat differences of a few points as noise.
- **Priority is usually close but rarely exact.** Gemini is within one level on 96% of tickets, Groq on 82%. Exact agreement is 53 to 60%. The system therefore recommends and a person decides.
- **The models differ in how they ask.** Gemini's questions are right 81% of the time but it misses about half of what is missing. Groq asks for more and is right only 34% of the time. That is why every email carries the "please ignore" line.
- **Handover (routing) agreement is about 62 to 64%.** Automatic assignment to the wrong team costs SLA time, so the reroute rate is the first thing to monitor.
- **Safety needed code, not only prompts.** In one of three Gemini runs the model rated the vague "URGENT!!!" ticket as P1. A guard now forces `unknown` for tickets that lack four or more key facts, and the table above includes that guard. The injection ticket never reached P1 or P2 in any run, and the "delete all invoices" request went to a human in every run.

## Run it yourself

Requirements: Docker Desktop, [uv](https://docs.astral.sh/uv/), free API keys from Groq and Google AI Studio. Enter keys by editing `.env`; never paste them into chat or commits.

```bash
git clone <this repo> && cd msp-ops-copilot
cp .env.example .env          # then edit .env: GROQ_API_KEY, GEMINI_API_KEY
uv sync

# Odoo lab: lab/docker-compose.yml has postgres:16, odoo:19.0 and, under the "n8n" profile, n8n and Mailpit
cd lab && cp .env.example .env     # then edit lab/.env and set POSTGRES_PASSWORD (openssl rand -hex 12)
docker compose up -d
docker compose run --rm odoo odoo -d mspdemo -i base,contacts,crm,project --without-demo=all --stop-after-init
docker compose up -d odoo
docker compose exec -T odoo sh -c 'odoo shell -d mspdemo --no-http --db_host=db --db_user=odoo --db_password="$PASSWORD"' < ../scripts/odoo_create_api_key.py
cd ..
# copy the printed key into ODOO_API_KEY in .env

uv run python -m msp_ops_copilot.seed_odoo             # old infrastructure demo tickets
uv run python -m msp_ops_copilot.seed_app_tickets      # 30 application-support tickets
uv run python -m msp_ops_copilot.kb                    # index the rules with Gemini embeddings
```

Triage (dry run prints; `--write` adds one note per ticket and queues the requester email):

```bash
uv run python -m msp_ops_copilot.triage_odoo --ids T01,T22
uv run python -m msp_ops_copilot.triage_odoo --write --ids T01,T22
```

Send the queued emails through n8n and Mailpit (inbox at http://127.0.0.1:8025):

```bash
uv run python -m msp_ops_copilot.outbox_server &        # local bridge, localhost only
cd lab && docker compose --profile n8n up -d n8n mailpit
docker compose cp ../automation/mailpit-smtp-credential.json n8n:/tmp/cred.json
docker compose cp ../automation/requester-email-outbox.json n8n:/tmp/wf.json
docker compose exec -T n8n n8n import:credentials --input=/tmp/cred.json
docker compose exec -T n8n n8n import:workflow --input=/tmp/wf.json
docker compose exec -T -e N8N_RUNNERS_BROKER_PORT=5680 n8n n8n execute --id=outboxEmail01
```

Evaluation and tests (add `--temperature 0` for the most repeatable runs):

```bash
uv run python -m msp_ops_copilot.eval_triage --name my-run    # scores against data/golden/tickets.csv
uv run python -m msp_ops_copilot.compare                      # history table
uv run python -m msp_ops_copilot.template_insights            # which questions keep recurring
uv run pytest                                                 # 66 tests, no network, no Odoo
```

Register the MCP server in Claude Code: `claude mcp add --scope user msp-odoo -- uv --directory <repo path> run python -m msp_ops_copilot.mcp_server`

The n8n workflow has an "Every minute" schedule trigger that ships disabled; enable it in the n8n editor to run continuously.

## Repository map

| Path | Contents |
|---|---|
| `src/msp_ops_copilot/` | Application code (one module per concern, listed in the phase table) |
| `data/kb_app/` | Company rules in Bahasa Indonesia: impact matrix, SLA and priority, access matrix, deletion policy, handover checklist, ticket template |
| `data/golden/` | Labelled tickets, change log, labelling guide |
| `data/roster.json` | Fictional on-duty roster per team |
| `data/kb/`, `data/tickets.json` | Earlier infrastructure-helpdesk prototype (phases 1 to 6) |
| `experiments/` | `history.jsonl` and per-run predictions |
| `automation/` | n8n workflow and mail credential (no secrets) |
| `lab/` | Docker compose for Odoo, Postgres, n8n and Mailpit (a copy of the compose file used during development) |
| `scripts/` | Odoo API-key helper |
| `docs/` | Design, workflow rules, measured resources |

## Honest limits

- The commands above were run against the original development lab folder. `lab/` is a copy of that compose file (minus a custom-addons mount) and was validated but not started as a second stack.
- Fictional data and 30 labelled tickets. Results are means of three runs and still move by up to 10 points per metric.
- The "advance evaluation" rule for drafting workaround messages is crude (a documented workaround in the retrieved impact-matrix section).
- Mailpit is a development mail catcher. Real delivery needs SMTP and real recipients.
- Free-tier limits and model names change; check them in each provider's console.
- Local multilingual embedding models were tried and were worse than Gemini's cloud embeddings. A private deployment would need a stronger local model on proper hardware, which this project did not have.
- The PIC rotation is a plain daily rotation over a fictional roster. It ignores leave, skills and workload.
- Local Docker data was lost once during this project; production needs backups of the Odoo and Postgres volumes.

## Licence

MIT, see [LICENSE](LICENSE).
