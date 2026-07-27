# Review Analyser — AI-Powered Discovery Engine

**NextLeap Grad Project** · Product Management
**Subject company:** Blinkit (Indian quick commerce)
**Phase:** Part 1 — Discovery Engine (design complete, build starting)

---

## The problem

Blinkit users have made the platform a weekly routine, but that routine is **narrow**. A large
share of Monthly Active Customers buy repeatedly from the same two or three categories and rarely
try a category new to them — despite Blinkit stocking it, delivering it at the same speed, at
competitive prices.

The result is a widening gap between **catalogue breadth** (what the platform stocks) and **basket
breadth** (what a user actually buys).

We can see *that* exploration is low. We do not know *why*. Awareness gaps, trust gaps, price
gaps, information gaps, friction, habit calcification, and loyalty to another retailer each imply
a completely different solution — and building against the wrong one wastes a quarter.

**This repository builds the system that answers *why*, at scale, from what real users actually
say.**

---

## What this is

An AI-powered discovery engine that:

1. **Collects** public user feedback from multiple sources — Play Store, App Store, Reddit,
   forums, social, product reviews — for Blinkit *and its competitors*
2. **Normalises** it into a single provenance-tagged corpus
3. **Labels** it with consistent, auditable structured coding via LLMs
4. **Induces themes bottom-up** from the data rather than confirming a pre-written hypothesis list
5. **Synthesises insights** with claim, mechanism, affected segment, and implication
6. **Proves the result is trustworthy** through a measured validation harness

Point 6 is the part that matters. An LLM will happily produce fluent, confident, wrong output —
so every insight is traceable to a specific verbatim, every quote is mechanically verified to
exist, and the validation numbers are reported including the bad ones.

---

## Pipeline

```
 [1] CONNECTORS ──▶ [2] NORMALISE ──▶ [3] CLEAN ──▶ [4] CORPUS STORE
                                                          │  (immutable)
                                                          ▼
        [5a] RELEVANCE GATE (Groq)  ──▶  [5b] LABELLING (Gemini)
                                                          │
                                                          ▼
                              [6] CLUSTER ──▶ [7] SYNTHESISE
                                                          │
                                                          ▼
                                                  [8] VALIDATION HARNESS
                                          reads back ─────┘
                                          against [4]
```

Stages 1–4 are the pipeline proper. Stages 5–8 consume it and are only as good as it is.

---

## Documentation

| Document | Contents |
|---|---|
| **[PROBLEM_STATEMENT.md](PROBLEM_STATEMENT.md)** | The framing — company rationale, problem, metric definition (Category Exploration Rate), scope, validation bar, stated assumptions. Source of truth for **why**. |
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | The build spec — data contracts, all 8 stages, provider strategy, validation harness, repo layout, cost model. Source of truth for **how**. |
| **[edge.md](edge.md)** | 143 edge cases by stage, severity-rated, with the 36 silent-corruption defences as a build checklist and the required test fixtures. |
| **[context.md](context.md)** | Condensed project context — the fast way in. |

New here? Read `context.md`, then `ARCHITECTURE.md` §4 (data contracts) and §19 (traceability
walkthrough).

---

## Stack

| Layer | Choice |
|---|---|
| Language | Python 3.12 |
| LLM — fast tier | **Groq** — full-corpus relevance gate |
| LLM — reasoning tier | **Google Gemini** — structured labelling, codebook induction, synthesis |
| Schemas | Pydantic v2 |
| Storage | Parquet + DuckDB (local-first, no server) |
| Collection | `google-play-scraper`, `praw`, `httpx`, `selectolax` |

Two providers is a deliberate design choice, not redundancy: it enables a **cross-provider
agreement check** that a single-provider setup cannot offer. A finding that survives two unrelated
model families is meaningfully more robust than one that survives running the same model twice.

---

## Operating rules

These are enforced in the design, not just stated:

1. **No invented numbers.** Unverified figures are marked `[TO VERIFY]`.
2. **No fabricated quotes, ever.** Every cited verbatim is mechanically verified against the
   corpus. Any failure fails the run.
3. **Insights carry their uncertainty** — confidence, evidence volume, source count, and the
   *direction* of known bias.
4. **Report the bad results too.** A validation report with no weaknesses is not believable.
5. **Themes come from the data**, not from a pre-written list.
6. **No PII.** Stripped before storage *and* before any transmission to a model provider.
7. **The collection pipeline is the backbone.** Every step extends it, hardens it, or consumes its
   provenance-tagged output.

---

## Status

| Milestone | State |
|---|---|
| Framing, metric definition, scope | ✅ Complete |
| Architecture and data contracts | ✅ Complete |
| Edge case analysis | ✅ Complete |
| M0 — provider spike | ⬜ Next |
| M1 — collection spike | ⬜ |
| M2 — pipeline proper (stages 1–4) | ⬜ |
| M3 — gate + codebook induction | ⬜ |
| M4 — labelling at scale | ⬜ |
| M5 — themes and insights | ⬜ |
| M6 — validation harness | ⬜ |
| M7 — reports | ⬜ |

---

## A note on scope

Part 1 produces **understanding, not features**. Solution design, roadmaps, prioritisation, and
experiment plans are explicitly out of scope — bringing solutions forward before the evidence is
complete is the specific failure mode this project is structured to avoid.

This is a **public-data project**. It uses no internal or proprietary data, and every behavioural
claim it produces is an inference from public discourse, labelled as such.
