# 3B: Voice Generation Tools -- Extracted Data

Source file: `results/3B.md`
Extraction date: 2026-02-01
Source context: Voice AI for Australian Parenting Content (Baby Brains pipeline)
Hardware baseline stated in source: 8GB VRAM GPU (upgraded from RTX 3050 Ti 4GB)

> **CRITICAL NOTE**: The source document assumes an 8GB GPU upgrade has occurred. The
> CLAUDE.md project spec lists the actual hardware as **RTX 3050 Ti 4GB**. All "runs
> on your GPU" claims in 3B refer to 8GB, NOT 4GB. This extraction flags both.

---

## TOOL-BY-TOOL BREAKDOWN

### Kokoro TTS

- **Current version**: v1.0 (released January 2025). No v2 announced. [CLAIMED]
- **Parameters**: 82 million (~350MB model size) [CLAIMED]
- **VRAM requirement**: 2-3GB [CLAIMED]
- **Runs on RTX 3050 Ti 4GB**: YES -- 2-3GB fits within 4GB. [VERIFIED against stated VRAM]
- **Processing speed**: 36x real-time (free Colab) to 210x real-time (RTX 4090) [CLAIMED]
  - 60-second voiceover in under 0.3 seconds at best-case hardware [CLAIMED]
  - No specific RTX 3050 Ti benchmark given
- **Voice cloning**: NOT SUPPORTED. Too small a training dataset (<100 hours). [CLAIMED]
- **Voice blending**: Supported -- combine existing voices with weighted ratios (e.g., "bm_daniel(2)+bm_george(1)") [CLAIMED]
- **Australian voices**: NONE. 8 British English voices available:
  - Female: bf_alice, bf_emma, bf_isabella, bf_lily
  - Male: bm_daniel, bm_fable, bm_george, bm_lewis
- **Australian/British voice quality**: British male voices (bm_george, bm_daniel) described as workable for educational content but cannot capture authentic Australian inflection [CLAIMED]
- **Batch capability**: Implied yes (extreme speed enables rapid batch processing)
- **Cost**: FREE (self-hosted, Apache 2.0 license, commercial use OK) [VERIFIED -- Apache 2.0]
- **HuggingFace downloads**: 4.3M+ monthly (hexgrad/Kokoro-82M: 4.29M listed separately) [CLAIMED]
- **TTS Arena ranking**: #17, ELO 1500, 45% win rate vs proprietary models [CLAIMED]
- **Recent improvements**: None noted -- still at v1.0 since January 2025

---

### ElevenLabs

- **Current pricing (February 2026, credit-based: 1 character = 1 credit)**:

| Plan | Monthly Cost | Credits | ~Minutes (v2/v3) | Voice Cloning |
|------|-------------|---------|-------------------|---------------|
| Free | $0 | 10,000 | ~10 min | None |
| Starter | $5 | 30,000 | ~30 min | Instant (IVC) |
| Creator | $22 | 100,000 | ~100 min | Professional (PVC) |
| Pro | $99 | 500,000 | ~500 min | All features |
| Scale | $330 | 2,000,000 | ~2,000 min | All features |

[CLAIMED -- pricing may have changed since source was written]

- **Voice cloning**:
  - **Instant Voice Cloning (IVC)**: 10-30 seconds minimum (1-2 minutes recommended). Quality from 10 seconds described as "usable for fast iteration" but not optimal. Available from Starter ($5) tier. [CLAIMED]
  - **Professional Voice Cloning (PVC)**: Requires 30+ minutes of clean audio. Produces "hyper-realistic" results "indistinguishable from original." Available from Creator ($22) tier. [CLAIMED]
- **Australian accent cloning reliability**:
  - IVC: May not capture particularly distinctive Australian accents perfectly (relies on prior training data). [CLAIMED]
  - PVC: More reliable -- trains directly on voice data. [CLAIMED]
  - v3 Audio Tags: `[Australian accent]`, `[strong Australian accent][warm]` -- can be applied to any voice, combined with emotion tags, switched mid-script. [CLAIMED]
  - Native **English (Australia)** listed as supported language option. [CLAIMED]
  - Voice Library includes searchable Australian community voices. [CLAIMED]
- **Cost for 20-30 VO tracks/month**:
  - At 30-90 seconds per track = ~15-45 minutes/month total
  - Creator plan ($22/month, 100 min) recommended as "adequate headroom" [CLAIMED]
  - Source later revises to Starter ($5/month, 30 min) for premium-only use in hybrid setup [CLAIMED]
- **TTS Arena ranking**: #7 (Eleven Flash v2.5), ELO 1548, 56% win rate [CLAIMED]
- **Minutes per tier per month**: See table above
- **API integration**: Official Python SDK available [CLAIMED]

---

### CosyVoice (Alibaba)

- **Current state**: CosyVoice 0.5B / Fun-CosyVoice 3.0 -- Alibaba's flagship TTS [CLAIMED]
- **VRAM requirement**: ~8GB minimum (described as "at the limit") [CLAIMED]
- **Runs on RTX 3050 Ti 4GB**: NO -- requires ~8GB minimum. [VERIFIED against stated VRAM]
- **Runs on 8GB GPU**: BORDERLINE -- "at the limit" [CLAIMED]
- **Voice cloning**: 3-10 seconds reference audio, 77-78% speaker similarity [CLAIMED]
- **Languages**: 9 including English, plus 18 Chinese dialects [CLAIMED]
- **Australian accent**: No explicit support; relies on zero-shot cloning from reference audio [CLAIMED]
- **Quality metrics**: 0.81% CER, "outperforms models 3x larger" [CLAIMED]
- **Streaming**: 150ms first-packet latency [CLAIMED]
- **License**: Apache 2.0 [CLAIMED]
- **TTS Arena ranking**: #25 (CosyVoice 2.0), ELO 1358, 28% win rate [CLAIMED]
- **Clone quality assessment**: "Very good" [CLAIMED]

---

### Chatterbox (Resemble AI)

- **Current state**: Chatterbox Turbo (December 2025 release). Original 0.5B model + Turbo variant (350M params). [CLAIMED]
- **Key claim**: 63.75% preferred over ElevenLabs in blind evaluations [CLAIMED -- no source study cited]
- **VRAM requirement**: 8GB borderline for original; Turbo variant (350M params) more efficient [CLAIMED]
- **Runs on RTX 3050 Ti 4GB**: NO -- 8GB is already "borderline." Turbo at 350M params may be tighter but still unlikely on 4GB. [INFERRED -- not directly tested]
- **Runs on 8GB GPU**: BORDERLINE ("if it runs stably on your 8GB card") [CLAIMED with hedging]
- **Voice cloning**: 5-10 seconds of reference audio (shortest in class) [CLAIMED]
- **Unique features**:
  - Emotion exaggeration control [CLAIMED]
  - Paralinguistic tags: [laugh], [cough], [sigh] [CLAIMED]
  - PerTh neural watermark embedded (imperceptible, survives compression) [CLAIMED]
- **Languages**: 23 including English [CLAIMED]
- **Australian accent**: Clone from sample; "excellent voice fidelity" [CLAIMED]
- **License**: MIT (fully commercial) [CLAIMED]
- **Cost**: FREE (self-hosted). Install: `pip install chatterbox-tts` or Docker [CLAIMED]
- **Processing speed**: ~2-5 seconds per 60s clip [CLAIMED -- from pipeline architecture section]
- **HuggingFace downloads**: 682k (ResembleAI/chatterbox) [CLAIMED]
- **TTS Arena ranking**: #16, ELO 1505, 47% win rate [CLAIMED]
- **Source's primary recommendation for bulk content** [CLAIMED]

---

### F5-TTS

- **VRAM requirement**: ~6-8GB (6.4GB for 800-character paragraphs) [CLAIMED]
- **Runs on RTX 3050 Ti 4GB**: NO -- minimum ~6GB. [VERIFIED against stated VRAM]
- **Runs on 8GB GPU**: YES ("comfortable fit") [CLAIMED]
- **Parameters**: 335M [CLAIMED]
- **Speed**: RTF 0.15 (fast) [CLAIMED]
- **Voice cloning**: ~10 seconds reference audio [CLAIMED]
- **Quality**: "Excellent" clone quality [CLAIMED]
- **License**: Code is MIT, but **models are CC-BY-NC (non-commercial)** [CLAIMED -- COMMERCIAL BLOCKER]
  - Commercial alternative: OpenF5-TTS-Base (Apache 2.0) available but "still alpha" [CLAIMED]
- **Australian accent**: Not explicitly mentioned; presumably via zero-shot cloning
- **Batch capability**: Not explicitly stated

---

### Fish Speech / OpenAudio S1

- **Current state**: Fish Speech evolved into OpenAudio S1 (June 2025). 4B full model. [CLAIMED]
- **VRAM requirement**: 12GB recommended (full model) [CLAIMED]
- **Runs on RTX 3050 Ti 4GB**: NO [VERIFIED against stated VRAM]
- **Runs on 8GB GPU**: NO -- requires 12GB+ [CLAIMED]
- **Quality**: #1 on TTS-Arena, WER 0.008, CER 0.004 (best in class) [CLAIMED]
- **Emotion markers**: 40+ [CLAIMED]
- **License**: Apache 2.0 (code), but commercial API required for production [CLAIMED -- ambiguous]
- **API pricing (Fish Audio API)**:
  - $9.99/200 minutes OR $15/1M characters [CLAIMED]
  - Described as ~70% cheaper than ElevenLabs [CLAIMED]
- **Voice cloning**: 10-30 seconds reference (via API) [CLAIMED]
- **Alternative recommendation**: Use Fish Audio API as cloud alternative to ElevenLabs [CLAIMED]

---

### StyleTTS2

- **Current state**: Established model, benchmark-proven "human-level" naturalness [CLAIMED]
- **VRAM requirement**: ~6GB baseline [CLAIMED]
- **Runs on RTX 3050 Ti 4GB**: NO -- requires ~6GB. [VERIFIED against stated VRAM]
- **Runs on 8GB GPU**: YES [CLAIMED]
- **Voice cloning**: Yes, via target voice path [CLAIMED]
- **License**: MIT (core), GPL for some dependencies [CLAIMED]
- **Known issues**: Memory leak issues reported in some long-form use cases [CLAIMED]
- **TTS Arena ranking**: #24, ELO 1369, 26% win rate [CLAIMED]

---

### XTTS v2 (Coqui / idiap fork)

- **Current state**: Classic voice cloning model. Most downloaded on HuggingFace: 6.44M downloads (coqui/XTTS-v2). [CLAIMED]
- **VRAM requirement**: Not explicitly stated, but listed as "comfortable fit" on 8GB [CLAIMED]
- **Runs on RTX 3050 Ti 4GB**: MAYBE -- VRAM not explicitly stated. Given 8GB is "comfortable," 4GB is uncertain.
- **Voice cloning**: 6 seconds reference audio, 85-95% speaker similarity [CLAIMED]
- **License**: CPML (Coqui Public Model License) [CLAIMED -- check commercial terms]
- **Quality**: "Good" clone quality [CLAIMED]
- **Australian accent**: Not explicitly mentioned

---

### Sesame CSM-1B

- **Current state**: Best VRAM efficiency for quality [CLAIMED]
- **VRAM requirement**: 4.5GB on CUDA [CLAIMED]
- **Runs on RTX 3050 Ti 4GB**: NO -- 4.5GB exceeds 4GB. [VERIFIED against stated VRAM]
- **Runs on 8GB GPU**: YES (best fit in Tier 1) [CLAIMED]
- **Voice cloning**: Yes, via speaker context (2-3 minutes reference recommended) [CLAIMED]
- **Strength**: Conversational speech with natural pauses, "umms," and turn-taking [CLAIMED]
- **License**: CC (requires Llama 3.2-1B access) [CLAIMED]
- **Australian accent**: Clone from reference audio [CLAIMED]
- **Best for**: Dialogue-style educational content [CLAIMED]

---

### Spark-TTS 0.5B

- **Current state**: Best zero-shot cloning on low VRAM [CLAIMED]
- **VRAM requirement**: "Comfortably fits 8GB", RTF ~1.0 on RTX 2070 [CLAIMED]
- **Runs on RTX 3050 Ti 4GB**: MAYBE -- described as "comfortably fits 8GB" but no 4GB test. Given 0.5B params, plausible but unverified.
- **Runs on 8GB GPU**: YES (comfortable) [CLAIMED]
- **Voice cloning**: Zero-shot from short audio clip (no training required) [CLAIMED]
- **Languages**: English + Chinese with cross-lingual cloning [CLAIMED]
- **License**: Apache 2.0 (commercial OK) [CLAIMED]
- **Controls**: Gender, pitch, speaking rate [CLAIMED]
- **Australian accent**: Clone directly from sample [CLAIMED]
- **TTS Arena ranking**: #26, ELO 1342, 25% win rate [CLAIMED]
- **Source's fallback recommendation** if Chatterbox unstable on 8GB [CLAIMED]

---

### Zonos (Zyphra AI)

- **VRAM requirement**: 6GB+ [CLAIMED]
- **Runs on RTX 3050 Ti 4GB**: NO -- requires 6GB+. [VERIFIED against stated VRAM]
- **Parameters**: 1.6B [CLAIMED]
- **Voice cloning**: 5-30 seconds reference [CLAIMED]
- **Features**: Emotion, pitch, and speed control [CLAIMED]
- **License**: Apache 2.0 [CLAIMED]
- **Requirement**: RTX 3000+ series GPU [CLAIMED]

---

### Dia 1.6B/2B (Nari Labs)

- **VRAM requirement**: 7.4GB baseline, peaks to 10GB [CLAIMED]
- **Runs on RTX 3050 Ti 4GB**: NO [VERIFIED against stated VRAM]
- **Runs on 8GB GPU**: MARGINAL ("marginal on 8GB cards") [CLAIMED]
- **Voice cloning**: Zero-shot from seconds of audio + transcript [CLAIMED]
- **Multi-speaker**: [S1], [S2] tags for dialogue [CLAIMED]
- **Non-verbal sounds**: Laughs, sighs, coughs [CLAIMED]
- **License**: Apache 2.0 [CLAIMED]
- **Languages**: English only [CLAIMED]
- **Optimization**: Quantized versions planned (not yet available) [CLAIMED]
- **Dia2**: Upgraded dialogue synthesis (November 2025) [CLAIMED]

---

### MaskGCT

- **VRAM requirement**: 16GB+ required (fails on 8GB after loading w2v-bert-2.0) [CLAIMED]
- **Runs on RTX 3050 Ti 4GB**: NO [VERIFIED]
- **Quality**: "SOTA on quality, similarity, and intelligibility benchmarks" [CLAIMED]
- **Architecture**: Non-autoregressive [CLAIMED]

---

### Orpheus TTS (3B full)

- **VRAM requirement**: ~15GB full model [CLAIMED]
- **Runs on RTX 3050 Ti 4GB**: NO for full model. MAYBE for quantized/smaller variants.
  - Quantized Q8 versions available [CLAIMED]
  - Smaller variants: 1B, 400M, 150M [CLAIMED]
  - Unsloth claims 70% VRAM reduction with fine-tuning optimizations [CLAIMED]
- **Emotion tags**: 8 nonverbals + 8 emotions [CLAIMED]
- **License**: Apache 2.0 [CLAIMED]

---

### Microsoft VibeVoice-1.5B

- **Release**: August 2025 [CLAIMED]
- **Key capability**: Up to 90 minutes continuous multi-speaker generation [CLAIMED]
- **HuggingFace downloads**: 390k [CLAIMED]
- **VRAM**: Not specified in source

---

### Vocu V3.0

- **Type**: Proprietary [CLAIMED]
- **TTS Arena ranking**: #1, ELO 1623, 57% win rate [CLAIMED]
- **No other details provided**

---

## COMPARISON TABLE

| Tool | Cost | VRAM | Fits 4GB? | Fits 8GB? | Australian Accent | Voice Cloning | Clone Ref Audio | License | TTS Arena Rank | Batch |
|------|------|------|-----------|-----------|-------------------|---------------|-----------------|---------|----------------|-------|
| Kokoro v1.0 | Free | 2-3GB | YES | YES | No (British approx) | No | N/A | Apache 2.0 | #17 (45%) | YES (extreme speed) |
| ElevenLabs | $5-330/mo | Cloud | N/A | N/A | YES (native + tags) | Yes (IVC/PVC) | 10s (IVC) / 30min (PVC) | Commercial | #7 (56%) | YES (API) |
| Chatterbox Turbo | Free | ~8GB | NO | Borderline | Clone from sample | Yes | 5-10s | MIT | #16 (47%) | Yes |
| Spark-TTS 0.5B | Free | <8GB | MAYBE | YES | Clone from sample | Yes (zero-shot) | Short clip | Apache 2.0 | #26 (25%) | Yes |
| CosyVoice 0.5B | Free | ~8GB | NO | Borderline | Clone from sample | Yes | 3-10s | Apache 2.0 | #25 (28%) | Yes |
| F5-TTS | Free | 6-8GB | NO | YES | Not stated | Yes | ~10s | MIT/CC-BY-NC | Not ranked | Yes |
| Fish Audio API | $9.99-15 | Cloud | N/A | N/A | Not stated | Yes | 10-30s | Apache 2.0/API | #1 (claimed) | YES (API) |
| StyleTTS2 | Free | ~6GB | NO | YES | Not stated | Yes | Target voice path | MIT/GPL | #24 (26%) | Yes |
| XTTS v2 | Free | ~6-8GB est. | MAYBE | YES | Not stated | Yes | 6s | CPML | Not ranked | Yes |
| Sesame CSM-1B | Free | 4.5GB | NO | YES | Clone from sample | Yes | 2-3min | CC | Not ranked | Yes |
| Zonos | Free | 6GB+ | NO | YES | Not stated | Yes | 5-30s | Apache 2.0 | Not ranked | Yes |
| Dia 1.6B/2B | Free | 7.4-10GB | NO | Marginal | Not stated | Yes | Seconds + transcript | Apache 2.0 | Not ranked | Yes |
| MaskGCT | Free | 16GB+ | NO | NO | Not stated | Not stated | Not stated | Not stated | Not ranked | Not stated |
| Orpheus 3B | Free | ~15GB | NO (full) | NO (full) | Not stated | Not stated | Not stated | Apache 2.0 | Not ranked | Not stated |

---

## LOCAL vs CLOUD SPLIT RECOMMENDATION (per source)

- **Bulk daily (20-30 tracks/month)**:
  - PRIMARY: Chatterbox Turbo locally on 8GB GPU. Cost: $0.
  - FALLBACK: Spark-TTS 0.5B (if Chatterbox unstable on 8GB).
  - BUDGET: Kokoro + British voice (no brand voice consistency).
- **Premium brand voice (2-4 tracks/month)**:
  - PRIMARY: ElevenLabs Creator ($22/mo) or Starter ($5/mo) with PVC.
  - ALTERNATIVE: Fish Audio API ($9.99/200 min) -- 70% cheaper than ElevenLabs.
- **Recommended split**: Chatterbox (bulk, free) + ElevenLabs Starter ($5/mo, premium only) = **$5/month total**.

---

## HARDWARE CONSTRAINTS

### What actually runs on RTX 3050 Ti 4GB (ATLAS actual hardware)

The source document assumes an **8GB GPU upgrade**. Against the actual 4GB RTX 3050 Ti:

| Model | Fits 4GB? | Confidence |
|-------|-----------|------------|
| Kokoro v1.0 (2-3GB) | YES | VERIFIED (2-3GB stated) |
| Spark-TTS 0.5B | MAYBE | UNCERTAIN (fits "8GB comfortably" -- 4GB not tested) |
| XTTS v2 | MAYBE | UNCERTAIN (VRAM not explicitly stated) |
| All others | NO | VERIFIED (all require 4.5GB+) |

**Conclusion on 4GB**: Only Kokoro is a confident fit. Kokoro has NO voice cloning. For voice cloning on 4GB, Spark-TTS is the best bet but unverified. All other cloning-capable models require 6GB+.

### What runs on 8GB (source's assumed hardware)

| Tier | Models | Notes |
|------|--------|-------|
| Comfortable (4-6GB) | Kokoro, Spark-TTS, Sesame CSM, StyleTTS2, F5-TTS, Zonos | All fit with headroom |
| Borderline (7-8GB) | Chatterbox Turbo, CosyVoice 0.5B | May need optimization, source hedges |
| Marginal (8-10GB) | Dia 1.6B/2B | 7.4GB base but peaks to 10GB |
| Not viable (12GB+) | Fish Speech/OpenAudio S1, MaskGCT, Orpheus 3B full | Require cloud or bigger GPU |

---

## COST ANALYSIS

- **Cheapest viable option**: Kokoro TTS -- $0, runs on 4GB, but NO voice cloning and NO Australian voices. British approximation only.
- **Cheapest with voice cloning (local)**: Chatterbox Turbo -- $0, but requires 8GB GPU. On 4GB, Spark-TTS at $0 is the gamble.
- **Cheapest cloud with cloning**: Fish Audio API -- $9.99/200 minutes.
- **Best quality option**: ElevenLabs Pro ($99/mo) with PVC, or Fish Audio API (#1 TTS-Arena).
- **Best value option (per source)**: Hybrid Chatterbox local ($0) + ElevenLabs Starter ($5/mo) = $5/month total.
- **Best value cloud-only**: Fish Audio API at $9.99-15/month (70% cheaper than ElevenLabs, #1 quality ranking).

### Monthly cost scenarios for Baby Brains (20-30 tracks + 2-4 premium)

| Approach | Monthly Cost | Notes |
|----------|-------------|-------|
| 100% ElevenLabs Creator | $22 | 100 min/mo, PVC clone |
| Hybrid: Chatterbox + ElevenLabs Starter | $5 | Source's top recommendation |
| Hybrid: Chatterbox + ElevenLabs (no plan, just Starter IVC) | $5-11 | Per source table |
| 100% Chatterbox local | $0 | Requires 8GB GPU |
| 100% Kokoro local | $0 | No cloning, British voices only |
| Fish Audio API only | $10-15 | 70% cheaper than EL, top quality |
| 100% ElevenLabs Pro | $99 | Overkill for this volume |

---

## KEY NUMBERS (Quick Reference)

- **Kokoro VRAM**: 2-3GB
- **Kokoro speed**: 36-210x real-time
- **Kokoro params**: 82M
- **Chatterbox vs ElevenLabs blind test**: 63.75% preferred Chatterbox [CLAIMED]
- **Chatterbox clone reference**: 5-10 seconds
- **Chatterbox VRAM**: ~8GB (Turbo 350M params)
- **ElevenLabs IVC minimum**: 10-30 seconds
- **ElevenLabs PVC minimum**: 30+ minutes recording
- **ElevenLabs Creator plan**: $22/mo, 100 min
- **ElevenLabs Starter plan**: $5/mo, 30 min
- **Fish Audio API**: $9.99/200 min -- 70% cheaper than ElevenLabs
- **CosyVoice similarity**: 77-78%
- **XTTS v2 similarity**: 85-95%
- **CosyVoice CER**: 0.81%
- **Fish Speech WER**: 0.008, CER: 0.004 (best in class)
- **F5-TTS RTF**: 0.15
- **CosyVoice streaming latency**: 150ms first packet
- **Open-source #1 on TTS-Arena**: Fish Speech/OpenAudio S1
- **Open-source #1 on HuggingFace downloads**: XTTS v2 (6.44M)
- **Baby Brains monthly volume**: 20-30 VO tracks (30-90s each) + 2-4 premium
- **Baby Brains monthly audio need**: ~15-45 minutes total

---

## CONTRADICTIONS & UNCERTAINTIES

1. **Hardware mismatch (CRITICAL)**: The source document assumes an 8GB VRAM GPU. ATLAS hardware spec (CLAUDE.md) lists RTX 3050 Ti 4GB. The entire "runs on your GPU" framing is based on 8GB. On 4GB, only Kokoro (no cloning) is confirmed viable. This is a **fundamental contradiction** between the research and the actual hardware.

2. **Chatterbox 63.75% claim**: The source states Chatterbox was "preferred over ElevenLabs in 63.75% of blind evaluations" but does not cite the specific study, sample size, test conditions, or which ElevenLabs model version was compared. [CLAIMED -- no source verification possible from this document]

3. **Chatterbox "borderline" on 8GB**: The source simultaneously recommends Chatterbox as the primary tool AND hedges with "if it runs stably on your 8GB card." This is internally uncertain. The Turbo variant (350M params) is described as "more efficient" but no specific VRAM number is given for Turbo alone.

4. **F5-TTS licensing**: Code is MIT but models are CC-BY-NC (non-commercial). The commercial alternative (OpenF5-TTS-Base, Apache 2.0) is "still alpha." This makes F5-TTS effectively non-commercial for Baby Brains despite being listed as viable. [VERIFIED contradiction for commercial use]

5. **Fish Speech ranking discrepancy**: Described as "#1 on TTS-Arena" in the tool description, but the TTS-Arena leaderboard table shows Vocu V3.0 at #1. Fish Speech / OpenAudio S1 is not listed in the Arena table at all. These may be different Arena versions or the claim may be outdated. [CONTRADICTED within source]

6. **ElevenLabs plan recommendation inconsistency**: First recommends Creator ($22/mo) as "adequate headroom," then later recommends Starter ($5/mo) in the hybrid setup. Both are valid for different scenarios but the shift is not explicitly reconciled.

7. **Spark-TTS VRAM**: Described as "comfortably fits 8GB" but no exact GB figure given. RTF ~1.0 on RTX 2070 suggests moderate resource use but 4GB viability is completely unknown.

8. **XTTS v2 VRAM**: No explicit VRAM figure given anywhere in the source. Listed as "comfortable fit" on 8GB in the cloning comparison table. Cannot verify 4GB viability.

9. **CosyVoice version confusion**: Header says "CosyVoice 0.5B / Fun-CosyVoice 3.0" but TTS-Arena table lists "CosyVoice 2.0" at #25. Unclear if these are the same or different releases.

10. **Chatterbox processing speed**: Stated as "~2-5 seconds per 60s clip" in the architecture diagram but no benchmark citation. On an 8GB borderline GPU, actual speed could be slower due to memory pressure.

11. **"No Australian accent natively supported by any open-source model"**: This is stated in the conclusion. If true, ALL open-source Australian voice quality depends entirely on zero-shot cloning fidelity, which varies significantly by model. No blind test data is provided for Australian accent cloning specifically.

12. **Fish Audio API pricing ambiguity**: Listed as "$9.99/200 min or $15/1M chars" -- these are two different pricing models and it is unclear which applies when, or if they are different tiers.

---

## SOURCE URLS

No external URLs are provided in the source document. All claims are unsourced within the text. The following are identifiable external references that could be verified:

- HuggingFace TTS-Arena V2 leaderboard (February 2026)
- HuggingFace model pages: coqui/XTTS-v2, hexgrad/Kokoro-82M, ResembleAI/chatterbox, microsoft/VibeVoice-1.5B
- ElevenLabs pricing page (February 2026)
- Fish Audio API pricing
- Resemble AI Chatterbox blind test study (uncited)
- Apache 2.0, MIT, CC-BY-NC, CPML license texts
- `pip install chatterbox-tts` package

**No URLs were embedded in the source document.**
