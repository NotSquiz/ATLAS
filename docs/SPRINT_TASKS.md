# Baby Brains Automation - Sprint Tasks

**Plan:** docs/BB_AUTOMATION_PLAN_V2.md (or .claude/plans/cuddly-watching-eagle.md)
**Start Date:** January 30, 2026
**Machine:** Laptop (build here, push to git, desktop pulls)

---

## How to Resume Any Session

```
Read these files first:
1. .claude/handoff.md (current state)
2. docs/SPRINT_TASKS.md (this file -- find next PENDING task)
3. docs/BB_AUTOMATION_PLAN_V2.md (architecture reference)

Then: Pick the next PENDING task with no blocked dependencies. Build it.
After: Mark task DONE, update handoff.md, commit + push.
```

---

## Week 1: Foundation + Warming MVP

### S1.1: Schema + Models + DB Init
- **Status:** DONE
- **Prerequisites:** None
- **Read First:** docs/BB_AUTOMATION_PLAN_V2.md (Database Schema section), atlas/memory/schema.sql (existing pattern), atlas/memory/store.py (existing DB init pattern)
- **Build:**
  - `atlas/babybrains/__init__.py`
  - `atlas/babybrains/schema.sql` (10 tables: bb_accounts, bb_warming_targets, bb_warming_actions, bb_engagement_log, bb_trends, bb_content_briefs, bb_scripts, bb_visual_assets, bb_exports, bb_cross_repo_index)
  - `atlas/babybrains/models.py` (dataclasses for each table)
  - `atlas/babybrains/db.py` (init_bb_tables, query helpers)
  - `tests/babybrains/__init__.py`
  - `tests/babybrains/conftest.py`
  - `tests/babybrains/test_db.py`
- **Test:** `pytest tests/babybrains/test_db.py`
- **Acceptance:** 10 tables created in test DB, models importable, db.init_bb_tables() idempotent
- **Update After:** Mark DONE, update handoff.md

### S1.2: Voice Spec Loader + Human Story Profile
- **Status:** DONE
- **Prerequisites:** None (can parallel with S1.1)
- **Read First:** /home/squiz/code/web/.claude/agents/BabyBrains-Writer.md (1712 lines), docs/BB_AUTOMATION_PLAN_V2.md (D103 section)
- **Build:**
  - `atlas/babybrains/voice_spec.py` (load voice spec, extract sections by heading, return relevant context for comment/script generation)
  - `config/babybrains/human_story.json` (the human story profile from D103)
  - `tests/babybrains/test_voice_spec.py`
- **Test:** `pytest tests/babybrains/test_voice_spec.py`
- **Acceptance:** Can load voice spec, extract "Comment Generation Rules" section, load human story profile
- **Update After:** Mark DONE, update handoff.md

### S1.3: Cross-Repo Path Map
- **Status:** DONE
- **Prerequisites:** None (can parallel with S1.1)
- **Read First:** docs/BB_AUTOMATION_PLAN_V2.md (D104 Cross-Repo Knowledge Map)
- **Build:**
  - `atlas/babybrains/cross_repo.py` (search function using static path map)
  - `config/babybrains/cross_repo_paths.json` (topic -> file path mappings across 5 active repos)
- **Test:** Manual test: cross_repo.search("warming strategy") returns relevant paths
- **Acceptance:** bb_find_doc("platform strategy") returns paths to PLATFORM-PLAYBOOKS.md and Dec 2025 research
- **Update After:** Mark DONE, update handoff.md

### S1.4: Platform + Warming Configs
- **Status:** DONE
- **Prerequisites:** None (can parallel with S1.1)
- **Read First:** /home/squiz/code/babybrains-os/docs/research/youtube-dec-2025.md, instagram-dec-2025.md, tiktok-dec-2025.md, /home/squiz/code/babybrains-os/docs/PLATFORM-PLAYBOOKS.md, docs/BB_AUTOMATION_PLAN_V2.md (D105)
- **Build:**
  - `config/babybrains/platforms.json` (platform rules extracted from Dec 2025 research: posting times, hashtag limits, caption lengths, algo signals per platform)
  - `config/babybrains/warming_schedule.json` (daily targets per platform, warming phases)
  - `config/babybrains/warming_engagement_rules.json` (watch time thresholds, like/subscribe criteria)
  - `config/babybrains/audience_segments.json` (5 personas from AUDIENCE-SEGMENTATION.md)
  - `config/babybrains/competitors.json` (competitor accounts to monitor)
- **Test:** JSON files load without error, schema validates
- **Acceptance:** All configs loadable, contain data from research docs
- **Update After:** Mark DONE, update handoff.md

### S1.5: bb_status + bb_find_doc MCP Tools
- **Status:** DONE
- **Prerequisites:** S1.1 (schema), S1.3 (cross_repo)
- **Read First:** atlas/mcp/server.py (existing @mcp.tool() pattern), docs/BB_AUTOMATION_PLAN_V2.md (MCP Tools section)
- **Build:**
  - Add `bb_status()` tool to atlas/mcp/server.py
  - Add `bb_find_doc(topic)` tool to atlas/mcp/server.py
  - `atlas/babybrains/cli.py` (basic CLI: `python -m atlas.babybrains.cli status`)
- **Test:** MCP tools callable from Claude Code, CLI runs
- **Acceptance:** `bb_status` returns dashboard data, `bb_find_doc` searches cross-repo
- **Update After:** Mark DONE, update handoff.md

### S1.6: Transcript Fetcher
- **Status:** DONE
- **Prerequisites:** None (can parallel)
- **Read First:** Check youtube-transcript-api is installed (pip show youtube-transcript-api)
- **Build:**
  - `atlas/babybrains/warming/transcript.py` (fetch YouTube transcripts, handle errors gracefully, fallback to title+description if transcript unavailable)
  - `tests/babybrains/test_transcript.py` (test with 5 known parenting video IDs)
- **Test:** `pytest tests/babybrains/test_transcript.py`
- **Acceptance:** Transcripts fetched for at least 15/20 test videos, graceful fallback for failures
- **Update After:** Mark DONE, update handoff.md

### S1.7: Comment Draft Generator
- **Status:** DONE
- **Prerequisites:** S1.2 (voice spec), S1.6 (transcripts)
- **Read First:** docs/BB_AUTOMATION_PLAN_V2.md (D103 -- all 3 layers), atlas/nutrition/usda_client.py (API client pattern)
- **Build:**
  - `atlas/babybrains/warming/comments.py` (CommentGenerator class: takes transcript + voice spec + human story + optional knowledge context, calls Sonnet API, validates output against voice spec rules, returns comment draft)
  - `tests/babybrains/test_comments.py`
- **Test:** `pytest tests/babybrains/test_comments.py` + generate 5 real comments and manually review quality
- **Acceptance:** Comments pass quality gate (no em-dashes, AU English, appropriate length, transcript-specific)
- **Update After:** Mark DONE, update handoff.md

### S1.8: WarmingService + bb_warming_daily MCP Tool
- **Status:** DONE
- **Prerequisites:** S1.1 (schema), S1.6 (transcripts), S1.7 (comments)
- **Read First:** docs/BB_AUTOMATION_PLAN_V2.md (D102 pipeline), atlas/mcp/server.py
- **Build:**
  - `atlas/babybrains/warming/__init__.py`
  - `atlas/babybrains/warming/service.py` (WarmingService: orchestrate daily targets, generate comments)
  - `atlas/babybrains/warming/targets.py` (target generation from manual list initially, API-driven later)
  - Add `bb_warming_daily(platform?)` MCP tool to server.py
  - Add `bb_warming_done(platform, actions)` MCP tool to server.py
  - Add warming commands to CLI
- **Test:** `pytest tests/babybrains/` full suite + manual test via Claude Code
- **Acceptance:** **WEEK 1 GATE: Type `bb warming daily` in Claude Code, see targets with transcript-aware BB-voice comments**
- **Update After:** Mark DONE, update handoff.md, commit + push, celebrate

---

## Week 2: Browser Automation + Trend Engine

### S2.1: WSLg / Playwright Spike Test
- **Status:** PENDING
- **Prerequisites:** None (DO THIS FIRST in Week 2)
- **Read First:** N/A
- **Build:**
  - Install playwright: `pip install playwright && playwright install chromium`
  - Install WSL2 browser deps: `sudo apt install libgtk-3-dev libnss3 libxss1 libasound2`
  - Test headed Chrome: `python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); b = p.chromium.launch(headless=False); page = b.new_page(); page.goto('https://youtube.com'); import time; time.sleep(5); b.close(); p.stop()"`
- **Test:** Chrome window opens showing YouTube
- **Acceptance:** Headed Chrome works on WSL2 OR fallback plan documented
- **Update After:** Mark DONE with result (WORKS / FALLBACK NEEDED)

### S2.2: Browser Automation (Watch + Like + Subscribe)
- **Status:** PENDING
- **Prerequisites:** S2.1 (WSLg confirmed)
- **Build:**
  - `atlas/babybrains/warming/browser.py` (WarmingBrowser class: open video, watch for N seconds with random variance, like, subscribe, circuit breaker)
  - `tests/babybrains/test_browser.py` (mock tests + 1 real integration test)
- **Acceptance:** Browser watches a video, likes it, returns cleanly

### S2.3: bb_warming_watch + bb_warming_done MCP Tools
- **Status:** PENDING
- **Prerequisites:** S2.2 (browser)
- **Build:**
  - Add `bb_warming_watch(platform?)` MCP tool
  - Enhance `bb_warming_done(platform, actions)` with action logging
  - Add `bb_warming_status()` MCP tool
- **Acceptance:** Full warming workflow: generate targets -> watch -> human posts comments -> log done

### S2.4: YouTube Data API Client
- **Status:** PENDING
- **Prerequisites:** S1.1 (schema)
- **Build:**
  - `atlas/babybrains/clients/youtube_client.py` (search, fetch captions, channel info)
  - `tests/babybrains/test_youtube_client.py`
- **Acceptance:** Search returns parenting videos, captions fetchable

### S2.5: Grok API Client
- **Status:** PENDING
- **Prerequisites:** S1.1 (schema)
- **Build:**
  - `atlas/babybrains/clients/grok_client.py` (X.com trending search)
  - `tests/babybrains/test_grok_client.py`
- **Acceptance:** Grok returns trending parenting topics from X.com

### S2.6: Trend Engine + bb_trend_scan MCP Tool
- **Status:** PENDING
- **Prerequisites:** S2.4, S2.5
- **Build:**
  - `atlas/babybrains/trends/engine.py`
  - `atlas/babybrains/trends/aggregator.py`
  - `atlas/babybrains/trends/scorer.py`
  - Add `bb_trend_scan(force?)` MCP tool
- **Acceptance:** **WEEK 2 GATE: `bb trend scan` returns scored, deduplicated trends from YouTube + Grok**

---

## Week 3: Content Pipeline + Polish

### S3.1: Brief Generator + MCP Tool
- **Status:** PENDING
- **Prerequisites:** S1.1, S1.2
- **Build:**
  - `atlas/babybrains/content/brief_generator.py`
  - Add `bb_content_brief(topic, trend_id?)` MCP tool
- **Acceptance:** Brief generated with hooks, evidence refs, visual concepts

### S3.2: Script Generator + MCP Tool
- **Status:** PENDING
- **Prerequisites:** S3.1, S1.2
- **Build:**
  - `atlas/babybrains/content/script_generator.py` (21s: 55-65 words, 60s: 160-185 words)
  - Add `bb_generate_script(brief_id, fmt)` MCP tool
- **Acceptance:** Scripts pass voice spec validation, correct word counts

### S3.3: Visual Prompt Generator + MCP Tool
- **Status:** PENDING
- **Prerequisites:** S3.2
- **Build:**
  - `atlas/babybrains/content/visual_generator.py`
  - Add `bb_generate_visuals(script_id)` MCP tool
- **Acceptance:** MidJourney/Kling prompts extractable from script

### S3.4: Caption + Export Pipeline + MCP Tools
- **Status:** PENDING
- **Prerequisites:** S3.2, S1.4 (platform configs)
- **Build:**
  - `atlas/babybrains/content/caption_generator.py`
  - `atlas/babybrains/content/exporter.py`
  - Add `bb_export_platform(script_id, platform)` MCP tool
- **Acceptance:** Platform-specific exports with correct caption lengths, hashtag counts

### S3.5: Review Queue + Calendar + Management MCP Tools
- **Status:** PENDING
- **Prerequisites:** S1.1 (schema)
- **Build:**
  - Add `bb_review_queue()`, `bb_calendar(days?)`, `bb_review_item(type, id, action)` MCP tools
- **Acceptance:** Review workflow functional

### S3.6: Scheduler Integration
- **Status:** PENDING
- **Prerequisites:** S1.8, S2.6 (services to schedule)
- **Build:**
  - Add 6 BB scheduled tasks to atlas/scheduler/loop.py
  - Add async task support to scheduler (existing tasks are sync)
  - Add dotenv loading for cron environment
- **Acceptance:** `python -m atlas.scheduler.loop --once bb_morning_prep` executes correctly

### S3.7: Integration Test + Docs Update + Handoff
- **Status:** PENDING
- **Prerequisites:** All previous tasks
- **Build:**
  - Full E2E integration test
  - Update CLAUDE.md with BB module docs
  - Update .claude/handoff.md with build status
  - Update docs/BB_AUTOMATION_PLAN_V2.md with any changes
  - Ensure all new files committed + pushed
- **Acceptance:** **WEEK 3 GATE: Full E2E test passes, all docs updated, git pushed, desktop can pull and run**

---

## Git Workflow (2-Machine Sync)

```bash
# After completing each task on LAPTOP:
git add atlas/babybrains/ config/babybrains/ tests/babybrains/ docs/SPRINT_TASKS.md .claude/handoff.md
git commit -m "S1.1: Schema + Models + DB Init"
git push origin master

# On DESKTOP (before running):
git pull origin master
# Install any new deps:
pip install -r requirements.txt  # or pip install playwright etc.
```

All state lives in git. No local-only files except .env (which must be manually copied to desktop).
