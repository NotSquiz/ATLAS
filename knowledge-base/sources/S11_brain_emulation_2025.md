# S11: State of Brain Emulation Report 2025

**Source:** brainemulation.mxschons.com — 200+ page research report by MxSchons GmbH
**Authors:** 5 neuroscientists + 41 expert collaborators (MIT, UC Berkeley, Allen Institute, Warwick, Fudan)
**Date:** January 2025 (report), accessed January 2026
**Type:** Neuroscience research — whole brain emulation (WBE) progress assessment
**Credibility:** Very high for what it covers. Published with DOI (10.5281/zenodo.18377594), CC BY 4.0 license, funded by established institutions. Endorsed by Adam Marblestone (CEO Convergent Research).

**Relevance Warning:** This is NOT about building AI agents. It's about the fundamental neuroscience of replicating biological brains in computers. The direct applicability to our Baby Brains agent is low. But the CONCEPTUAL insights about intelligence, memory, and evolution are worth noting.

---

### S11 — What Brain Emulation Actually Is

Brain emulation replicates actual neural architecture with biological accuracy. This is fundamentally different from what we're building:

| | Brain Emulation | Our Agent (LLM-based) |
|---|---|---|
| Approach | Bottom-up: reconstruct biology | Top-down: optimize for task performance |
| Basis | Physical neural circuits | Statistical patterns in text |
| Method | Map every neuron and synapse | Train on data, fine-tune with RLHF |
| Current state | 302 neurons fully mapped (C. elegans) | Billions of parameters, no neural mapping |
| Goal | Faithful reproduction of cognition | Useful task completion |
| Timeline | Decades away for humans | Available now |

**The report's key distinction:** Brain emulation replicates *causal machinery*. LLMs replicate *behavioral outputs*. We're building behavioral AI, not biological emulation.

---

### S11 — Extracted Items

#### CONCEPTUAL INSIGHTS (Not Direct Tools)

| # | Item | Tags | Relevance | Notes |
|---|------|------|-----------|-------|
| S11.01 | **"The central challenge is acquiring data, not computation"** — data quality limits model quality, not compute power. | `ARCH` `MEMORY` | MEDIUM | Applies to our agent too. We have compute (desktop GPU, cloud APIs). What we lack is DATA — Baby Brains domain knowledge, customer behavior data, content performance data. Investing in data acquisition and quality is more important than upgrading compute. |
| S11.02 | **40-50% of synaptic connections differ between genetically identical worms** — even identical organisms produce different neural wiring. | `AUTONOMY` | LOW | Philosophical: even with identical starting conditions, systems diverge. Our agent will evolve differently from anyone else's even if they start from the same codebase. Individuality emerges from experience, not just architecture. The Love Equation from R31 (memory bias toward positive interactions) is our version of this. |
| S11.03 | **Three-pillar pipeline: Recording (data in) → Connectomics (structure) → Modeling (behavior)** — the WBE architecture. | `ARCH` | MEDIUM | Loose analogy to our agent: **Data in** (voice, messaging, sensors) → **Structure** (knowledge base, memory graph, intent patterns) → **Behavior** (responses, actions, autonomous work). The quality of each layer depends on the one before it. Garbage data → garbage structure → garbage behavior. |
| S11.04 | **< 500 active researchers globally in brain emulation** — a tiny field where individual contributions profoundly shape trajectory. | `COMMUNITY` | LOW | Parallel to personal AI agent space in Jan 2026: small community, early stage, individual contributions matter. Our work on ATLAS/Baby Brains agent is meaningful in this context. |
| S11.05 | **Faithful emulation vs behavioral imitation** — brain emulation seeks to replicate the mechanism, not just the output. AI (and our agent) imitates behavior without replicating the mechanism. | `ARCH` | MEDIUM | Design question: do we care HOW our agent arrives at answers, or only THAT it arrives at correct answers? For safety-critical domains (health, Baby Brains child safety): we DO care about the mechanism. The "Wait" pattern and confidence routing in ATLAS are attempts to make the reasoning process visible, not just the output. |
| S11.06 | **Non-neural factors matter** — hormones, glial cells, vasculature all affect cognition. Brain ≠ just neurons. | `ARCH` | LOW | Analogy: our agent ≠ just the LLM. Context (time of day, user mood, recent events), environment (which device, what's happening), and state (active workout, pending tasks) all affect what the "right" response is. Our Traffic Light system, morning sync, and session state are our "non-neural factors." |

---

### S11 — Why This Matters (And Why It Mostly Doesn't)

**Why it matters:**
- It frames where AI CURRENTLY is versus where intelligence ACTUALLY is. We're building behavioral imitation (useful, practical, available now). Real brain emulation is decades away. This grounding prevents us from over-claiming what our agent is.
- The "data > compute" principle directly applies. Our agent's quality ceiling is determined by the quality of Baby Brains knowledge, not by which model we use.
- The individuality insight (identical worms, different wiring) validates our approach of building a PERSONAL agent that evolves through experience. Mass-produced agents will never match a personal one.

**Why it mostly doesn't matter for us right now:**
- We're not doing neuroscience. We're building a practical assistant.
- The timeline for human brain emulation is measured in decades.
- The technical details (electron microscopy, calcium imaging, C. elegans) are fascinating but not actionable.
- Our agent doesn't need to replicate biological cognition. It needs to schedule workouts, manage Baby Brains content, and send Telegram messages.

---

### S11 — Cross-References

| Item | S11 Says | Previous Sources Say | Synthesis |
|------|---------|---------------------|-----------|
| Data vs compute | Data is the bottleneck, not computation | S6.04: compressed knowledge index beats full injection; S3.07: private data is the moat | **Convergent insight from very different fields.** Neuroscience says data limits brain models. AI practice says knowledge quality limits agent performance. Our investment should be in Baby Brains DATA quality (activities, research, customer insights), not just model upgrades. |
| Individual evolution | Identical organisms develop differently | R31: Love Equation — interactions shape the agent over time; S1.03: recursive self-improvement | **Our agent's individuality comes from its experiences with us.** Architecture matters, but accumulated experience and memory differentiate. This is the "evolution" the user wants — not code changes, but experiential growth. |
| Mechanism vs output | Brain emulation cares about mechanism; AI only cares about output | S8.07: LLMs can't do temporal reasoning despite having API access | **Sometimes mechanism matters.** When the agent fails at calendar dates (S8), it's because the mechanism (LLM reasoning) is wrong for the task, even though the output format is correct. Use the right mechanism for each task: deterministic code for dates, LLM for reasoning, retrieval for facts. |

---

*S11 processed: January 30, 2026*

---
---
