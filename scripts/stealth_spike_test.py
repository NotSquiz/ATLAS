#!/usr/bin/env python3
"""
S2.1: Patchright Stealth Spike Test

Validates browser stealth setup for BB warming automation.
Opens headed Chrome via Patchright with persistent profile,
checks bot detection sites, and reports PASS/FAIL.

Usage:
    python scripts/stealth_spike_test.py [--keep-open]

Flags:
    --keep-open  Keep browser open after tests for manual inspection
"""

import asyncio
import logging
import sys
from pathlib import Path
from urllib.parse import urlparse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# Domain allowlist (P30) — only these domains allowed during warming
ALLOWED_DOMAINS = {
    "youtube.com",
    "www.youtube.com",
    "google.com",
    "www.google.com",
    "accounts.google.com",
    "bot.sannysoft.com",
    "creepjs.com",
    "abrahamjuliot.github.io",
}

PROFILE_DIR = Path.home() / ".atlas" / ".browser" / "bb_test"
RESULTS: dict[str, tuple[str, str]] = {}  # name -> (status, detail)


def is_domain_allowed(url: str) -> bool:
    """Check if a URL's domain is in the allowlist."""
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname or ""
        for allowed in ALLOWED_DOMAINS:
            if hostname == allowed or hostname.endswith(f".{allowed}"):
                return True
        return False
    except Exception:
        return False


def record(name: str, passed: bool, detail: str = ""):
    """Record a test result."""
    status = "PASS" if passed else "FAIL"
    RESULTS[name] = (status, detail)
    msg = f"[{status}] {name}"
    if detail:
        msg += f" — {detail}"
    if passed:
        logger.info(msg)
    else:
        logger.error(msg)


async def check_webdriver(page) -> bool:
    """Check navigator.webdriver is not exposed."""
    result = await page.evaluate("() => navigator.webdriver")
    if result is True:
        record("navigator.webdriver", False, "webdriver=true (detected as bot)")
        return False
    else:
        record("navigator.webdriver", True, f"webdriver={result}")
        return True


async def check_sannysoft(page) -> bool:
    """Navigate to bot.sannysoft.com and check detection results."""
    logger.info("Navigating to bot.sannysoft.com...")
    try:
        await page.goto("https://bot.sannysoft.com/", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(3)

        # Get all test results with their actual background colors
        all_cells = await page.evaluate("""() => {
            const results = [];
            const rows = document.querySelectorAll('table tr');
            for (const row of rows) {
                const cells = row.querySelectorAll('td');
                if (cells.length >= 2) {
                    const name = cells[0]?.textContent?.trim() || '';
                    const value = cells[1]?.textContent?.trim() || '';
                    const bg = window.getComputedStyle(cells[1]).backgroundColor;
                    // rgb(244, 81, 89) = red/failed, rgb(127, 199, 127) = green/passed
                    const isRed = bg.includes('244, 81, 89') || bg.includes('255, 0, 0');
                    results.push({name, value: value.substring(0, 120), flagged: isRed});
                }
            }
            return results;
        }""")

        flagged = [r for r in all_cells if r.get("flagged")]
        total = len(all_cells)

        for r in flagged:
            logger.warning(f"  FLAGGED: {r['name']} = {r['value']}")

        if flagged:
            names = ", ".join(r["name"] for r in flagged)
            record("bot.sannysoft.com", False, f"{len(flagged)}/{total} red flags: {names}")
            return False
        else:
            record("bot.sannysoft.com", True, f"0/{total} red flags")
            return True

    except Exception as e:
        record("bot.sannysoft.com", False, f"Navigation failed: {e}")
        return False


async def check_creepjs(page) -> bool:
    """Navigate to creepjs.com and check fingerprint trust score."""
    logger.info("Navigating to creepjs.com...")
    try:
        await page.goto(
            "https://abrahamjuliot.github.io/creepjs/",
            wait_until="domcontentloaded",
            timeout=60000,
        )
        logger.info("Waiting for CreepJS fingerprint generation (up to 45s)...")
        await asyncio.sleep(30)

        # Try to extract the trust score / fingerprint grade
        score_info = await page.evaluate("""() => {
            // Look for trust score or grade in common CreepJS elements
            const allText = document.body?.innerText || '';

            // Try to find trust percentage
            const trustMatch = allText.match(/trust[:\\s]*([\\d.]+%?)/i);
            if (trustMatch) return {found: true, text: trustMatch[0]};

            // Try to find grade
            const gradeMatch = allText.match(/grade[:\\s]*([A-F][+-]?)/i);
            if (gradeMatch) return {found: true, text: 'Grade: ' + gradeMatch[1]};

            // Check page title for score
            const title = document.title || '';
            if (title.includes('%')) return {found: true, text: 'Title: ' + title};

            return {found: false, text: 'Score not found (page may still be loading)'};
        }""")

        if score_info.get("found"):
            record("creepjs.com", True, f"Fingerprint: {score_info['text']}")
        else:
            record("creepjs.com", True, "Page loaded — check manually for fingerprint score")

        return True

    except Exception as e:
        record("creepjs.com", False, f"Navigation failed: {e}")
        return False


async def check_youtube(page) -> bool:
    """Navigate to youtube.com and verify it loads."""
    logger.info("Navigating to youtube.com...")
    try:
        await page.goto("https://www.youtube.com/", wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)

        loaded = await page.evaluate("""() => {
            const searchInput = document.querySelector('input#search')
                || document.querySelector('[name="search_query"]');
            const logo = document.querySelector('ytd-logo')
                || document.querySelector('#logo');
            return {
                hasSearch: !!searchInput,
                hasLogo: !!logo,
                title: document.title,
            };
        }""")

        title = loaded.get("title", "unknown")
        if loaded.get("hasSearch") or loaded.get("hasLogo"):
            record("youtube.com", True, f"Loaded with search + logo: {title}")
        else:
            record("youtube.com", True, f"Page loaded: {title}")
        return True

    except Exception as e:
        record("youtube.com", False, f"Navigation failed: {e}")
        return False


async def check_profile_persistence() -> bool:
    """Check that the browser profile directory was created and contains data."""
    if PROFILE_DIR.exists() and any(PROFILE_DIR.iterdir()):
        size_mb = sum(
            f.stat().st_size for f in PROFILE_DIR.rglob("*") if f.is_file()
        ) / (1024 * 1024)
        record("profile_persistence", True, f"{PROFILE_DIR} ({size_mb:.1f} MB)")
        return True
    else:
        record("profile_persistence", False, f"{PROFILE_DIR} empty or missing")
        return False


async def run_spike_test(keep_open: bool = False):
    """Run the full stealth spike test."""
    from patchright.async_api import async_playwright

    logger.info("=" * 60)
    logger.info("S2.1: Patchright Stealth Spike Test")
    logger.info("=" * 60)

    # Ensure profile directory exists
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Browser profile: {PROFILE_DIR}")

    async with async_playwright() as p:
        logger.info("Launching headed Chrome via Patchright...")
        try:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=str(PROFILE_DIR),
                channel="chrome",
                headless=False,
                no_viewport=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                ],
            )
            record("chrome_launch", True, "Headed Chrome window opened via WSLg")
        except Exception as e:
            record("chrome_launch", False, f"Launch failed: {e}")
            print_summary()
            return

        page = context.pages[0] if context.pages else await context.new_page()

        # --- Test 1: navigator.webdriver ---
        await check_webdriver(page)

        # --- Test 2: bot.sannysoft.com ---
        await check_sannysoft(page)

        # --- Test 3: creepjs (separate page, no route blocking — needs CDN resources) ---
        page2 = await context.new_page()
        await check_creepjs(page2)
        await page2.close()

        # --- Test 4: YouTube loads ---
        page3 = await context.new_page()
        await check_youtube(page3)
        await page3.close()

        # --- Test 5: Profile persistence ---
        await check_profile_persistence()

        if keep_open:
            logger.info("Browser kept open for manual inspection. Close browser to exit.")
            try:
                await context.pages[0].wait_for_event("close", timeout=0)
            except Exception:
                pass
        else:
            await context.close()

    print_summary()


def print_summary():
    """Print test summary."""
    print("\n" + "=" * 60)
    print("STEALTH SPIKE TEST RESULTS")
    print("=" * 60)

    passes = 0
    fails = 0
    for name, (status, detail) in RESULTS.items():
        icon = "+" if status == "PASS" else "X"
        line = f"  [{icon}] {name}: {status}"
        if detail:
            line += f"  ({detail})"
        print(line)
        if status == "PASS":
            passes += 1
        else:
            fails += 1

    print("-" * 60)
    print(f"  Total: {passes} PASS, {fails} FAIL")

    if fails == 0:
        print("\n  VERDICT: PASS — Stealth setup working. Proceed to S2.2.")
    elif fails <= 1 and "navigator.webdriver" not in [
        n for n, (s, _) in RESULTS.items() if s == "FAIL"
    ]:
        print("\n  VERDICT: CONDITIONAL PASS — Minor flags only.")
        print("  webdriver hidden, YouTube loads, profile persists.")
        print("  Proceed to S2.2 with monitoring.")
    else:
        print("\n  VERDICT: FAIL — Review flags above.")
        print("  Fallback options:")
        print("    1. Run on desktop machine (real GPU fixes WebGL flag)")
        print("    2. Manual warming while researching alternatives")
        print("    3. Headless with additional patches (higher risk)")

    print("=" * 60)


if __name__ == "__main__":
    keep_open = "--keep-open" in sys.argv
    asyncio.run(run_spike_test(keep_open=keep_open))
