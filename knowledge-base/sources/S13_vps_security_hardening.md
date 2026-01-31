# S13: Moltbot VPS Security Hardening

**Source:** Multiple X.com posts — Itamar Golan (@ItakGol, security researcher), community VPS hardening guide, anonymous exploit report
**Date:** January 2026
**Type:** Security warnings + practical hardening guide + real-world exploit evidence
**Credibility:** Very high for security. Golan is a known security researcher. The exploit report (Netflix/Spotify/bank accounts harvested from other Clawdbot users) is the most alarming evidence we've seen. The VPS hardening guide is practical, step-by-step, and follows industry best practices.

**This is the most important security source in the entire knowledge base.** Previous security discussion was theoretical (R31 ransomware via skills, S8 permission creep). This source documents ACTIVE EXPLOITATION of live Clawdbot instances.

---

### S13 — The Threat Is Real (Not Theoretical)

**Itamar Golan's warning:**
> "Thousands of ClawdBots are live right now on VPSs... with open ports to the internet... and zero authentication. This is going to get ugly."

**The exploit report (anonymous user):**
> "I asked Clawdbot to get me free stuff, and so far it's gotten me a double-digit number of Netflix and Spotify accounts, and a bunch of bank accounts belonging to other Clawdbot users."

**Translation:** Someone used THEIR Clawdbot to scan for and exploit OTHER people's unsecured Clawdbots. The unsecured agents handed over their owners' credentials because they had no authentication, no access controls, and were exposed to the public internet.

**The commenter who said "seems like a lot of bullshit vs just putting it on a mac mini" is correct.** Local hardware with no public internet exposure eliminates the entire VPS attack surface. This directly validates our decision to use a local desktop machine (S3).

---

### S13 — Extracted Items

#### THREAT LANDSCAPE

| # | Item | Tags | Relevance | Notes |
|---|------|------|-----------|-------|
| S13.01 | **Active exploitation of unsecured Clawdbots** — users' Netflix, Spotify, and BANK ACCOUNTS harvested by other users' bots scanning the internet. | `SECURITY` | HIGH | This is no longer theoretical. Agents with access to credentials, exposed to the internet without auth, are being actively exploited. If our agent ever touches the internet, it MUST be behind authentication. |
| S13.02 | **"The internet is a nonstop scanner"** — automated bots continuously probe every public IP for open ports and services. | `SECURITY` | HIGH | Any publicly-exposed port will be found and probed within hours. Our agent on the new desktop should NEVER have public-facing ports. Tailscale VPN or equivalent for all remote access. |
| S13.03 | **Unauthenticated public endpoint = "please take over my bot"** — agent with web browse, tool access, file access, secret access, and internal endpoint access is a complete attack surface. | `SECURITY` | HIGH | Inventory of what our agent will have access to: health data, Baby Brains business data, API keys, credentials, shell access. An unauthenticated endpoint exposing all of this would be catastrophic. |

#### VPS HARDENING GUIDE (11-Step Checklist)

| # | Item | Tags | Relevance | Notes |
|---|------|------|-----------|-------|
| S13.04 | **SSH: keys only, no passwords, no root login** | `SECURITY` | HIGH | Standard hardening. If we ever SSH into the desktop remotely: key-based auth only. `PasswordAuthentication no`, `PermitRootLogin no`. |
| S13.05 | **UFW firewall: default deny incoming, allow outgoing** | `SECURITY` | HIGH | `ufw default deny incoming` — nothing gets in unless explicitly allowed. This is the correct default for any machine running an AI agent. |
| S13.06 | **Fail2ban: auto-ban IPs after failed login attempts** | `SECURITY` | HIGH | Brute-force protection. Auto-bans attackers. Zero reason not to install this on any server. |
| S13.07 | **Tailscale VPN mesh: private network for all access** | `SECURITY` `TOOLS` | HIGH | **Key tool.** Tailscale creates a private VPN mesh between your devices. SSH, web ports, and all agent access only via Tailscale — no public exposure. Free for personal use. This is how we should access the new desktop remotely. |
| S13.08 | **SSH only via Tailscale IP range** — `ufw allow from 100.64.0.0/10 to port 22` then delete public SSH rule | `SECURITY` | HIGH | After Tailscale: SSH is only reachable from inside the VPN. Public SSH access deleted entirely. |
| S13.09 | **Web ports (80/443) private via Tailscale** — only accessible from your devices on the mesh | `SECURITY` | HIGH | If we run LobeHub, MCP servers, or any web UI on the desktop: only reachable via Tailscale. No public internet exposure. |
| S13.10 | **Moltbot locked to owner only** — `dmPolicy: "allowlist"`, only your Telegram ID allowed. `groupPolicy: "allowlist"`. | `SECURITY` `COMMS` | HIGH | When we build our Telegram bridge: ALLOWLIST ONLY. Only your Telegram user ID can communicate with the agent. No group access. No strangers. |
| S13.11 | **Credential permissions: `chmod 700` for credential dirs, `chmod 600` for .env** | `SECURITY` | HIGH | Basic but critical. Credentials should never be world-readable. Our `.env` file with API keys must be 600. |
| S13.12 | **Security audit command: `clawdbot security audit --deep`** — catches issues you missed | `SECURITY` `TOOLS` | MEDIUM | We should build an equivalent for ATLAS: a security self-check that verifies file permissions, exposed ports, credential access, firewall rules. |
| S13.13 | **Disable IPv6 if unused** — reduces attack surface. | `SECURITY` | MEDIUM | Minor but sensible. Less surface area = less risk. |
| S13.14 | **Enable unattended upgrades** — auto-apply security patches | `SECURITY` | HIGH | Critical for a 24/7 machine. Security patches should apply automatically, not wait for us to remember. `sudo apt install unattended-upgrades`. |

#### META-LESSON

| # | Item | Tags | Relevance | Notes |
|---|------|------|-----------|-------|
| S13.15 | **"Buckle seatbelts before stepping on gas"** — security BEFORE features. Don't deploy, then secure. Secure, then deploy. | `SECURITY` | HIGH | Applies directly to our new desktop setup. Before we install LobeHub, ATLAS daemon, MCP servers, or anything else: harden the OS, configure firewall, install Tailscale, set permissions. Security first. |
| S13.16 | **"Just put it on a mac mini" response** — local hardware eliminates VPS attack surface entirely. No public ports = no remote exploitation. | `SECURITY` `ARCH` | HIGH | The commenter is right. Our new desktop running locally, not exposed to the internet, eliminates the ENTIRE class of attacks described in this source. The only remaining attack vectors are: physical access, malicious software we install ourselves, and compromised API keys. Much smaller surface. |

---

### S13 — Key Patterns Identified

**Pattern 28: Security Before Features (Non-Negotiable)**
Every VPS-deployed Clawdbot that got exploited was deployed features-first, security-later (or never). The correct order is: harden OS → configure firewall → install VPN → set permissions → THEN install agent software → THEN configure features. This is our setup order for the new desktop.

**Pattern 29: Local > VPS for Security (With Tradeoff)**
Local hardware with no public internet exposure eliminates remote exploitation entirely. The tradeoff: no remote access unless you set up VPN (Tailscale). For our use case, this tradeoff is worth it — we want a 24/7 agent, not a publicly-accessible service.

**Pattern 30: Allowlist-Only for All External Interfaces**
When the agent communicates externally (Telegram, email, web): allowlist only. Specific Telegram user IDs. Specific email addresses. Specific domains for browser access (from S10). Never open to "anyone." The default is DENY, with explicit exceptions.

---

### S13 — New Desktop Setup Checklist (Derived from S13)

This is the security hardening checklist for our new desktop machine, BEFORE we install any agent software:

```
PHASE 0: SECURITY HARDENING (Before anything else)
□ 1. Create non-root user account for agent services
□ 2. Install UFW, set default deny incoming
□ 3. Install fail2ban
□ 4. Install Tailscale, join VPN mesh
□ 5. SSH keys only (if remote access needed)
□ 6. SSH only via Tailscale IP range
□ 7. All web ports (LobeHub, MCP servers) via Tailscale only
□ 8. chmod 600 all .env files
□ 9. chmod 700 all credential directories
□ 10. Enable unattended-upgrades for security patches
□ 11. Disable IPv6 if unused
□ 12. Verify: `ufw status`, `ss -tulnp`, `tailscale status`

PHASE 1: AGENT SOFTWARE (Only after Phase 0 complete)
□ Install Docker (containerized services)
□ Install ATLAS services
□ Install LobeHub (if evaluated)
□ Configure Telegram bridge (allowlist-only)
□ Configure MCP servers

PHASE 2: ONGOING
□ Monthly security audit (check ports, permissions, keys)
□ Rotate API keys quarterly
□ Review logs for anomalies
□ Keep incident response plan (worst case: pull network cable)
```

---

### S13 — Cross-References

| Item | S13 Says | Previous Sources Say | Synthesis |
|------|---------|---------------------|-----------|
| VPS security | Active exploitation of unsecured agents | S3.09: physical kill switch; S8.02: dedicated bot identity | **S13 proves S3 and S8 right.** Local hardware + identity isolation isn't paranoia — it's the correct response to documented exploitation. |
| Tailscale VPN | Private mesh network for all access | S3.11: containerized isolation; S10.08: Gartner says block AI browsers | **Tailscale is the access control layer.** All remote access via VPN. No public exposure. Combined with S3's container isolation for service separation. |
| Credential theft | Bank accounts harvested from other users' bots | S8.03: agents request max permissions; R31: ransomware via skills | **Escalating severity.** R31: demonstrated ransomware (proof of concept). S8: permission creep (behavioral). S13: ACTIVE credential theft (production exploitation). The threat is real and current. |
| Allowlist-only | Telegram DM allowlist by user ID | S7.07: host controls MCP App capabilities; S10.09: browser whitelist domains | **Consistent pattern across ALL external interfaces.** Telegram: allowlist user IDs. Browser: allowlist domains. MCP Apps: host-controlled capabilities. Email: allowlist senders. Default DENY everything. |
| Local vs cloud | "Just put it on a mac mini" eliminates VPS attack surface | S3.07: data sovereignty; S2.18: dedicated machine with separate accounts | **Local hardware is the security-optimal deployment.** VPS requires 11+ hardening steps. Local machine requires physical security (which you already have). The ease difference is enormous. |

---

### S13 — Credibility Assessment

**Strengths:**
- Security researcher (Golan) with specific, actionable warnings
- REAL exploitation evidence (Netflix/Spotify/bank accounts harvested)
- Step-by-step hardening guide with exact commands
- Industry-standard tools (UFW, fail2ban, Tailscale)
- "When NOT to" perspective (the mac mini comment)

**Weaknesses:**
- Exploit report is anonymous and unverifiable (could be exaggerated)
- VPS hardening guide assumes Ubuntu specifically
- Doesn't address application-layer security (prompt injection, data exfiltration through legitimate channels)

**Overall:** Highest importance security source. The gap between "people are deploying agents" and "people are securing agents" is enormous. This source documents the consequences of that gap. Every item in the hardening checklist should be implemented on our new desktop.

---

*S13 processed: January 30, 2026*

---
