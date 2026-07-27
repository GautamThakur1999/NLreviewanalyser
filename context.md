# Project Context

> Condensed, load-bearing context for this project. Read this first in any new session.
> Full framing document: [PROBLEM_STATEMENT.md](PROBLEM_STATEMENT.md) — this file is the
> distilled reference; the problem statement is the source of truth for reasoning and rationale.
>
> Last updated: 27 July 2026

---

## 1. Identity

| Field | Value |
|---|---|
| **Project** | NextLeap Grad Project — Review Analyser |
| **Company selected** | **Blinkit** (Indian quick commerce, part of Eternal Ltd., formerly Zomato Ltd.) |
| **Role being played** | Product Manager, Growth Team |
| **Current phase** | **Part 1 — build the AI-Powered Discovery Engine** |
| **Working directory** | `C:\Users\thaku\Downloads\Nextleap Grad Project - Review Analyser` |
| **Environment** | Windows 11, Python 3.12.4 (Anaconda), network access confirmed working |

---

## 2. The strategic goal (verbatim from the brief)

> **Increase the percentage of Monthly Active Customers who purchase products from at least
> one new category every month.**

Illustrative transitions named in the brief:
- Groceries → pet supplies
- Snacks & beverages → personal care
- Household essentials → baby products

---

## 3. The problem in one paragraph

Blinkit users have made the platform a weekly routine, but that routine is **narrow**. A large
share of Monthly Active Customers buy repeatedly from the same 2–3 categories and rarely try a
category new to them — despite Blinkit stocking it, delivering it at the same speed, at
competitive prices. The result is a widening gap between **catalogue breadth** (what Blinkit
stocks) and **basket breadth** (what a user actually buys). **We can see *that* exploration is
low; we do not know *why*.** Awareness gaps, trust gaps, price gaps, information gaps, friction
gaps, habit calcification, and loyalty to another retailer each imply a completely different
solution. Building against the wrong one wastes a quarter.

---

## 4. Why Blinkit (rationale, compressed)

- **Habit-formed base** — ~10-min delivery has moved it from occasion to routine. Repeat behaviour is established; the problem is *narrow* repeat behaviour.
- **Catalogue breadth ≫ basket breadth** — aggressive expansion into personal care, baby, pet, home & kitchen, electronics, health & wellness has outpaced the average user's basket.
- **Dark-store economics** — margin depends on AOV and basket size, not just frequency. One more category on an *already-paid-for* delivery trip is the cheapest incremental revenue available. Exploration is a **margin lever**, not only an engagement lever.
- **Speed is no longer a differentiator** — parity with Zepto, Swiggy Instamart, BigBasket/BB Now, Flipkart Minutes, Amazon's q-commerce push. Discovery and share-of-basket are the emerging battleground.
- **Rich public discourse** — enough continuous public feedback volume to build a real listening system, not a toy demo.

---

## 5. The core tension (central design constraint)

> **The product is engineered to help users finish faster, and exploration requires users to
> slow down.**

The user's real loop is **retrieval, not browsing**: open app → search or "Order again" → add
known SKUs → checkout, often under 90 seconds. Every efficiency feature ever shipped (reorder
lists, saved carts, search-first navigation, previously-bought rails) optimises completion of a
*known* need and therefore actively suppresses exploration. Any Part 2 solution must **resolve**
this tension, not ignore it.

Habit formation sequence: urgent high-intent first order → experience works, trust established →
mental model forms (*"Blinkit is for [my 2–3 categories]"*) → sessions become retrieval → model
calcifies → other categories become invisible even one tap away.

---

## 6. The metric — Category Exploration Rate (CER)

**CER (month M)** = (MACs in month M who purchased ≥1 product from a category *new to that
customer*) ÷ (Total MACs in month M) × 100

### Definitions

| Term | Working definition | Open decision |
|---|---|---|
| **MAC** | Placed ≥1 delivered order in the calendar month | Exclude fully-refunded orders? (proposed: yes) |
| **Category** | **L1 taxonomy node** (Grocery & Staples, Snacks & Beverages, Household Essentials, Personal Care, Baby Care, Pet Supplies, Home & Kitchen, Electronics & Accessories, Health & Wellness) | L1 vs L2 — L2 inflates CER and rewards trivial adjacency (shampoo → conditioner). **Recommendation: L1 primary, L2 as secondary diagnostic** |
| **New category** | Not purchased from in the **trailing 6 months** before month M | 3mo too loose (captures seasonal return as exploration); lifetime too strict |
| **Purchase** | Delivered, non-returned line item | Free samples / 100%-discounted items flagged and reported separately — trial, but not commercial validation |

### Why CER and not alternatives
- **Not "categories per user"** — an average hides the distribution; power users mask a median of 2.
- **Not "new category orders"** — order-level metrics reward splitting baskets, which hurts margin. We want the *same trip* to carry more categories.
- CER is a per-user, per-month binary: simple to explain, hard to game, matches the goal's wording.

### Guardrails (a CER win that breaks any of these is not a win)
1. Time-to-checkout for repeat-intent sessions
2. Return/refund rate in newly explored categories
3. Repeat rate on the new category at M+1, M+2 (one-off discount-driven trial = vanity)
4. AOV and contribution margin per order
5. App rating and complaint volume
6. Order frequency / retention

### Required segment cuts
Tenure (<1mo / 1–6mo / 6+mo) · Frequency (light/medium/heavy) · Current breadth (1–2 / 3–4 / 5+
categories) · Household context (baby signals, pet signals, single vs family) · City tier & metro

---

## 7. Part 1 — the AI-Powered Discovery Engine

### Objective
A **working, repeatable** AI system that ingests unstructured public user feedback at scale and
converts it into structured, validated, decision-grade insight about category exploration.

**Part 1 does not move the metric. It earns the right to try.** Output is understanding, not features.

### 7.0 The collection pipeline is the backbone — not a preliminary step

> **Standing directive.** The data pipeline that collects reviews and feedback from *all* viable
> sources is the foundation of Part 1, not a setup task before the "real" work. Every subsequent
> step must be built on it and must be traceable back through it.

Why this is non-negotiable:

- **Insight quality is capped by corpus quality.** No amount of LLM sophistication downstream
  recovers signal that was never collected. A weak corpus produces confident, wrong insight.
- **Single-source collection systematically distorts the answer.** Play Store reviews skew to
  complaints about delivery and app bugs; Reddit carries the long-form *reasoning* about trust,
  price comparison, and loyalty to other retailers. Collect only the former and we will conclude
  the barrier is friction, when it may be trust. **The barrier type we identify is a direct
  function of which sources we reached.**
- **Competitor data is what makes a finding attributable.** A barrier in Blinkit *and* Zepto/
  Instamart feedback is a category-level problem; one only in Blinkit feedback is ours. Without
  competitor collection, every finding is ambiguous.
- **Traceability runs backwards through the pipeline.** The 100%-quote-verifiability bar (§8) is
  only enforceable if every verbatim retains its source, ID, timestamp, and provenance from
  ingestion onward. Provenance must be captured at collection time — it cannot be added later.
- **Re-runnability lives here.** "Repeatable system, not one-off analysis" is a property of the
  collection layer first.

**What this means for every upcoming step:** each new prompt or task in this project must connect
to this pipeline — either extending collection coverage, hardening normalisation/dedup/provenance,
or consuming its normalised output. Any analysis step that bypasses it, or any insight that cannot
be walked back to a collected, provenance-tagged verbatim, does not count.

**Pipeline stages (the spine of Part 1):**

```
[1] SOURCE CONNECTORS   → per-source collectors (Play, App Store, Reddit, forums, social, product reviews)
[2] NORMALISATION       → one schema: text, source, source_id, url, timestamp, rating, lang, app/brand, meta
[3] CLEANING            → dedup (exact + near), spam/bot filtering, language ID (EN/HI/Hinglish/Indic), PII strip
[4] CORPUS STORE        → immutable, provenance-tagged, re-readable; the single source all analysis reads from
[5] LABELLING           → structured per-verbatim coding against the codebook
[6] THEME CLUSTERING    → bottom-up themes with evidence sets
[7] INSIGHT SYNTHESIS   → claim + mechanism + segment + implication + confidence
[8] VALIDATION HARNESS  → reads back against [4] to enforce the §8 bar
```

Stages [1]–[4] are the pipeline proper. [5]–[8] consume it and are only as good as it is.

### "At scale" means (a human reading 100 reviews does NOT satisfy this)
- Multi-source ingestion into one normalised schema
- Consistent, auditable labelling across the entire corpus
- Themes emerging **bottom-up** from data, not confirming a pre-written hypothesis list
- Every insight traceable to specific verbatims
- Measurably reliable, not just plausible-sounding
- **Re-runnable**, not a one-off

### Data sources (all required)
| Source | Good for | Note |
|---|---|---|
| Google Play reviews (Blinkit + competitors) | Volume, star ratings, timestamps, version tags | Sample across all rating bands, not just 1-star |
| Apple App Store reviews | Different demographic (iOS) — segment contrast | Lower volume; public RSS review feed per storefront |
| Reddit (r/india, city subs, r/personalfinanceindia) | **Longest-form, most candid — best source for *why*** | Read comment trees, not just top posts |
| Community forums / complaint sites | Trust and quality-perception failures | Heavily negative-skewed; weight accordingly |
| Social media (X, Instagram, YouTube comments) | Real-time reaction to category launches | Noisy; aggressive spam/bot filtering needed |
| Product reviews (on- and off-platform) | **Most direct evidence on "what info is needed before trying"** | Category-specific quality/trust signal |
| General q-commerce discussion | Category narrative shaping expectations | Context, not primary evidence |

> **Competitor coverage is mandatory, not optional.** A barrier present in Blinkit *and* Zepto/
> Instamart feedback = category-level problem. Present only in Blinkit = our problem. Different
> solutions. Only visible if both are collected.

### The 8 research questions the engine must answer
1. Why do users repeatedly buy from the same categories? (habit / speed-optimisation / trust concentration / deliberate loyalty elsewhere?)
2. What prevents exploration? — **rank the barriers**, distinguishing awareness vs trust vs price vs information vs friction gaps
3. How do users discover products today? (search / home rails / reorder / external rec / offline / word of mouth) — and where does discovery demonstrably *not* happen
4. What role do habits play? How fast does the repertoire calcify post-onboarding? Is there an open window, and does it close?
5. What information do users need before trying a new category? (freshness/expiry, brand authenticity, return policy, sizing, ingredients, social proof, price comparison)
6. What frustrations emerge repeatedly — including ones that suppress the *trust* required to risk something new?
7. Which segments are more likely to experiment? (determines where to pilot)
8. What unmet needs emerge consistently — and which are latent category-exploration demand?

### The 4 things the brief requires demonstrating
1. **How the workflow gathers and analyses data** — connectors, normalisation schema, dedup, language handling (English/Hindi/Hinglish/Indic + romanised), spam filtering, LLM analysis stage. Documented architecture, running code.
2. **How themes are identified** — verbatim → structured label → clustered theme. Bottom-up. Documented codebook incl. how it evolved.
3. **How insights are generated** — theme with N mentions → insight with claim + mechanism + affected segment + implication. **Frequency alone is not an insight.**
4. **How insight quality was validated** — measured, not asserted. See §8.

---

## 8. Validation bar (the differentiating section)

An LLM will happily produce fluent, confident, wrong output. Credibility rests on proving it didn't.

| Dimension | Method | Bar |
|---|---|---|
| **Labelling reliability** | Human-labelled random gold set vs model labels; report agreement + Cohen's κ | Substantial agreement; disagreements inspected and explained, not hidden |
| **Groundedness / anti-hallucination** | Every cited quote automatically string-checked as literally present in source corpus | **100% traceable. Any fabricated quote = hard failure** |
| **Stability** | Re-run with different sample order / temperature; compare theme sets | Major themes reproducible; single-run themes = noise |
| **Saturation** | Plot new-theme discovery vs corpus size | Curve must flatten. If not, corpus is too small |
| **Coverage** | % of corpus mapping to ≥1 theme | High; large unassigned residue = incomplete codebook |
| **Source triangulation** | Does each major theme appear in >1 independent source? | Single-source themes flagged lower-confidence and reported as such |
| **Bias awareness** | Characterise corpus skew (reviews over-represent extremes; Reddit skews metro/male/tech-literate) | Documented per insight, **with direction of bias stated** |

**Every insight must carry:** confidence level · evidence volume · sources triangulated across · known bias.

---

## 9. Part 1 deliverables

1. Working discovery engine — runnable code, documented architecture, reproducible end-to-end
2. Documented corpus — sources, method, volume, time range, language mix, honest limitations
3. Theme codebook — barriers / drivers / discovery paths / unmet needs, with definitions + verbatims
4. Validation report — the §8 numbers, **including where it performed poorly**
5. Insight report — the 8 questions answered with evidence, segment, confidence, implication
6. Segment view — who explores, who doesn't, what differentiates them

### Definition of done
- [ ] Pipeline runs end-to-end on a real multi-source corpus; re-runnable on new data
- [ ] All 8 research questions answered with cited evidence
- [ ] Every §8 validation dimension has a reported number, including bad ones
- [ ] Every insight traceable to verbatims; every quote verifiable
- [ ] Barriers ranked **and classified by type** (awareness / trust / price / information / friction / habit / external loyalty)
- [ ] Explorer vs non-explorer segments identified and characterised
- [ ] Limitations and biases stated plainly, not buried

---

## 10. Out of scope for Part 1

Solution design · wireframes · feature concepts · prioritisation frameworks · roadmaps · effort
estimates · experiment/A-B design · financial modelling or business-case sizing · any internal
Blinkit proprietary data (we have none — this is a **public-data project**) · any PII

> Bringing solutions forward before the evidence is complete is the specific failure mode this
> project is structured to avoid.

---

## 11. Standing rules for this project

1. **No invented numbers.** Market size, GOV, MTU, share figures are marked `[TO VERIFY]` unless
   sourced from Eternal Ltd. filings/shareholder letters or credible published research.
   Fabricated stats are the fastest way to lose credibility in review.
2. **No fabricated quotes, ever.** Every verbatim cited must exist in the collected corpus and be
   automatically verifiable.
3. **Insights carry their uncertainty.** Confidence, evidence volume, source count, bias direction.
4. **Report the bad results too.** A validation report with no weaknesses is not believable.
5. **Themes come from the data.** No pre-written hypothesis list dressed up as findings.
6. **No personal identifying details in any deliverable.** No author name, email, or personal
   details anywhere in submitted files, documents, code comments, metadata, or presentation
   material. Documents are attributed by **role only** ("Product Manager, Growth Team"). This
   applies to every artifact produced for this project without exception.
7. **The collection pipeline is the backbone** (§7.0). Every step either extends it, hardens it,
   or consumes its normalised, provenance-tagged output. Nothing bypasses it.

---

## 12. Assumptions (stated so they can be challenged)

1. **Public feedback is a usable proxy for motivation** — skewed to extremes and to vocal, metro,
   digitally-fluent users. Assumed directionally informative about *mechanisms*, not representative
   in *proportion*. The §8 bias requirement keeps this honest.
2. **Low exploration is demand-side, not purely supply-side** — if Part 1 finds Blinkit genuinely
   lacks depth/quality in those categories, that's a **merchandising finding** and must be reported
   as such, not forced into a growth-lever conclusion.
3. **L1 taxonomy is the right grain** — to be validated.
4. **Exploration benefits the user, not just the business** — *if* Part 1 finds users deliberately
   and rationally split categories across retailers, **"increase exploration" may be the wrong goal,
   and we should say so.**
5. **No internal Blinkit analytics access** — all quantitative behavioural claims are inferred from
   public discourse and must be labelled as such. §6 metric definitions are specified so they *could*
   be implemented internally, but will not be measured by us.

---

## 13. Open questions before Part 2

| # | Question | Decides |
|---|---|---|
| 1 | L1 or L2 taxonomy for CER? | Whether the metric rewards genuine exploration or adjacency |
| 2 | 3-month, 6-month, or lifetime lookback? | Sensitivity and honesty of the metric |
| 3 | Do discounted/free trial purchases count? | Whether the metric can be bought with margin |
| 4 | Acceptable trade-off between exploration and time-to-checkout? | The design constraint for every Part 2 solution |
| 5 | Which categories are we actually ready to drive demand into (supply, quality, ops)? | Prevents driving trial into categories that disappoint and destroy trust |

---

## 14. Glossary

| Term | Meaning |
|---|---|
| **Quick commerce (q-commerce)** | Retail delivering small baskets in ~10–30 min from hyperlocal dark stores |
| **Dark store** | Micro-warehouse serving online orders only; no walk-in |
| **MAC** | Monthly Active Customer (§6) |
| **CER** | Category Exploration Rate — the primary metric (§6) |
| **AOV** | Average Order Value |
| **Basket breadth** | Distinct categories in a customer's purchases over a period |
| **Catalogue breadth** | Distinct categories the platform stocks |
| **Repertoire** | The stable set of categories a customer habitually buys from |
| **L1 / L2 category** | Taxonomy levels — L1 broadest ("Personal Care"), L2 sub-level ("Hair Care") |
| **Verbatim** | A single unedited piece of user-authored text (review, post, comment) |
| **Saturation** | Point at which more data stops producing new themes |
| **Groundedness** | Property that every generated claim traces to real source text |

---

## 15. File map

| File | Purpose |
|---|---|
| `PROBLEM_STATEMENT.md` | Full framing document — company rationale, problem, metric, Part 1 scope, validation bar, assumptions. Source of truth for **why**. |
| `context.md` | This file — condensed context for loading into a new session. |
| `ARCHITECTURE.md` | Technical build spec for the discovery engine — data contracts, all 8 stages, validation harness, repo layout, cost model, failure modes. Source of truth for **how**. |
| `edge.md` | Edge case catalogue — 143 cases by stage, severity-rated, with the 36 silent-corruption (S1) defences as a build checklist and required test fixtures. |

**LLM stack decision (locked):** Groq + Google Gemini. Two-tier routing — Groq for the
full-corpus relevance gate, Gemini for structured labelling, codebook induction, and insight
synthesis. See `ARCHITECTURE.md` §9. This also enables a cross-provider agreement check (§12.8)
that a single-provider design could not offer.
