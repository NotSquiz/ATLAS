# Browser Stealth Research for BB Warming Automation

**Date:** January 31, 2026
**Purpose:** Anti-detection research for Playwright-based YouTube/Instagram warming automation
**Context:** KB audit finding — YouTube terminates accounts via infrastructure-level bot detection (D102). Stealth patches mandatory.

---

## Executive Summary

Default Playwright is trivially detectable. YouTube's Dec 2025/July 2025 enforcement uses browser fingerprinting, CDP leak detection, behavioral analysis, and AI-based account linkage. Using Playwright out-of-the-box for automated watching/liking will eventually lead to account flagging.

**Recommended stack:** Patchright (patched Playwright fork) + humanization-playwright (Bezier curves, variable typing, smooth scroll) + persistent browser profile + manual first-time Google login.

---

## Detection Vectors (What YouTube/Instagram Look For)

| Vector | Description | Default Playwright Status |
|--------|-------------|--------------------------|
| `navigator.webdriver` flag | Boolean indicating automation | EXPOSED (detectable) |
| CDP Runtime.enable | Chrome DevTools Protocol leak | LEAKING |
| Command-line flags | `--enable-automation`, etc. | PRESENT |
| Canvas fingerprint | Consistent across sessions if not spoofed | STATIC |
| WebGL fingerprint | GPU rendering signature | STATIC |
| Mouse movement patterns | Linear = bot, Bezier curves = human | LINEAR |
| Typing cadence | Uniform speed = bot | UNIFORM |
| Scroll behavior | Instant jump = bot | INSTANT |
| Browser profile | No cookies/history = suspicious | EMPTY each launch |
| IP reputation | Known datacenter IPs flagged | N/A (residential IP) |
| Account linkage | Shared recovery details, device ID | N/A |

---

## Tool Comparison (Python, January 2026)

### Tier 1: Patchright + humanization-playwright (RECOMMENDED)

**What:** Patched Playwright fork that fixes CDP leaks and automation flags at source level.

**Why recommended:**
- Python-native (`pip install patchright`)
- Chromium-based (YouTube/Instagram are Chromium-optimised)
- Fixes `navigator.webdriver`, `Runtime.enable` leak, command flag leaks
- humanization-playwright adds Bezier mouse curves, variable typing, smooth scrolling
- API-compatible with Playwright (minimal code changes from existing plan)
- Considered "undetectable" with proper setup (per maintainers and community reports)

**Installation:**
```bash
pip install patchright
pip install humanization-playwright
patchright install chrome  # Use system Chrome, NOT bundled Chromium
```

**What Patchright actually patches:**
- `Runtime.enable` CDP command (the #1 detection vector in 2025-2026) -- executes JS in isolated ExecutionContexts instead
- `navigator.webdriver` flag via `--disable-blink-features=AutomationControlled`
- Removes `--enable-automation`, `--disable-popup-blocking`, `--disable-component-update` flags
- Console API disabled to prevent detection via console binding inspection
- Closed Shadow DOM interaction support (can interact with elements in shadow roots)
- CDP artifacts like `__playwright__binding__` invisible to page JavaScript

**Recommended launch configuration (async Python):**
```python
from patchright.async_api import async_playwright

async def launch_stealth_browser():
    async with async_playwright() as p:
        # CRITICAL: persistent context + system Chrome + headed mode
        context = await p.chromium.launch_persistent_context(
            user_data_dir="/home/squiz/.atlas/browser_profiles/youtube_bb",
            channel="chrome",        # System Chrome, NOT bundled Chromium
            headless=False,          # Headed mode avoids headless detection
            no_viewport=True,        # Use native resolution
            # Do NOT set custom user_agent or extra headers
            # Let the real Chrome provide its own fingerprint
        )
        page = context.pages[0] if context.pages else await context.new_page()
        return context, page
```

**With humanization layer:**
```python
from humanization_playwright import HumanizedBrowser, HumanizationConfig

config = HumanizationConfig(
    stealth_mode=True,
    typing_speed=(50, 150),   # Variable ms per char
    mouse_speed="natural",     # Bezier curve movements
)

async def watch_video(url: str):
    browser = HumanizedBrowser(config=config)
    await browser.launch(
        user_data_dir="/home/squiz/.atlas/browser_profiles/youtube_bb",
        channel="chrome",
        headless=False,
    )
    page = await browser.new_page()

    # Navigate with human-like behavior
    await page.goto(url)
    await browser.random_delay(2000, 5000)  # Variable pause

    # Human-like scroll to simulate reading
    await browser.scroll_to(page, y=300, speed="slow")
    await browser.random_delay(1000, 3000)

    # Click like button with bezier curve mouse movement
    like_button = page.locator('button[aria-label*="like"]')
    await browser.click_at(like_button)
```

**Limitations:**
- Chromium-only (no Firefox/WebKit)
- Headed mode required (need display or Xvfb on WSL2)
- Still requires realistic browsing patterns on top of stealth patches

### Tier 2: Camoufox (Firefox-based alternative)

**What:** Anti-detect browser built on Firefox with Playwright API compatibility.

**Why consider:**
- Fingerprint rotation via BrowserForge (mimics real device distribution)
- Spoofs navigator, screen, WebGL, audio, fonts, timezone
- Firefox is inherently harder to fingerprint than Chromium
- Playwright API compatible (similar code structure)
- Built-in `humanize` parameter for cursor movement

**Installation:**
```bash
pip install camoufox[geoip]
python -m camoufox fetch  # Downloads ~400MB browser binary
```

**Basic usage:**
```python
from camoufox.async_api import AsyncCamoufox

async with AsyncCamoufox(
    os="linux",  # Match actual OS
    humanize=True,
) as browser:
    page = await browser.new_page()
    await page.goto("https://youtube.com")
```

**Current status (Jan 2026):** UNSTABLE. Year gap in maintenance, v146.0.1-beta.25 is experimental. Performance has degraded from original. Under active development but not production-ready.

**Verdict:** Monitor for stability. If Camoufox stabilises, it may surpass Patchright for stealth. For now, too risky for production use.

### Tier 3: Nodriver / Zendriver

**What:** Alternative Python browser automation (not based on Playwright/Selenium).

**Why mention:**
- 75% bypass rate in benchmarks vs 25% for default Playwright/Selenium
- Async-first architecture
- No traditional automation signatures (no CDP, no WebDriver protocol)

**Why NOT recommended for us:**
- Different API than Playwright (would require rewriting all browser code)
- Smaller community, fewer tutorials
- No proxy/CAPTCHA support yet
- Would diverge from our existing Playwright-based architecture

---

## YouTube-Specific Risk Assessment (2025-2026)

### Policy Changes
- **July 2025:** YouTube expanded "repetitious content" to "inauthentic content" with stricter AI enforcement
- **Circumvention Policy:** If channel terminated, you CANNOT create new channels (even with different email/phone/device)
- **Detection methods:** Browser fingerprinting, account linkage, behavioral pattern analysis, AI-based flagging

### Risk Matrix for BB Warming

| Action | Risk with Patchright+Stealth | Risk without Stealth | Notes |
|--------|------------------------------|---------------------|-------|
| Watch videos (60-300s) | VERY LOW | MEDIUM | Longest dwell = most natural |
| Like after watching | LOW | MEDIUM | Must follow real watch time |
| Subscribe (max 2/day) | LOW | HIGH | Aggressive subscribing = red flag |
| Comment posting | HUMAN ONLY | N/A | Automated posting = account death |
| Login automation | AVOID | AVOID | Manual first-time login, persist session |

### Critical Rules
1. **NEVER automate Google login.** Log in manually once, persist the browser profile. Re-auth manually if cookies expire.
2. **NEVER post comments via automation.** Human copy-paste only (D102 decision stands).
3. **Persistent browser profile is MANDATORY.** Fresh profiles with no history are a detection signal.
4. **Residential IP only.** YouTube flags datacenter IPs. Your home connection is fine.
5. **One account per browser profile.** Don't switch accounts in the same context.

---

## Behavioral Detection Vectors (Most Critical for Engagement)

These are what catch most automation AFTER fingerprint stealth is solved:

| Vector | What Detects It | Mitigation |
|--------|----------------|------------|
| Perfectly straight mouse movements | DataDome, YouTube | humanization-playwright Bezier curves |
| Instant clicks (no mouse travel) | All platforms | ghost-cursor / humanization library |
| Uniform timing between actions | Pattern recognition AI | Gaussian delay distribution (not uniform random) |
| No scroll events during video | YouTube, Instagram | Simulate natural scrolling with variable speed |
| No idle time / constant activity | All platforms | Build in random pauses, tab switches |
| Action rate spikes | Instagram especially | Rate limit: max 20-30 actions/hour |
| Zero mistakes (no misclicks) | Advanced behavioral AI | humanization-playwright adds typo simulation |
| Session duration anomalies | YouTube watch time | Watch 60-80% of actual video length |

---

## Platform-Specific Risk Assessments

### Instagram: HIGH Risk (Most Aggressive Detection)

- Instagram tracks a **"trust score"** per account -- once flagged, detection sensitivity permanently increases
- Action blocks ("feedback_required" error) trigger after even moderate automation
- Device fingerprint + IP correlation used to link accounts
- Shadow bans degrade reach without notification
- Mobile residential proxies preferred (Instagram is mobile-first)
- **Never exceed 20-30 actions per hour** (likes + follows combined)
- Warm up account manually for first 7-14 days before any automation
- Mix automated actions with genuine manual use on same device

### TikTok: MEDIUM Risk

- New accounts face 14-day warming requirement
- Algorithm flags accounts that do not receive ads (not yet trusted)
- IP-per-account requirement is strict
- Complete every profile field during setup
- Follow 10-15 accounts in niche during first week manually

---

## Recommended Session Design for BB Warming

```
1. Launch persistent context with system Chrome (Patchright)
2. Navigate to YouTube (already logged in via persistent profile)
3. Search for niche content ("baby development activities", "montessori for babies")
4. Scroll search results with humanized scrolling
5. Click on video (Bezier curve mouse movement)
6. Actually watch 60-80% of video (random between 60-80% of duration)
7. Random chance to like (70%) or subscribe (10% for quality channels)
8. Random delay 30s-3min between videos (gaussian distribution)
9. Watch 3-7 videos per session
10. Session duration: 15-45 minutes
11. 1-2 sessions per day max
12. Log all actions to BB database
```

### Infrastructure for Headed Mode on WSL2

```bash
# Required for headed Chrome on WSL2 without WSLg
sudo apt install xvfb
Xvfb :99 -screen 0 1920x1080x24 &
export DISPLAY=:99

# Install system Chrome for Patchright
patchright install chrome
```

### What NOT to Do

1. **Do NOT use headless mode** -- headless Chrome renders differently and is detectable
2. **Do NOT set custom User-Agent or headers** -- introduces fingerprint inconsistencies
3. **Do NOT use datacenter proxies** -- instant flag on all platforms (home IP is fine)
4. **Do NOT automate Google login** -- log in manually once, persist session
5. **Do NOT exceed 5-10 interactions per platform per day** during first month

---

## Implementation Plan for S2.1-S2.3

### S2.1: Spike Test (Updated)
1. Install Patchright + humanization-playwright
2. Launch with persistent profile + system Chrome
3. Manually log into Google/YouTube in the automated browser (one-time)
4. Verify stealth: visit `bot.sannysoft.com` and `creepjs.com` — all checks should pass
5. Watch a YouTube video for 120s with humanized scrolling

### S2.2: Browser Automation (Updated)
- Replace `playwright` imports with `patchright` (API-compatible, minimal changes)
- Add humanization config for all interactions
- Use persistent browser context (user_data_dir)
- Gaussian delay distribution (not uniform random)
- Random viewport sizes from realistic set (1366x768, 1920x1080, 1536x864)
- Scroll during video watch (random intervals, random amounts)

### S2.3: Integration
- WarmingBrowser class uses Patchright instead of Playwright
- Manual login flow documented for first-time setup
- Profile backup/restore for machine migration

---

## Dependencies to Add

```
# requirements.txt additions for Week 2
patchright>=1.0.0
humanization-playwright>=0.1.0
# camoufox[geoip]  # MONITOR - not stable enough yet (Jan 2026)
```

---

## Open Questions

1. **Profile persistence across machines:** How to transfer the logged-in browser profile from laptop to desktop? Options: copy user_data_dir folder, or log in manually on each machine.
2. **Cookie expiry:** Google session cookies expire. Need a process for re-authentication (manual) when sessions drop.
3. **Headless fallback:** If WSLg doesn't work, can Patchright run headless with full stealth? Needs testing. YouTube's headless detection is aggressive.
4. **Rate limiting triggers:** What's the exact threshold for likes/subscribes before YouTube flags? Community reports vary. Start conservative, increase gradually.

---

## Sources

### Tools & Libraries
- [Patchright Python](https://github.com/Kaliiiiiiiiii-Vinyzu/patchright-python) -- recommended Playwright fork
- [humanization-playwright](https://pypi.org/project/humanization-playwright/) -- Bezier mouse + typing
- [Camoufox](https://camoufox.com/) / [GitHub](https://github.com/daijro/camoufox) -- Firefox anti-detect
- [Rebrowser Patches](https://github.com/rebrowser/rebrowser-patches) -- alternative Playwright patches
- [python-ghost-cursor](https://github.com/mcolella14/python_ghost_cursor) -- alternative mouse humanization
- [ghost-cursor-playwright](https://github.com/bn-l/ghost-cursor-play) -- ghost cursor for Playwright

### Platform Policy & Detection
- [YouTube Monetization Policy Update July 2025](https://fliki.ai/blog/youtube-monetization-policy-2025)
- [YouTube Policy Circumvention 2025](https://digiarun.com/resources/youtube-policy-circumvention-termination-2025/)
- [Antidetect Browsers for YouTube 2025](https://multilogin.com/blog/best-antidetect-browsers-for-youtube/)
- [Instagram Automated Behaviour Detection](https://www.spurnow.com/en/blogs/instagram-automated-behaviour)
- [TikTok Account Warm-Up Guide](https://autoshorts.ai/blog/how-to-warm-up-tiktok-account)

### Technical Analysis
- [Patchright vs Playwright](https://dev.to/claudeprime/patchright-vs-playwright-when-to-use-the-stealth-browser-fork-382a)
- [How to Scrape with Camoufox](https://www.scrapingbee.com/blog/how-to-scrape-with-camoufox-to-bypass-antibot-technology/)
- [Detecting Vanilla Playwright](https://scrapingant.com/blog/detect-playwright-bot)
- [Nodriver/Zendriver vs Selenium/Playwright Benchmarks](https://medium.com/@dimakynal/baseline-performance-comparison-of-nodriver-zendriver-selenium-and-playwright-against-anti-bot-2e593db4b243)
- [Anti-Detect Framework Evolution](https://blog.castle.io/from-puppeteer-stealth-to-nodriver-how-anti-detect-frameworks-evolved-to-evade-bot-detection/)
- [Bot Detection 101 (2025)](https://blog.castle.io/bot-detection-101-how-to-detect-bots-in-2025-2/)

---

*Research conducted: January 31, 2026*
*Next action: S2.1 spike test with Patchright + humanization-playwright*
