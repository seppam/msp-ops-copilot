# Resources used (measured on the development machine)

Reference for sizing a production version. Everything marked **measured** was observed on this project; **reported** means taken from a third-party source and not verified; **derived** is arithmetic on measured values. These are idle or small-batch figures, not load tests.

## Machine
MacBook, Apple Silicon, 16 GB RAM, 8 cores, shared with Chrome, Edge, Claude and Docker. During measurement: 38-41% memory free, swap about 2.6 of 3 GB used (measured). One Chrome tab process used about 3.3 GB, more than the whole Docker stack. Docker Desktop VM limit 4 GB.

## Containers (measured, idle, after startup)
| Service | Memory | Cap set | Image on disk |
|---|---|---|---|
| Odoo 19 Community | 119 MiB | 2 GiB | 3.31 GB |
| PostgreSQL 16 | 113 MiB | none | 0.66 GB |
| n8n (optional) | 358 MiB at first test, 502 MiB in the later test | 768 MiB | 1.79 GB |
| Mailpit (optional, dev mail catcher) | 14 MiB | 128 MiB | 0.06 GB |

Total with everything running: about 750 MiB of container memory; images 5.8 GB; volumes 120 MB. Odoo memory grows with use and is capped. n8n was measured twice with different results, so budget at its cap.

## Project files
| Item | Size |
|---|---|
| Python environment (106 packages) | 400 MB |
| Vector store (Chroma) | 7.7 MB |
| Embeddings cache | 4.6 MB |
| Default local embedding model (MiniLM, cached by Chroma) | 166 MB |
| Local multilingual models tried and not used | 762 MB (safe to delete: `~/.cache/fastembed`) |

## LLM usage (measured, from experiments/history.jsonl)
| Provider and model | Input tokens per ticket | Output tokens per ticket | Seconds per ticket | Rate-limit retries |
|---|---|---|---|---|
| Groq openai/gpt-oss-120b | about 1,320 | about 242 | about 8 | none |
| Gemini 3.5 flash-lite | about 1,263 | about 99 | about 2.7 | 3 per 30-ticket run |

Prompt size is dominated by retrieved policy text, the change log and the fixed instructions. Output varies mainly because the Groq model spends hidden reasoning tokens. Embeddings: one batched call indexes the 38 policy sections; each ticket needs one embedding call (cached on disk).

Derived: 1,000 tickets a day is roughly 1.3 million input tokens a day, more than the free tiers allow (reported limits for Groq's free plan: about 8,000 tokens per minute and 200,000 per day, so about 150 tickets a day, not verified here). A production service needs a paid plan or a self-hosted model. No prices were recorded because only free tiers were used.

## Retrieval options (measured on 26 labelled tickets)
| Embedder | Right menu ranked first | Time | Peak memory | Disk |
|---|---|---|---|---|
| Gemini embeddings (cloud) | 24/26 | 2.8 s | 111 MB | none |
| MiniLM (English-trained, local) | 14/26 | 1.3 s | 560 MB | 166 MB |
| Multilingual MiniLM (local) | 13/26 | 1.8 s | 1.0 GB | 252 MB |
| Multilingual potion (local) | 15/26 | 2.0 s | 2.1 GB | 547 MB |

## Before going to production, measure
Concurrent tickets and p95 latency; Odoo under real user load and worker count; n8n queue behaviour; provider failover when rate-limited; cost per ticket at the chosen provider; a local multilingual model large enough to match cloud quality, on a server, if data cannot leave the company; real SMTP delivery; backups of the Odoo and Postgres volumes (a Docker storage reset destroyed all data once during this project).
