# Problem Statement — Category Exploration on Blinkit

**Company selected:** Blinkit (quick commerce, India — part of Eternal Ltd., formerly Zomato Ltd.)
**Team:** Growth
**Role:** Product Manager
**Date:** 27 July 2026
**Status:** Draft v1 — scope locked for Part 1 (AI-Powered Discovery Engine)

---

## 0. How to read this document

This is the *framing* artifact for the project. It fixes the company, the user, the
business problem, the metric, and the boundaries of what we are solving — **before** any
solution is proposed. It deliberately does **not** contain feature ideas, designs, or a
roadmap. Those are downstream and must be earned by evidence produced from Part 1.

Sections 1–6 define the problem. Section 7 defines the metric. Sections 8–11 define
Part 1 (the discovery engine) — what it must answer, what it must ingest, and how its
output will be judged. Section 12 lists what is explicitly out of scope. Section 13
records the assumptions this document rests on, so they can be challenged.

---

## 1. Company selection and rationale

**Blinkit** is the chosen platform for this project.

Why Blinkit is the right case for a category-exploration problem:

| Factor | Why it makes Blinkit a strong fit |
|---|---|
| **Habit-formed user base** | Blinkit's core value proposition (delivery in ~10 minutes) has moved it from an occasion-based service to a weekly — often multi-weekly — routine for urban households. Repeat behaviour is already established; the problem is *narrow* repeat behaviour. |
| **Wide catalogue, narrow consumption** | Blinkit has aggressively expanded beyond grocery into personal care, baby care, pet supplies, home & kitchen, electronics and accessories, festive/seasonal ranges, and pharmacy-adjacent items. Catalogue breadth has grown much faster than the average user's basket breadth. |
| **Dark-store economics** | Blinkit's unit economics depend on average order value (AOV) and basket size, not just order frequency. A user who adds one new category to their basket improves contribution margin per delivery trip without adding a delivery trip. Category exploration is therefore a *margin* lever, not only an engagement lever. |
| **Competitive parity on speed** | Speed is no longer a differentiator against Zepto, Swiggy Instamart, BigBasket, Flipkart Minutes and Amazon's quick-commerce push. Assortment discovery and share-of-basket are the emerging battlegrounds. |
| **Rich public discourse** | Blinkit generates a high, continuous volume of public user feedback across App Store, Play Store, Reddit, X, YouTube and consumer forums — enough raw material to build a genuine listening system rather than a toy demo. |

**Note on scope of claims:** Any market-size, GOV, MTU or share figures used later in this
project must be sourced and cited from public filings (Eternal Ltd. quarterly results and
shareholder letters) or credible published research. This document intentionally avoids
asserting unverified numbers; placeholders are marked `[TO VERIFY]` where a figure would
strengthen the argument.

---

## 2. Business context

Quick commerce in India has completed its first act. The category proved that sub-15-minute
delivery of groceries and essentials is a viable, repeatable consumer behaviour rather than
a novelty. Blinkit sits at or near the front of that market.

The consequence of winning act one is the problem of act two:

- **Acquisition is expensive and slowing.** The pool of urban users willing to try quick
  commerce has been heavily worked. Incremental growth from new-user acquisition is getting
  costlier per user.
- **Frequency has a ceiling.** A household can only need groceries so often. Beyond a point,
  pushing order frequency yields diminishing returns and can degrade margin (more trips,
  smaller baskets).
- **Basket breadth is the remaining headroom.** The same user, on the same delivery trip,
  buying from one more category is the cheapest incremental revenue available to the
  business. It requires no new user, no new trip, and no new dark store.

Blinkit has already invested heavily in the *supply* side of this — expanding the catalogue
into new categories. The gap is on the *demand* side: users are not discovering, trusting,
or trying those categories at the rate the catalogue expansion assumed.

---

## 3. The user behaviour we are trying to change

The typical Blinkit user has converged on a **stable, small repertoire of categories** and
shops almost entirely within it.

The observed behaviour pattern:

1. A user onboards with an urgent, high-intent need — usually a grocery top-up, milk/bread,
   or a snacks-and-beverages run.
2. The experience works. Delivery is fast. Trust is established.
3. The user builds a mental model: *"Blinkit is for [my 2–3 categories]."*
4. Subsequent sessions become **retrieval, not browsing.** The user opens the app, searches
   or uses "Order again", adds known SKUs, and checks out — often in under 90 seconds.
5. The mental model calcifies. Categories outside it become invisible, even when they are
   one tap away on the home screen.

This is a rational user behaviour. Speed of task completion *is* the product. Every
efficiency the app has added — reorder lists, saved carts, search-first navigation,
personalised rails of previously bought items — has optimised for the fast completion of a
*known* need. The same optimisations actively suppress exploration.

**The core tension:** the product is engineered to help users finish faster, and exploration
requires users to slow down. Any solution must resolve this tension, not ignore it.

### Illustrative transitions we want to enable

| From (established behaviour) | To (new category) |
|---|---|
| Buys groceries weekly | Starts buying pet supplies |
| Buys snacks & beverages | Starts buying personal care |
| Buys household essentials | Starts buying baby products |
| Buys fruits & vegetables | Starts buying home & kitchen |
| Buys beverages | Starts buying health & wellness |

These are illustrative, not a target list. Part 1 must tell us which transitions are
*actually* plausible and desired by users, and which are wishful thinking on our part.

---

## 4. Problem statement

> Blinkit users have made the platform part of their weekly routine, but that routine is
> narrow. A large share of Monthly Active Customers purchase repeatedly from the same small
> set of categories and rarely, if ever, buy from a category that is new to them — despite
> Blinkit stocking those categories, delivering them at the same speed, and often at
> competitive prices.
>
> The result is a widening gap between **catalogue breadth** and **basket breadth**: Blinkit
> has invested in expanding what it can deliver, but the average user's mental model of
> "what Blinkit is for" has not expanded with it. Every category a user never tries is
> revenue that is available on an already-paid-for delivery trip and is being left on the
> table.
>
> **We do not currently know why.** We can see *that* exploration is low in our analytics,
> but analytics describe behaviour, not motivation. We cannot tell from clickstream data
> whether users don't explore because they don't know the category exists, don't trust
> Blinkit's quality in it, are already loyal to another retailer for it, find the price
> unconvincing, lack the information needed to choose confidently, or simply never slow down
> enough to notice. Each of those causes implies a completely different solution, and
> building against the wrong one wastes a quarter.

**Therefore, before proposing any solution, we must build a system that can answer *why* —
at scale, from the words of real users, across every public channel where they talk about
quick commerce.**

That system is Part 1: the AI-Powered Discovery Engine.

---

## 5. Strategic goal

The company-level goal this project serves:

> **Increase the percentage of Monthly Active Customers who purchase products from at least
> one new category every month.**

This project's contribution to that goal is delivered in two parts:

- **Part 1 (this phase):** Build an AI-powered discovery engine that analyses user feedback
  at scale and produces validated, evidence-backed insight into the drivers and barriers of
  category exploration.
- **Part 2 (subsequent phase):** Use those insights to design and prioritise interventions,
  with success measured against the metric defined in Section 7.

**Part 1 does not move the metric. It earns the right to try.** Its output is understanding,
not features.

---

## 6. Who this affects

| Stakeholder | Stake in the outcome |
|---|---|
| **Users** | Get more of their household needs met in one trusted, fast place — *if* the exploration we drive is genuinely useful and not manipulative. |
| **Growth team (us)** | Owns the metric. Needs a defensible causal story before committing engineering capacity. |
| **Category / merchandising teams** | Have invested in assortment in under-consumed categories. Need demand-side help to justify continued expansion. |
| **Supply chain / dark store ops** | Basket breadth changes picking patterns and per-store SKU velocity. Must be consulted before we drive volume into cold categories. |
| **Brand partners** | New-category trial is a strong commercial proposition for partner-funded sampling and launches. |
| **Finance** | Cares about contribution margin per order, not just order count. Basket breadth is the cleanest path there. |

---

## 7. The metric

### 7.1 Primary metric — Category Exploration Rate (CER)

> **CER (month M)** = (Number of Monthly Active Customers in month M who purchased at least
> one product from a category that is *new to that customer*) ÷ (Total Monthly Active
> Customers in month M) × 100

### 7.2 Definitions (these must be agreed before any measurement)

| Term | Working definition | Open decision |
|---|---|---|
| **Monthly Active Customer (MAC)** | A customer who placed ≥1 delivered order in the calendar month. | Do cancelled/returned orders count? Proposal: exclude fully-refunded orders. |
| **Category** | The **L1 taxonomy node** (e.g. Grocery & Staples, Snacks & Beverages, Household Essentials, Personal Care, Baby Care, Pet Supplies, Home & Kitchen, Electronics & Accessories, Health & Wellness). | L1 is proposed as the default. L2 would inflate CER and reward trivial adjacency (e.g. "shampoo → conditioner"). **Recommendation: measure at L1, report L2 as a secondary diagnostic.** |
| **New category (to a customer)** | A category from which the customer has **not** purchased in the trailing 6 months prior to month M. | Lookback window is the key lever. 6 months is proposed as the balance between "genuinely new" and "we don't have infinite history". Alternatives: lifetime (too strict), 3 months (too loose — captures seasonal returns as exploration). |
| **Purchase** | A delivered, non-returned line item. | Free samples and 100%-discounted items should be flagged and reported separately — they are trial, but not commercial validation. |

### 7.3 Why this metric and not something else

- **Not "categories per user"** — an average hides the distribution. A few power users buying
  across 9 categories can mask the fact that the median user buys from 2.
- **Not "new category orders"** — an order-level metric rewards splitting baskets, which hurts
  margin. We want the same trip to carry more categories.
- **CER is a per-user, per-month binary.** It is simple to explain to leadership, hard to
  game, and directly reflects the strategic goal's wording.

### 7.4 Guardrail metrics (a CER win that breaks any of these is not a win)

| Guardrail | Why |
|---|---|
| **Time-to-checkout for repeat-intent sessions** | If we make exploration happen by slowing down the core task, we have damaged the product's central promise. |
| **Return / refund rate in newly explored categories** | Trial that ends in a return is worse than no trial — it teaches the user that Blinkit is bad at that category. |
| **Repeat rate on the newly explored category (M+1, M+2)** | One-off trial driven by a discount is a vanity number. Exploration only counts if it *sticks*. |
| **AOV and contribution margin per order** | Exploration must add to the basket, not cannibalise it. |
| **App rating and complaint volume** | Aggressive cross-category promotion is a well-known source of user irritation. |
| **Order frequency / retention** | Must not decline. Exploration is additive to the routine, not a replacement for it. |

### 7.5 Segmentation (CER must always be reported cut by these)

- **Tenure**: new (<1 month) / growing (1–6 months) / established (6+ months)
- **Frequency**: light / medium / heavy
- **Current category breadth**: 1–2 categories / 3–4 / 5+
- **Household context**: has-baby signals, has-pet signals, single vs family basket patterns
- **City tier and metro**

A single aggregate CER number will hide the actual problem. Part 1 must tell us which
segments are structurally more willing to experiment.

---

## 8. Part 1 — Scope of the AI-Powered Discovery Engine

### 8.1 Objective

Build a working, repeatable AI system that ingests unstructured public user feedback at
scale and converts it into structured, validated, decision-grade insight about category
exploration behaviour on Blinkit and in Indian quick commerce generally.

### 8.2 What "at scale" means here

The engine must be built to handle a corpus that is too large to read manually — thousands of
reviews and posts — and must be **re-runnable**, not a one-off manual analysis. A human
reading 100 reviews and writing a summary does not satisfy this requirement. The system must:

- ingest from multiple heterogeneous sources into a single normalised schema,
- apply consistent, auditable labelling across the entire corpus,
- surface themes bottom-up from the data rather than confirming a pre-written hypothesis list,
- keep every insight traceable back to the specific verbatims that produced it,
- and be measurably reliable, not just plausible-sounding.

### 8.3 Required data sources

| Source | What it is good for | Collection considerations |
|---|---|---|
| **Google Play Store reviews** (Blinkit + competitors) | High volume, star-rated, timestamped, version-tagged. Best signal on friction and complaints. | Largest single source. Must be sampled across rating bands, not just 1-star. |
| **Apple App Store reviews** | Skews to a different (often higher-income, iOS) demographic. Useful as a segment contrast. | Lower volume than Play Store. Public RSS review feed is available per storefront. |
| **Reddit** (r/india, r/bangalore, r/mumbai, r/delhi, r/IndiaSpeaks, r/personalfinanceindia, city subs) | Longest-form, most candid reasoning. Best source for *why* — comparisons, trust, price rationalisation. | Signal-rich but volume-light. Threads must be read with comment trees, not just top posts. |
| **Community forums & consumer complaint sites** | Structured grievances; good for trust and quality-perception failures. | Heavily skewed negative — must be weighted accordingly. |
| **Social media (X, Instagram comments, YouTube comments)** | Real-time reaction, especially to category launches and campaigns. | Noisy; requires aggressive spam/bot filtering. |
| **Product reviews on-platform and on competitor platforms** | Category-specific quality and trust signals — exactly what a user needs before trying a new category. | The most direct evidence on "what information do users need before trying". |
| **General quick-commerce discussion** (news comments, newsletters, creator content) | Category-level narrative and framing that shapes user expectations. | Context, not primary evidence. |

**Competitor coverage is mandatory, not optional.** A barrier that appears in Blinkit
feedback *and* in Zepto/Instamart feedback is a category-level problem. One that appears only
in Blinkit feedback is our problem specifically. That distinction changes the solution
completely, and it is only visible if we collect both.

### 8.4 Research questions the engine must answer

The engine's output must be able to answer each of the following with evidence:

1. **Why do users repeatedly buy from the same categories?**
   What is the actual mechanism — habit, speed-optimisation, trust concentration, or
   deliberate loyalty to another retailer for other categories?

2. **What prevents users from exploring new categories?**
   Rank the barriers. Distinguish awareness gaps from trust gaps from price gaps from
   information gaps from friction gaps. These require different solutions.

3. **How do users discover products today?**
   What is the real discovery path — search, home rails, reorder lists, external
   recommendation, offline observation, word of mouth? Where does discovery actually happen,
   and where does it demonstrably not?

4. **What role do habits play in shopping behaviour?**
   How quickly does the repertoire calcify after onboarding? Is there a window in which users
   are more open, and does it close?

5. **What information do users need before trying a new category?**
   What is the specific missing input that blocks the first purchase — freshness/expiry
   guarantees, brand authenticity, return policy, sizing, ingredient detail, social proof,
   price comparison?

6. **What frustrations emerge repeatedly?**
   Which recurring complaints, even when unrelated to exploration on their surface,
   suppress the trust required for a user to risk trying something new?

7. **Which user segments are more likely to experiment?**
   Who explores today, and what distinguishes them? This determines where any intervention
   should be piloted.

8. **What unmet needs emerge consistently across discussions?**
   What are users asking for that we are not providing — and which of those requests are
   actually latent category-exploration demand?

### 8.5 What the engine must demonstrate

Per the project brief, the deliverable must show four things explicitly:

| Requirement | What must be evidenced |
|---|---|
| **How the workflow gathers and analyses data** | The end-to-end pipeline: source connectors, normalisation schema, deduplication, language handling (English, Hindi, Hinglish, and other Indic-script and romanised input), spam/bot filtering, and the LLM analysis stage. Architecture must be documented and the code must run. |
| **How themes are identified** | The path from individual verbatim → structured label → clustered theme. Themes must emerge from the data, not from a pre-written list. The codebook must be documented, including how it evolved. |
| **How insights are generated** | The step from "theme with N mentions" to "insight with a claim, a mechanism, an affected segment, and an implication". Frequency alone is not an insight. |
| **How insight quality was validated** | Explicit, measured validation — not a claim of confidence. See Section 9. |

---

## 9. Insight quality — the validation bar

An LLM-based analysis system is trivially capable of producing fluent, confident, and wrong
output. The credibility of this entire project rests on being able to show that it did not.

The engine must be validated on at least the following dimensions, with reported numbers:

| Dimension | Method | Bar |
|---|---|---|
| **Labelling reliability** | Human-labelled gold set drawn at random from the corpus, compared against model labels. Report agreement (and, where applicable, Cohen's κ). | Substantial agreement, with disagreements inspected and explained — not hidden. |
| **Groundedness / anti-hallucination** | Every insight must cite verbatim quotes. Each cited quote must be verifiable as literally present in the source corpus. Automated string-level check. | 100% of cited quotes traceable to a real source document. Any fabricated quote is a hard failure. |
| **Stability** | Re-run the same analysis with a different sample order and/or temperature setting; compare the resulting theme set. | Major themes must be reproducible across runs. Themes that appear only once are noise. |
| **Saturation** | Plot new-theme discovery against corpus size. | The curve must flatten — evidence that the corpus is large enough that we are no longer finding new things. If it hasn't flattened, we have not collected enough data. |
| **Coverage** | Share of the corpus that maps to at least one theme. | High coverage; a large unassigned residue means the codebook is incomplete. |
| **Source triangulation** | Cross-check whether each major theme appears in more than one independent source. | Themes present in only one source are flagged as lower-confidence and reported as such. |
| **Bias awareness** | Explicitly characterise the skew of the corpus (public reviews over-represent extremes; Reddit over-represents metro, male, tech-literate users). | Documented as a limitation on every insight, with its direction of bias stated. |

**Every insight in the final output must carry:** a confidence level, the volume of evidence
behind it, the sources it was triangulated across, and the known bias affecting it.

---

## 10. Part 1 deliverables

1. **A working discovery engine** — runnable code, documented architecture, reproducible
   end-to-end from raw ingestion to final insight output.
2. **A documented corpus** — sources, collection method, volume, time range, language mix, and
   an honest statement of its limitations and skew.
3. **A theme codebook** — the taxonomy of barriers, drivers, discovery paths, and unmet needs
   that emerged from the data, with definitions and representative verbatims for each.
4. **A validation report** — the measured numbers from Section 9, including where the system
   performed poorly.
5. **An insight report** — the answers to the eight research questions in Section 8.4, each
   with evidence, affected segment, confidence, and implication.
6. **A segment view** — which user segments explore, which don't, and what differentiates them.

---

## 11. Definition of done for Part 1

Part 1 is complete when:

- [ ] The pipeline runs end-to-end on a real, multi-source corpus and can be re-run on new data.
- [ ] All eight research questions in Section 8.4 are answered with cited evidence.
- [ ] Every validation dimension in Section 9 has a reported number, including the bad ones.
- [ ] Every insight is traceable to specific verbatims, and every quote is verifiable.
- [ ] Barriers to exploration are ranked, and each is classified by type (awareness / trust /
      price / information / friction / habit / external loyalty).
- [ ] Segments more and less likely to explore are identified and characterised.
- [ ] Limitations and biases of the analysis are stated plainly, not buried.

---

## 12. Explicitly out of scope for Part 1

- Solution design, feature concepts, wireframes, or UX proposals.
- Prioritisation frameworks, roadmaps, or effort estimates.
- Experiment design or A/B test plans.
- Financial modelling or business-case sizing.
- Any internal Blinkit proprietary data (we have none; this is a public-data project).
- Personally identifiable information — no user identity is collected, stored, or inferred.

Bringing solutions forward before the evidence is complete is the specific failure mode this
project is structured to avoid.

---

## 13. Assumptions this document rests on

These are stated so they can be challenged rather than silently inherited:

1. **Public feedback is a usable proxy for user motivation.** It is skewed toward extremes and
   toward vocal, metro, digitally-fluent users. We assume it is directionally informative
   about *mechanisms* even though it is not representative in *proportion*. Section 9's bias
   requirement exists to keep this assumption honest.
2. **Low category exploration is a demand-side problem, not purely a supply-side one.** If
   Part 1 finds that users don't explore because Blinkit genuinely lacks depth or quality in
   those categories, that is a merchandising finding, and we must report it as such rather
   than force a growth-lever conclusion.
3. **L1 category taxonomy is the right measurement grain.** To be validated; see Section 7.2.
4. **Exploration is good for the user, not just the business.** The project assumes that
   consolidating genuine household needs into one fast, trusted service is a real user
   benefit. If Part 1 finds that users deliberately and rationally split categories across
   retailers, "increase exploration" may be the wrong goal, and we should say so.
5. **We have no access to Blinkit internal analytics.** All quantitative behavioural claims in
   this project are inferred from public discourse and must be labelled as such. Metric
   definitions in Section 7 are specified so they *could* be implemented internally, but will
   not be measured by us in this project.

---

## 14. Open questions to resolve before Part 2

| # | Question | Needed to decide |
|---|---|---|
| 1 | L1 or L2 taxonomy for the CER definition? | Whether the metric rewards genuine exploration or adjacency. |
| 2 | 3-month, 6-month, or lifetime lookback for "new category"? | The sensitivity and honesty of the metric. |
| 3 | Do discounted/free trial purchases count toward CER? | Whether the metric can be bought with margin. |
| 4 | What is the acceptable trade-off between exploration and time-to-checkout? | The design constraint for every solution in Part 2. |
| 5 | Which categories are we actually ready to drive demand into (supply, quality, ops)? | Prevents driving trial into categories that will disappoint and destroy trust. |

---

## Appendix A — Glossary

| Term | Meaning |
|---|---|
| **Quick commerce (q-commerce)** | Retail model delivering small baskets in ~10–30 minutes from hyperlocal dark stores. |
| **Dark store** | A micro-warehouse serving online orders only, with no customer walk-in. |
| **MAC** | Monthly Active Customer — see Section 7.2. |
| **CER** | Category Exploration Rate — the primary metric, Section 7.1. |
| **AOV** | Average Order Value. |
| **Basket breadth** | The number of distinct categories present in a customer's purchases over a period. |
| **Catalogue breadth** | The number of distinct categories the platform stocks. |
| **Repertoire** | The stable set of categories an individual customer habitually buys from. |
| **L1 / L2 category** | Levels of the product taxonomy — L1 being the broadest (e.g. "Personal Care"), L2 a sub-level (e.g. "Hair Care"). |
| **Verbatim** | A single unedited piece of user-authored text (a review, post, or comment). |
| **Saturation** | The point at which additional data stops producing new themes. |
| **Groundedness** | The property that every generated claim is traceable to real source text. |

---

*End of problem statement. Part 1 build begins against this scope.*
