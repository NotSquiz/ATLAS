# ATLAS Session Handoff

**Date:** January 26, 2026
**Status:** Strategic Research Complete — ATLAS 3.0 Planning

---

## What Was Accomplished This Session

### Personal AI Landscape Research (Comprehensive)

Deep analysis of the personal AI assistant ecosystem in January 2026:

**Key Discoveries:**
1. **Clawdbot** — 9.7k GitHub stars, viral adoption, self-hosted AI assistant
2. **Claude Skills Marketplace** — 71,000+ skills, but security concerns (ransomware demonstrated)
3. **Levangie Labs/BlevLabs** — Cognitive Agentic Framework with episodic memory
4. **Brian Roemmele's Love Equation** — `dE/dt = β(C-D)E` for AI alignment
5. **/last30days skill** — Trend research across Reddit/X
6. **WooYun Legacy** — 88,636 vulnerability cases as Claude skill

**Strategic Conclusion:** Don't adopt Clawdbot — evolve ATLAS with Clawdbot's best patterns while preserving unique strengths (voice-first, health tracking, Baby Brains pipeline).

---

## Documents Created

| Document | Purpose |
|----------|---------|
| `docs/research/R31.Personal AI Assistant Landscape January 2026 - Clawdbot Era.md` | **Comprehensive research document** — Clawdbot analysis, competitive landscape, Love Equation, security architecture, ATLAS 3.0 strategy, 90-day roadmap |
| `.claude/plans/transient-rolling-hamming.md` | Active strategic plan with implementation details |
| `docs/Clawdbot Trend Analysis - Comprehensive .md` | Raw Clawdbot trend data (5,620 posts analyzed) |

---

## ATLAS 3.0 Vision

A 24/7 AI partner that:
1. **Manages health** (current strength)
2. **Runs Baby Brains** as business workforce
3. **Handles life admin** (email, calendar, tasks)
4. **Is reachable anywhere** (voice, Telegram, email)
5. **Improves itself** over time

### Architecture Summary

```
Voice Bridge (current) + Messaging Bridge (new) + Daemon Mode (new)
                              ↓
                    Intent Dispatcher (unified)
                              ↓
         Health Services | Baby Brains Workforce | Life Admin
                              ↓
                    Model Router (multi-model)
                              ↓
                    Persistent Memory
```

---

## Implementation Phases (Not Started)

| Phase | Description | Duration |
|-------|-------------|----------|
| 1 | Telegram bridge | 1-2 weeks |
| 2 | Daemon mode + Ralph loop | 1-2 weeks |
| 3 | Model router | 1 week |
| 4 | Self-improvement layer | 2-3 weeks |
| 5 | Life admin (email, calendar) | 2-3 weeks |

---

## Key Concepts to Remember

### Love Equation (Brian Roemmele)
```
dE/dt = β(C - D)E
```
- E = emotional complexity / "love" level
- C = cooperative interactions, D = defective/toxic
- If C > D: Love grows exponentially
- **Application:** Design ATLAS interactions as relationship, not transaction. Store positive memories. Proactive care.

### Security Architecture
- Clawdbot/Skills ecosystem has real attack vectors (MedusaLocker demonstrated)
- Use OS-level sandboxing (bubblewrap/Docker)
- Deny rules for curl, fetch, .env
- Whitelist-only skill installation
- Monthly audits

### ATLAS Advantages (Don't Lose)
- Voice-first <1.8s latency
- 0-token intent matching (95%+ local)
- Traffic Light + GATE system
- Baby Brains quality pipeline
- Ethical gamification

---

## How to Resume

```
Read these files:
1. .claude/handoff.md (this file)
2. docs/research/R31.Personal AI Assistant Landscape January 2026 - Clawdbot Era.md

Then:
- For implementation: Start with Phase 1 (Telegram bridge)
- For more research: User has more X.com discoveries to share
- For Baby Brains focus: Activity pipeline automation via Ralph loop
```

---

## Quick Reference: Key External Resources

| Resource | URL | Purpose |
|----------|-----|---------|
| Clawdbot | https://github.com/clawdbot/clawdbot | Reference architecture |
| /last30days | https://github.com/mvanhorn/last30days-skill | Trend research for Baby Brains |
| WooYun Security | https://github.com/tanweai/wooyun-legacy | Security auditing skill |
| Claude Sandboxing | https://code.claude.com/docs/en/sandboxing | Security implementation |
| Levangie Labs | https://levangielabs.com/ | Cognitive architecture reference |

---

## User Context

**Goal:** Build AI system that acts as life assistant and business partner for Baby Brains.

**Stakes:** User explicitly stated this is about providing a better life for their family. The personal AI assistant opportunity is seen as critical path to financial improvement.

**Baby Brains:** Evidence-based Montessori parenting platform with:
- Knowledge repo (175+ activities to convert)
- Web platform (pre-launch)
- Marketing OS (content generation)

---

## This Session: Qwen3-TTS Voice Cloning (January 26, 2026)

### What Was Done
1. **Qwen3-TTS Installation** - Installed qwen-tts, flash-attn, openai-whisper, ffmpeg
2. **Voice Cloning Testing** - Tested multiple voices:
   - **Jeremy Irons** (interview audio) - WORKS WELL, adopted as default
   - **Thomas Shelby/Cillian Murphy** (TV audio) - FAILED, TV audio too processed
3. **Module Integration** - Fixed `atlas/voice/tts_qwen.py`:
   - Changed from CustomVoice to Base model (ICL mode)
   - Added correct API calls (`generate_voice_clone` with `ref_text`)
   - Added x-vector fallback mode
4. **Bridge Integration** - Updated `atlas/voice/bridge_file_server.py`:
   - Default voice changed to `jeremy_irons`
   - Removed thomas_shelby from QWEN_VOICES (didn't work)
5. **Documentation** - Updated CLAUDE.md, V2_ORCHESTRATOR_GUIDE.md, DECISIONS.md

### Key Files
| File | Purpose |
|------|---------|
| `config/voice/jeremy_irons.wav` | Reference audio (11 seconds) |
| `config/voice/qwen_tts_voices.json` | Voice cloning config |
| `atlas/voice/tts_qwen.py` | Qwen3TTS wrapper |
| `atlas/voice/bridge_file_server.py` | Voice bridge (uses Qwen3TTS) |

### Voice Cloning Learnings
- Clean interview/podcast audio works best
- TV/film dialogue fails (reverb, EQ, background score)
- Regional accents (Birmingham) harder than RP British
- Transcription accuracy critical for ICL mode
- Punctuation controls pacing (commas, ellipses)

### Testing the Voice
```bash
# Start voice bridge
cd /home/squiz/ATLAS && source venv/bin/activate
python -m atlas.voice.bridge_file_server

# First response will be slow (~30s) as model loads
# Subsequent responses faster
```

---

## Previous Session Work (Preserved)

### UI & Voice Pipeline
- Tab order fixed, HUD gauge sizes increased
- Visual workout display in main zone
- Seneca Trial protocol (Full/Quick modes)
- Combat level formula: `(skill_sum // 2) + 3`

### Pending
- White background on Focus/Learning icons (need GIMP fix)
- Combat level display in HUD
- XP balancing values
- Test voice bridge with Qwen3-TTS live

---

*Session ended: January 26, 2026*
*Qwen3-TTS integration complete, ready for live testing*
