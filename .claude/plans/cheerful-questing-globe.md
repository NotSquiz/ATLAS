# Baby Brains Migration: ATLAS to babybrains-os

## Summary

Move BB documentation and (eventually) runtime code from ATLAS into the babybrains-os repo. BB code has **zero ATLAS dependencies** — it only imports stdlib, anthropic, youtube_transcript_api, and its own modules. The 10-table BB schema has no foreign keys to ATLAS tables. Extraction is clean.

**This session:** Phase 1 (move docs). Phase 2-3 are plan-only.

---

## Phase 1: Move BB Docs (THIS SESSION)

### What Moves

| ATLAS Source | babybrains-os Destination |
|---|---|
| `docs/BB_AUTOMATION_PLAN_V2.md` (38KB) | `docs/automation/BB_AUTOMATION_PLAN_V2.md` |
| `docs/SPRINT_TASKS.md` (15KB) | `docs/automation/SPRINT_TASKS.md` |
| `docs/BROWSER_STEALTH_RESEARCH.md` (16KB) | `docs/automation/BROWSER_STEALTH_RESEARCH.md` |
| `docs/BABY-BRAINS-LAUNCH-STRATEGY-JAN2026.md` (21KB) | `docs/automation/LAUNCH-STRATEGY-JAN2026.md` |

**Destination rationale:** `docs/automation/` because babybrains-os already has `docs/` with strategy docs and `docs/research/` and `docs/strategic-review/`. The automation pipeline docs are a distinct concern — operational build docs, not strategy or research.

### Steps

1. **Create `docs/automation/` in babybrains-os**
   ```bash
   mkdir -p /home/squiz/code/babybrains-os/docs/automation
   ```

2. **Copy 4 docs** (copy first, then we'll update references)
   ```bash
   cp /home/squiz/ATLAS/docs/BB_AUTOMATION_PLAN_V2.md /home/squiz/code/babybrains-os/docs/automation/
   cp /home/squiz/ATLAS/docs/SPRINT_TASKS.md /home/squiz/code/babybrains-os/docs/automation/
   cp /home/squiz/ATLAS/docs/BROWSER_STEALTH_RESEARCH.md /home/squiz/code/babybrains-os/docs/automation/
   cp /home/squiz/ATLAS/docs/BABY-BRAINS-LAUNCH-STRATEGY-JAN2026.md /home/squiz/code/babybrains-os/docs/automation/LAUNCH-STRATEGY-JAN2026.md
   ```

3. **Update internal cross-references in moved docs**

   In `SPRINT_TASKS.md`:
   - `docs/BB_AUTOMATION_PLAN_V2.md` → `BB_AUTOMATION_PLAN_V2.md` (same directory, ~12 refs)
   - `docs/BROWSER_STEALTH_RESEARCH.md` → `BROWSER_STEALTH_RESEARCH.md` (~3 refs)
   - **[AUDIT FIX]** Remove dead reference to `.claude/plans/cuddly-watching-eagle.md` (line 3, file doesn't exist)
   - **[AUDIT FIX]** Add `[ATLAS repo]` label to ALL ~15 ATLAS-local paths (atlas/mcp/server.py, atlas/memory/schema.sql, atlas/memory/store.py, atlas/nutrition/usda_client.py, .claude/handoff.md, tests/babybrains/, etc.)

   In `BB_AUTOMATION_PLAN_V2.md`:
   - `docs/BROWSER_STEALTH_RESEARCH.md` → `BROWSER_STEALTH_RESEARCH.md` (~2 refs)
   - `docs/SPRINT_TASKS.md` → `SPRINT_TASKS.md` (line 552 has `docs/` prefix)
   - `docs/BABY-BRAINS-LAUNCH-STRATEGY-JAN2026.md` → `LAUNCH-STRATEGY-JAN2026.md` (~1 ref)
   - **[AUDIT FIX]** `docs/BB_AUTOMATION_PLAN_V2.md` self-reference (line 545) → `BB_AUTOMATION_PLAN_V2.md`
   - **[AUDIT FIX]** Update repo tree diagram (~line 219) to show launch strategy under babybrains-os, not ATLAS

4. **Replace ATLAS originals with stub redirects** (NOT symlinks)
   Each moved doc becomes a short markdown pointer:
   ```markdown
   # MOVED to babybrains-os

   This document now lives in the babybrains-os repository:
   **Path:** /home/squiz/code/babybrains-os/docs/automation/<filename>

   Moved: 2026-01-31 | Reason: BB docs belong in BB repo
   ```

5. **Update ATLAS cross-references**
   - `.claude/handoff.md` — Update "How to Resume" to point to babybrains-os absolute paths (not stubs). Update "Files Modified" section.
   - `docs/DOCUMENTATION_UPDATE_GUIDE.md` — Update BB doc references table
   - `docs/TECHNICAL_STATUS.md` (lines 1306-1307) — **[AUDIT FIX]** Update "How to Resume" instructions that reference BB docs to point to babybrains-os paths
   - `config/babybrains/cross_repo_paths.json` — Change 2 entries from `"repo": "ATLAS"` to `"repo": "babybrains-os"` with updated paths:
     - "launch strategy" → `docs/automation/LAUNCH-STRATEGY-JAN2026.md`
     - "warming strategy" → `docs/automation/BB_AUTOMATION_PLAN_V2.md`

6. **Update babybrains-os README.md** — Add "Automation Pipeline" section

7. **Commit in babybrains-os:**
   ```
   Move BB automation docs from ATLAS repo

   - docs/automation/BB_AUTOMATION_PLAN_V2.md (sprint architecture)
   - docs/automation/SPRINT_TASKS.md (task tracking)
   - docs/automation/BROWSER_STEALTH_RESEARCH.md (anti-detection)
   - docs/automation/LAUNCH-STRATEGY-JAN2026.md (launch plan)
   ```

8. **Commit in ATLAS:**
   ```
   Replace BB docs with stubs pointing to babybrains-os

   BB docs moved to /home/squiz/code/babybrains-os/docs/automation/
   Updated cross_repo_paths.json, handoff.md, DOCUMENTATION_UPDATE_GUIDE.md
   ```

9. **Push both repos**

### Verification

- `pytest tests/babybrains/` in ATLAS — still 98 tests pass (docs don't affect code)
- `grep -r "docs/BB_AUTOMATION\|docs/SPRINT_TASKS\|docs/BROWSER_STEALTH\|docs/BABY-BRAINS-LAUNCH" /home/squiz/ATLAS/ --include="*.py" --include="*.json"` — returns only stubs and updated cross_repo_paths.json
- `python -m atlas.babybrains.cli find-doc "warming strategy"` — returns babybrains-os path
- All 4 docs exist and are readable in babybrains-os

### Rollback

- ATLAS: `git checkout HEAD~1 -- docs/BB_AUTOMATION_PLAN_V2.md docs/SPRINT_TASKS.md docs/BROWSER_STEALTH_RESEARCH.md docs/BABY-BRAINS-LAUNCH-STRATEGY-JAN2026.md`
- babybrains-os: `git revert HEAD`

---

## Phase 2: Extract BB Runtime Code (FUTURE SESSION)

### Architecture Decision: pip-installable package with editable install

**Recommendation:** `pip install -e /home/squiz/code/babybrains-os`

| Option | Verdict | Why |
|---|---|---|
| **pip install -e (editable)** | **RECOMMENDED** | Standard Python, IDE support, proper namespace, works on both machines |
| sys.path manipulation | No | Fragile, breaks linting, anti-pattern |
| git submodule | No | Complexity nightmare for 1 developer, breaks Claude Code |
| Standalone with own MCP | Phase 3 | Premature; adds IPC overhead, two servers to manage |

### Target Package Structure

```
babybrains-os/
├── pyproject.toml              (NEW)
├── src/                        (NEW — src layout)
│   └── babybrains/             (moved from ATLAS atlas/babybrains/)
│       ├── __init__.py         (add REPO_ROOT, CONFIG_DIR)
│       ├── __main__.py
│       ├── schema.sql
│       ├── models.py
│       ├── db.py               (update default DB path)
│       ├── cli.py
│       ├── voice_spec.py       (fix hardcoded path → env var)
│       ├── cross_repo.py       (fix config path traversal)
│       ├── warming/
│       │   ├── service.py
│       │   ├── targets.py      (fix config path traversal)
│       │   ├── comments.py
│       │   └── transcript.py
│       ├── trends/, content/, clients/  (stubs)
│
├── config/                     (existing + merge from ATLAS)
│   ├── flags.yaml, paths.yaml  (existing)
│   ├── platforms.json           (from ATLAS config/babybrains/)
│   ├── warming_schedule.json
│   ├── warming_engagement_rules.json
│   ├── audience_segments.json
│   ├── competitors.json
│   ├── cross_repo_paths.json
│   └── human_story.json
│
├── tests/                      (existing + merge from ATLAS)
│   ├── conftest.py, test_db.py, test_voice_spec.py, etc.  (from ATLAS tests/babybrains/)
│   ├── scripts/, skills/, traceability/  (existing)
│
├── skills/, schemas/, qc/, docs/, marketing/  (all existing, unchanged)
```

### Key Code Changes Required

1. **All imports**: `atlas.babybrains.X` → `babybrains.X` (15 files, mechanical find/replace)

2. **Config path resolution** — Add to `src/babybrains/__init__.py`:
   ```python
   import os
   from pathlib import Path

   REPO_ROOT = Path(os.environ.get(
       "BABYBRAINS_REPO",
       str(Path(__file__).resolve().parent.parent.parent)
   ))
   CONFIG_DIR = REPO_ROOT / "config"
   ```

3. **Hardcoded paths**:
   - `voice_spec.py:16` — Change to `os.environ.get("BB_VOICE_SPEC_PATH", "/home/squiz/code/web/.claude/agents/BabyBrains-Writer.md")`
   - `voice_spec.py:19` — Change to `from babybrains import CONFIG_DIR; CONFIG_DIR / "human_story.json"`
   - `targets.py:17-18` — Change to use `CONFIG_DIR` instead of `__file__` traversal
   - `cross_repo.py:16` — Change to use `CONFIG_DIR`

4. **Database path** — `db.py:64` changes default from `~/.atlas/atlas.db` to:
   ```python
   db_path = Path(os.environ.get("BB_DB_PATH", str(Path.home() / ".babybrains" / "babybrains.db")))
   ```

5. **ATLAS MCP server** (`atlas/mcp/server.py:852-1023`) — Change imports:
   ```python
   # from atlas.babybrains import db as bb_db
   from babybrains import db as bb_db  # pip-installed package
   ```

6. **Data migration** — One-time script to copy BB tables from `~/.atlas/atlas.db` to `~/.babybrains/babybrains.db`

7. **ATLAS cleanup** — Delete `atlas/babybrains/`, `config/babybrains/`, `tests/babybrains/`. Delete stub files from `docs/`. Add `babybrains` to ATLAS requirements. **[AUDIT FIX: include stub cleanup]**

### Installation on Each Machine

```bash
cd /home/squiz/code/babybrains-os
pip install -e ".[dev]"
python -c "from babybrains.models import BBAccount; print('OK')"
```

---

## Phase 3: Independent BB MCP Server (FUTURE)

Create `src/babybrains/mcp_server.py` with all 5 BB tools. Remove BB tools from ATLAS MCP server. Configure Claude Code with dual MCP servers:

```json
{
  "mcpServers": {
    "atlas": {"command": "python", "args": ["-m", "atlas.mcp.server"]},
    "babybrains": {"command": "python", "args": ["-m", "babybrains.mcp_server"]}
  }
}
```

---

## "Wait" Pattern Audit

**Assumption 1: BB code is truly independent of ATLAS**
- Verified: All imports are within `atlas.babybrains.*` namespace. The db.py docstring says "Uses ATLAS MemoryStore connection" but the code just takes any sqlite3 connection. No actual ATLAS dependency.
- Risk: The test conftest.py creates a `semantic_memory` table stub — defensive only, not functional.

**Assumption 2: pip editable install works across machine sync**
- Risk: If user forgets `pip install -e` on desktop, MCP tools fail with ImportError.
- Mitigation: Lazy imports in MCP server already return `{"status": "error"}`. Add to handoff checklist.

**Assumption 3: Moving docs won't disrupt Sprint 2 work**
- Mitigation: Phase 1 is atomic — all moves + all reference updates in one session.

**Assumption 4: babybrains-os config/ can absorb BB JSON configs**
- Verified: Existing config/ only has flags.yaml and paths.yaml. BB JSON files use different naming. No conflict.

**Assumption 5: No circular dependencies after extraction**
- Verified: BB never imports ATLAS. ATLAS imports BB (via MCP tools only). One-way dependency.

---

## Verification Audit Results (3 prompts applied)

**Inversion Test:** WARN — Found `docs/TECHNICAL_STATUS.md` (lines 1306-1307) missing from update list. Fixed above.
**Adversarial Self-Check:** WARN — `handoff.md` should point to babybrains-os absolute paths not stubs. CLAUDE.md has no BB doc refs (PASS). `bb_find_doc` path resolution verified working after JSON update (PASS).
**"Wait" Pattern:** WARN — SPRINT_TASKS.md has ~15 ATLAS-local paths needing labels (underspecified). Dead reference to non-existent plan file. Phase 2 needed stub cleanup step. All fixed above.

**Must-fix (1):** TECHNICAL_STATUS.md → added to Step 5
**Should-fix (5):** All incorporated into Steps 3 and 5

---

## Files Modified (Phase 1 Only)

### In babybrains-os (create/add):
- `docs/automation/BB_AUTOMATION_PLAN_V2.md` (new)
- `docs/automation/SPRINT_TASKS.md` (new)
- `docs/automation/BROWSER_STEALTH_RESEARCH.md` (new)
- `docs/automation/LAUNCH-STRATEGY-JAN2026.md` (new)
- `README.md` (update — add automation section)

### In ATLAS (modify):
- `docs/BB_AUTOMATION_PLAN_V2.md` (replace with stub)
- `docs/SPRINT_TASKS.md` (replace with stub)
- `docs/BROWSER_STEALTH_RESEARCH.md` (replace with stub)
- `docs/BABY-BRAINS-LAUNCH-STRATEGY-JAN2026.md` (replace with stub)
- `.claude/handoff.md` (update paths to babybrains-os absolute paths)
- `docs/DOCUMENTATION_UPDATE_GUIDE.md` (update BB doc references)
- `docs/TECHNICAL_STATUS.md` (update lines 1306-1307) **[AUDIT FIX]**
- `config/babybrains/cross_repo_paths.json` (update 2 topic entries)
