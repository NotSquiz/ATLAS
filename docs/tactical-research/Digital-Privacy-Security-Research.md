# Digital Privacy and Personal Information Security Research

## Executive Summary

This document provides practical guidance for Australian families seeking to reduce their digital footprint and protect their privacy online. It covers smartphone privacy management, social media settings, home network security, encrypted communications, data broker exposure, and personal security practices, with specific references to Australian resources and legislation.

---

## 1. Smartphone Privacy

### Location Tracking Management

Modern smartphones continuously track location through GPS, WiFi networks, and cell tower connections. This data builds patterns of movements, habits, and daily routines that apps can access and share with third parties.

**Key Privacy Risks:**
- Apps collect location data for advertising and analytics
- The Gravy Analytics breach revealed thousands of apps (including Flightradar24, Grindr, Moovit, Muslim Pro, Tinder) facilitated sensitive location data collection
- Mobile app location tracking puts individuals at risk of stalking, surveillance, and physical harm

**iOS Location Management:**
- Enable Stolen Device Protection in Settings
- Set AirDrop to "Contacts Only"
- Turn off Significant Locations: Settings > Privacy > Location Services > System Services > Significant Locations
- Use Safari's "Hide IP Address" feature
- For iOS 13+, select "Allow Once" for temporary location access
- Review location permissions per app in Settings > Privacy > Location Services

**Android Location Management:**
- Settings > Privacy > Permission manager > Location
- Set location access to "Only while app is in use" or "Ask every time"
- Enable auto-reset permissions: Settings > Apps > Special app access > Remove permissions if app isn't used
- Delete advertising ID: Settings > Privacy > Ads
- Turn off WiFi scanning and Bluetooth scanning: Settings > Location (prevents background probing)

### App Permissions Management

Third-party apps can collect, share, and sell information if permissions are not properly managed. Apps may request access to:
- Photo library
- Audio/video recording and livestreaming
- Real-time location
- SMS text messages
- Health data from fitness trackers
- Contact list
- Calendar events
- Device storage

**Best Practices:**

1. **Audit Installed Apps**
   - Remove apps you do not use
   - Review permissions for remaining apps
   - Delete apps requiring uncomfortable data access

2. **Apply "Deny by Default"**
   - Deny access to any data or functions not required for the app's core purpose
   - Just because an app requests camera access does not mean camera permissions are needed

3. **Limit Location Permissions**
   - For apps requiring location, limit to "while in use only"
   - Regularly review which apps have location access

4. **Keep Apps Updated**
   - Out-of-date apps may have exploitable vulnerabilities
   - Install updates as released

**Platform-Specific Features:**

*Android:*
- Privacy Dashboard: Displays all permissions used by apps in past 24 hours
- Access via Settings > Privacy > Permission Manager

*iOS:*
- App Privacy Report: Shows how apps use granted permissions and network activity
- Settings > Privacy > App Privacy Report
- Disable app tracking: Settings > Privacy > Tracking > Toggle off "Allow Apps to Request to Track"

### Critical Permissions to Watch

Be particularly cautious with permissions for:
- Microphone
- Body sensors
- Health data
- Calendar
- Camera
- Contacts
- Location
- Built-in messaging
- Call functions
- Storage

**Sources:**
- [CISA: Privacy and Mobile Device Apps](https://www.cisa.gov/news-events/news/privacy-and-mobile-device-apps)
- [CISA: Manage Application Permissions](https://www.cisa.gov/resources-tools/training/manage-application-permissions-privacy-and-security)
- [Android Privacy Settings](https://www.android.com/intl/en_us/safety/privacy/)
- [Apple: Control Access to Information in Apps](https://support.apple.com/guide/iphone/control-access-to-information-in-apps-iph251e92810/ios)
- [Consumer Reports: Protect Your Privacy From Apps](https://www.consumerreports.org/electronics-computers/privacy/protect-your-privacy-from-the-apps-on-your-phone-a1049648633/)

---

## 2. Social Media Privacy

### Facebook and Instagram Privacy

**What Meta Collects:**
- Meta stores full original photos with all metadata on their servers
- Even though GPS coordinates are stripped from publicly visible images, Meta retains this information in its own database
- Facebook's downloadable archive contains photos bundled with geotags and IP addresses

**Key Privacy Settings:**

*Disable Location Services:*
- Settings & Privacy > Settings > Location
- Turn off location services entirely by selecting "Don't allow location access"
- This prevents Facebook from tracking physical movements and building location-based advertising profiles

*Manage Off-Platform Tracking:*
- Meta Pixel on websites monitors visitor activity for targeted advertising
- Accounts Center > Account settings > Your information and permissions > Your activity off Meta technologies
- Review and clear history, choose "Disconnect" to stop future tracking

*Photo Privacy:*
- To prevent nosy apps accessing photos: Settings > Privacy > Photos > [App Name] > Select "None"
- Strip metadata before uploading using tools like PrivacyStrip
- Turn off automatic location tagging

### Photo Metadata Risks

EXIF data embedded in photos can reveal:
- Exact GPS coordinates where photo was taken
- Date and time of capture
- Device information
- Camera settings

**Protecting Photo Privacy:**
- Strip GPS data before uploading to any platform
- Use metadata removal tools (PrivacyStrip, EXIF removal apps)
- Disable geotagging in smartphone camera settings
- Review photos before sharing for identifiable location details

### Location Check-ins

**Risks:**
- Real-time location disclosure enables stalking or targeted theft
- Historical check-ins reveal patterns (work location, gym schedule, children's school)
- Friends tagging you can expose location without consent

**Recommendations:**
- Disable location tagging by default
- Review and approve tags before they appear on your profile
- Avoid real-time check-ins; post about locations after leaving
- Regularly audit past posts and remove location data

### Privacy Settings Review

Facebook and social media privacy is not set-and-forget. New features and policy updates occur regularly.

- Review privacy settings every few months
- Check friend lists and audience settings for posts
- Review apps connected to social media accounts
- Enable login notifications for unusual activity

**Sources:**
- [Reader's Digest: Facebook Instagram Privacy Setting](https://www.rd.com/article/facebook-instagram-privacy-setting/)
- [AboutThisImage: Social Media Metadata Guide](https://aboutthisimage.com/social-media-metadata)
- [Kaspersky: What EXIF Can Tell About Your Photos](https://www.kaspersky.com/blog/exif-privacy/13356/)
- [PrivacyStrip: Social Media Metadata Policies](https://privacystrip.com/blog/social-media-metadata-policies/)

---

## 3. Home Network Security

### Router Security Settings

**Essential Router Security:**
1. **Change Default Credentials**
   - Use strong, unique admin password
   - Change default router username

2. **Update Firmware Regularly**
   - Keep router firmware current
   - Enable automatic updates if available
   - ASD's ACSC has observed malicious actors targeting edge devices (routers, firewalls, VPN concentrators)

3. **Disable Remote Management**
   - Remote management allows access from the internet
   - Known attack vector for cybercriminals
   - Keep disabled unless specifically required

4. **Disable WPS (WiFi Protected Setup)**
   - WPS has known vulnerabilities
   - Disable for improved security

5. **Hide Network SSID** (optional)
   - Prevents casual discovery
   - Not a strong security measure but adds minor obscurity

### WiFi Security (WPA3)

**WPA3 Advantages:**
- Requires attackers to interact with WiFi for each password guess, preventing dictionary attacks
- Makes brute-force attacks more time-consuming
- Uses forward secrecy: even if encrypted data is captured and password later obtained, captured data cannot be decrypted
- Currently the most secure method available

**WPA3 Limitations:**
- Design and implementation flaws known as "Dragonblood vulnerabilities" exist
- Includes downgrade attacks (forcing reversion to WPA2) and side-channel attacks
- Vendors can mitigate with software updates

**Legacy Device Considerations:**
- Older IoT devices may not support WPA3
- Millions of networks cannot use WPA3 due to legacy device compatibility
- WPA2 is better than nothing but increasingly vulnerable
- Strongly recommend WPA3 where possible

### IoT Device Risks

**Current Statistics (2025-2026):**
- Average household: 22 connected devices
- Global IoT devices expected to reach 21.1 billion by end of 2025
- 52%+ of organizations experienced cyberattacks via IoT/OT devices
- Home network attack attempts: average 29 daily per household

**Common Vulnerable Devices:**
- Smart TVs
- Smart speakers
- Thermostats
- Baby monitors
- Security cameras
- Printers
- Smart appliances

**Risks:**
- Weak built-in security on many devices
- Single compromised device can expose entire home network
- Attackers can use compromised devices for surveillance or staging further attacks

### Network Segmentation

**Guest Network Strategy:**
- Create separate guest networks for visitors and IoT devices
- Isolates IoT devices from accessing sensitive information on main network
- Prevents compromised IoT device from reaching personal computers or smartphones

**Implementation:**
- Most modern routers support multiple SSIDs
- Configure main network for trusted devices (computers, phones)
- Configure guest/IoT network for smart home devices, visitors

### Future Security Trends (2026)

- AI-based security monitoring built into next-gen routers
- Quantum-resistant encryption protocols in development
- Zero-trust home networking models treating every device as potential risk
- WPA4 development underway
- Wi-Fi 7 security enhancements

**Sources:**
- [TechBoltx: Secure Home WiFi Network 2025](https://techboltx.com/secure-home-wifi-network-2025/)
- [ExpressVPN: 12 Smart Ways to Secure Home WiFi](https://www.expressvpn.com/blog/how-to-secure-your-home-wi-fi/)
- [TechGenyz: IoT Security in 2025](https://techgenyz.com/iot-security-smart-home-risks-protection-guide/)
- [Batten Home Security: Securing IoT Devices 2026](https://battenhomesecurity.com/briefs/securing-iot-devices-smart-homes/)
- [DigiCert: How Weak WiFi Security Endangers IoT Devices](https://www.digicert.com/blog/wi-fi-hacked-iot-devices)

---

## 4. Communication Privacy

### Encrypted Messaging Apps

**Signal - The Gold Standard:**
- Uses Signal Protocol for all messages, calls, and group chats by default
- Perfect Forward Secrecy (PFS): temporary keys discarded after use, protecting past messages
- Open source code available for inspection
- Collects minimal data: does not store contacts, message content, or who you communicate with
- Run by non-profit, free from ads and trackers
- Offers anonymous messaging with usernames instead of phone numbers
- **Limitation:** Requires phone number for registration

**WhatsApp:**
- Uses Signal Protocol for encryption
- End-to-end encryption by default for messages, calls, photos, videos
- **Concerns:** Logs device info, contacts, IP address and shares with Meta
- 3.1+ billion monthly active users

**Telegram:**
- End-to-end encryption only in "secret chats" (not default)
- Standard chats encrypted only between device and Telegram servers
- Collects significant metadata (IP address, contacts, communication partners)

**Other Secure Options:**

| App | Key Feature |
|-----|-------------|
| Threema | Strongest metadata protection, anonymous IDs, no phone/email required |
| Session | No personal details required, decentralized message routing |
| Briar | Works offline, mesh networking for unreliable internet or high-risk environments |

**Recommendation:** Signal provides best balance of strong privacy without complexity for everyday use.

### Email Privacy Options

**Why Encrypted Email Matters:**
- Traditional providers like Gmail and Outlook can read emails
- Secure providers like ProtonMail and Tutanota use end-to-end encryption
- Provider cannot access email content

**ProtonMail:**
- Based in Switzerland (strong privacy laws)
- Uses PGP (Pretty Good Privacy) encryption standard
- AES 256-bit encryption
- Messages to non-ProtonMail users can be password protected
- Includes Proton Drive and Proton VPN access
- **Note:** Does NOT encrypt subject lines
- Starting price: EUR 3.99/month for paid plans

**Tutanota (Tuta):**
- Based in Germany
- Proprietary encryption encrypting subject lines as well as content
- AES 256 / RSA 2048 encryption
- No cookies on website
- Includes encrypted calendar and contact manager
- Already uses quantum-safe encryption
- Starting price: EUR 3/month

**Comparison:**

| Feature | ProtonMail | Tutanota |
|---------|------------|----------|
| Subject Line Encryption | No | Yes |
| Encryption Standard | PGP (open) | Proprietary |
| Interoperability | Works with other PGP users | Only encrypts with other Tutanota users |
| Location | Switzerland | Germany |

### What Encryption Means Practically

**End-to-End Encryption (E2EE):**
- Only sender and recipient can read message content
- Even service provider cannot access plaintext
- Messages encrypted on sender's device, decrypted on recipient's device

**In Transit vs At Rest:**
- In transit: Data protected while moving between devices
- At rest: Data protected while stored on servers
- Both are important; E2EE provides strongest protection

**Practical Considerations:**
- E2EE only works when both parties use the same service or compatible protocol
- Metadata (who contacted whom, when) may still be visible
- Backup and recovery: encrypted services make password recovery impossible; losing password means losing access

**Sources:**
- [CyberInsider: Best Secure Encrypted Messaging Apps 2026](https://cyberinsider.com/secure-encrypted-messaging-apps/)
- [ExpressVPN: Most Secure Messaging Apps 2026](https://www.expressvpn.com/blog/best-messaging-apps/)
- [Proton: ProtonMail vs Tutanota](https://proton.me/mail/proton-mail-vs-tutanota)
- [Cloudwards: Tutanota vs ProtonMail 2026](https://www.cloudwards.net/tutanota-vs-protonmail/)
- [NordVPN: Tuta vs ProtonMail 2026](https://nordvpn.com/blog/tutanota/)

---

## 5. Data Broker Exposure

### What Data Brokers Are

Data brokers collect, analyze, and process vast amounts of personal information from various sources:
- Social media (Facebook, LinkedIn, Instagram)
- Public records (court records, criminal records)
- Other third parties and data brokers
- Website tracking and cookies

They compile comprehensive profiles and sell this data to businesses for:
- Targeted advertising
- Background checks
- Credit assessments
- Marketing campaigns

**Australian Context:**
Australia has limited transparency around data broker operations. According to industry insiders, "Australia has super lax laws when it comes to what you can do with data."

### Current Australian Data Deletion Rights

**Current Limitations:**
- Australia does not currently recognise a right to delete personal data
- Despite 90% of Australians supporting laws for greater privacy control
- Federal Government passed limited privacy reforms in 2023
- Committed to implementing over 100 more, including right to delete

**Proposed Reforms:**
The Privacy Act Review Report proposes:
- Right to erasure modeled on EU GDPR
- Enhanced right of access
- If entity collected information from third party, they must notify the third party of erasure request
- Particularly important for data broker context

**Existing Protections (APP 11):**
- Entities must delete or de-identify information no longer needed
- If no requirement or justification for retention, entities must take reasonable steps to destroy or de-identify
- Individuals can lodge complaints with OAIC if organisations refuse to comply

### How to Request Deletion (OAIC Guidance)

1. **Identify Data Holders**
   - Search for your information on known data broker and people search sites
   - Note which sites have your data

2. **Locate Opt-Out Pages**
   - Look for "Opt Out", "Do Not Sell", "Privacy Request", "Right to Delete" pages
   - Usually found in footer or FAQ sections

3. **Submit Removal Requests**
   - Follow site-specific instructions
   - May require form completion or email
   - Some sites require identity verification

4. **Document Requests**
   - Keep records of all removal requests
   - Note dates and sites contacted

5. **Verify Removal**
   - Check back weeks/months later
   - Re-submit if information reappears

6. **Lodge OAIC Complaint if Refused**
   - Australians can lodge complaint with OAIC if organisation refuses to comply with Privacy Act

### People Search Sites

**Common Data Brokers:**
- Whitepages
- BeenVerified
- CheckPeople
- Intelius
- MyLife
- Nuwber
- PeopleFinders
- Radaris
- Spokeo
- ThatsThem

**Whitepages Opt-Out Process:**
1. Search for your name on Whitepages.com
2. Copy URLs for all listings
3. Visit Whitepages opt-out page
4. Paste URLs and click "Opt-out"
5. Verify record to remove and click "Remove me"
6. Select reason for removal
7. Provide phone number for verification call
8. Answer verification call promptly
9. For Whitepages Premium removal, submit support ticket

### Reducing Exposure

**Proactive Measures:**
- Use dedicated email for opt-out requests (protects main email)
- Check if site has your information before providing data for removal
- Repeat process approximately twice per year
- Data tends to resurface as brokers collect new data

**Paid Removal Services:**
Consumer Reports found EasyOptOuts and Optery to be among the most effective people-search data removal services.

**Sources:**
- [Digital Rights Watch: Australians Need Data Deletion Rights](https://digitalrightswatch.org.au/2025/10/16/your-data-their-rules-australians-need-data-deletion-rights/)
- [OAIC: Digital Platform Services Inquiry on Data Brokers](https://www.oaic.gov.au/engage-with-us/submissions/digital-platform-services-inquiry-march-2024-report-on-data-brokers-issues-paper)
- [Kaspersky: How to Remove Yourself from Data Brokers](https://www.kaspersky.com.au/blog/how-to-remove-yourself-from-data-brokers-people-search-sites/35356/)
- [Consumer Reports: Delete Information From People-Search Sites](https://www.consumerreports.org/electronics/personal-information/how-to-delete-your-information-from-people-search-sites-a6926856917/)
- [CHOICE: Data Brokers Investigation](https://www.choice.com.au/data-protection-and-privacy/data-collection-and-use/who-has-your-data/articles/data-broking-investigation)

---

## 6. Personal Security Practices

### Password Managers

**Why Use Password Managers:**
- Generate and store complex, unique passwords for every account
- Eliminates password reuse (major security risk)
- Encrypted vault protected by single master password
- Browser autofill reduces phishing risk

**Security Features to Look For:**
- AES 256-bit encryption with PBKDF2-HMAC-SHA512
- Two-factor authentication support
- Biometric login options
- Zero-knowledge architecture (provider cannot access your data)
- Password generator
- Secure password sharing

**Recommended Managers (2026):**
- NordPass (strong 2FA support, hardware security keys)
- 1Password
- Bitwarden
- RoboForm

### Two-Factor Authentication (2FA)

**Types of 2FA:**

| Type | Description | Security Level |
|------|-------------|----------------|
| SMS OTP | Code sent via text message | Lower (SIM swapping risk) |
| Authenticator App | Time-based code from app (Google Authenticator, Authy) | Good |
| Hardware Security Key | Physical USB key (YubiKey) | Highest |
| Biometric | Fingerprint or facial recognition | Good |

**Best Practices:**
1. Enable 2FA on all accounts, prioritizing email and financial accounts
2. Prefer authenticator apps over SMS where possible
3. Store backup codes in secure location (password manager or physical safe)
4. Keep backup codes separate from primary authentication method
5. Use hardware security key for highest-value accounts

**Effectiveness:**
- 2FA can thwart the vast majority of account takeover attempts even if password is compromised
- Hardware security keys provide strongest protection against phishing

### Phishing Awareness

**Current Threat Landscape (2025-2026):**
- Generative AI creates flawless, personalized phishing messages
- Attackers can mimic executive tone, clone voices/faces for vishing and deepfake scams
- Attacks more believable, harder to detect, easier to launch at scale
- FBI 2024: Phishing topped most reported cybercrimes (193,407 complaints)
- 91% of security breaches caused by phishing

**Red Flags to Identify Phishing:**
- Artificial urgency demanding immediate action
- Strange or unexpected requests
- Suspicious links (hover to check actual URL)
- Display name vs actual email address mismatch
- Generic greetings instead of personal name
- Poor grammar or spelling (less reliable with AI-generated content)
- Requests for login credentials or sensitive information

**Verification Steps:**
- Check sender's actual email address (not just display name)
- Hover over links before clicking to verify destination
- When in doubt, contact organisation directly through official channels
- Do not use phone numbers or links provided in suspicious message

**If You Click a Phishing Link:**
1. Isolate the device from network
2. Change compromised credentials immediately
3. Notify IT security or relevant administrator
4. Scan for malware
5. Monitor affected accounts for unusual activity
6. Document the incident

### Device Security

**Mobile Device Security:**
- Enable device encryption (default on modern iOS/Android)
- Use strong PIN/password or biometric lock
- Enable auto-lock after brief inactivity
- Keep operating system and apps updated
- Enable remote wipe capability (Find My iPhone, Find My Device)
- Install apps only from official stores
- Review app permissions regularly

**Computer Security:**
- Enable full-disk encryption (FileVault on Mac, BitLocker on Windows)
- Keep operating system and software updated
- Use reputable antivirus/anti-malware
- Enable firewall
- Use standard user account for daily use, admin for system changes
- Regular backups (3-2-1 rule: 3 copies, 2 different media, 1 offsite)

**VPN Usage:**
- 69% of people use VPNs on phones (2025 data)
- Encrypts internet traffic, especially important on public WiFi
- Hides IP address from websites and services
- Choose reputable provider with no-logs policy

**Sources:**
- [Password Manager: Best Password Managers with 2FA 2026](https://www.passwordmanager.com/best-password-managers-with-two-factor-authentication/)
- [Securden: Password Management Best Practices 2026](https://www.securden.com/blog/password-management-best-practices.html)
- [Adaptive Security: Phishing Awareness Training 2025](https://www.adaptivesecurity.com/blog/phishing-training-employees)
- [CISA: Teach Employees to Avoid Phishing](https://www.cisa.gov/audiences/small-and-medium-businesses/secure-your-business/teach-employees-avoid-phishing)
- [BitLyft: Phishing Attack Red Flags 2025](https://www.bitlyft.com/resources/phishing-attack-red-flags-complete-guide-to-spotting-email-scams-in-2025)

---

## 7. Australian Resources

### Office of the Australian Information Commissioner (OAIC)

**Website:** [oaic.gov.au](https://www.oaic.gov.au/)

**Role:**
- Independent statutory agency in Attorney-General's portfolio
- Ensures Australian Government agencies and organisations with annual turnover >$3 million follow Privacy Act 1988
- Investigates, conciliates, and awards damages for APP breaches
- Develops codes of practice for information privacy
- Publishes guidelines for organisations
- Handles individual privacy complaints

**Individual Rights Under Privacy Act:**
- Know why personal information is being collected
- Know how information will be used and disclosed
- Option to not identify yourself or use pseudonym (in certain circumstances)
- Request access to personal information held about you
- Request correction of inaccurate, out-of-date, incomplete, or misleading information
- Lodge complaint about privacy handling

**Recent Developments (December 2024):**
Privacy and Other Legislation Amendment Act 2024 (POLA Act):
- Enhanced privacy protections
- Expanded Information Commissioner enforcement powers
- New statutory tort for serious invasions of privacy

**How to Make a Complaint:**
1. First complain directly to the organisation/agency
2. If unresolved after 30 days, lodge complaint with OAIC
3. OAIC investigates and may conciliate
4. Outcomes can include compensation for financial or emotional harm

### Australian Cyber Security Centre (ACSC)

**Website:** [cyber.gov.au](https://www.cyber.gov.au/)

**Role:**
- Within Australian Signals Directorate (ASD)
- Drives cyber-resilience across Australian economy
- Provides information, advice, assistance on cyber threats
- Collaborates with business, government, community

**Key Resources:**
- Alerts and advisories on current threats
- Essential Eight security framework
- Gateway security guidance
- Small business cyber security guides

**Statistics (2024-25):**
- Responded to over 1,200 cyber incidents (11% increase year-on-year)
- Issued more than 1,700 alerts (83% surge from previous year)
- 187 notifiable breaches exposed personal data of up to 3.6 million Australians

**Australia's Cyber Security Strategy 2023-2030:**
- Horizon 1 (current): Strengthen foundations, address critical gaps
- Horizon 2 (2026): Scale cyber maturity across whole economy

**How to Report:**
- Report cyber incidents: [cyber.gov.au/report](https://www.cyber.gov.au/report)
- ReportCyber for cybercrime reporting

### Electronic Frontiers Australia (EFA)

**Website:** [efa.org.au](https://efa.org.au/)

**About:**
- Non-profit organisation established January 1994
- Represents Internet users concerned with online liberties and rights
- Independent of government and commerce
- Funded by membership subscriptions and donations

**Key Advocacy Areas:**
- **Privacy:** Fundamental human right; consent and control over information access
- **Encryption:** Vital for individuals and groups to safeguard security and privacy
- **Copyright Reform:** Advocate for updating outdated copyright laws for digital age
- **Surveillance:** Opposition to excessive government surveillance powers

**Activities:**
- Submissions to government inquiries
- Public campaigns and open letters
- Collaboration with Digital Rights Watch
- Education and awareness

### Privacy Act 1988 Rights

**Who Must Comply:**
- Australian Government agencies (and Norfolk Island administration)
- Private sector organisations with annual turnover more than $3 million
- Some smaller organisations handling health information or specific activities

**Australian Privacy Principles (APPs):**
13 principles governing personal information handling:
1. Open and transparent management of personal information
2. Anonymity and pseudonymity options
3. Collection of solicited personal information
4. Dealing with unsolicited personal information
5. Notification of collection
6. Use or disclosure of personal information
7. Direct marketing restrictions
8. Cross-border disclosure
9. Adoption, use, or disclosure of government identifiers
10. Quality of personal information
11. Security of personal information
12. Access to personal information
13. Correction of personal information

**Your Rights:**
- Request access to personal information (response within 30 days)
- Request correction of inaccurate information (no charge)
- Complain to organisation, then OAIC if unresolved
- Seek compensation through Commissioner or courts

**Penalties for Breaches:**
- Maximum penalties for serious/repeated breaches:
  - Up to AUD $10 million
  - 3x value of benefit obtained through misuse
  - 10% of annual domestic turnover
  - Whichever is greater

**Sources:**
- [OAIC: Your Privacy Rights](https://www.oaic.gov.au/privacy/your-privacy-rights)
- [OAIC: Rights and Responsibilities](https://www.oaic.gov.au/privacy/privacy-legislation/the-privacy-act/rights-and-responsibilities)
- [Australian Cyber Security Centre](https://www.cyber.gov.au/)
- [Electronic Frontiers Australia](https://efa.org.au/)
- [SecurePrivacy: Australia Privacy Act Compliance Guide](https://secureprivacy.ai/blog/australia-privacy-act-1988-compliance-guide)
- [Usercentrics: Australia Privacy Act and APPs Guide](https://usercentrics.com/knowledge-hub/australia-privacy-act-apps/)

---

## Quick Reference Checklist for Australian Families

### Immediate Actions (Do This Week)

- [ ] Audit smartphone app permissions (location, camera, microphone)
- [ ] Enable two-factor authentication on email and banking accounts
- [ ] Review social media privacy settings on Facebook/Instagram
- [ ] Change default router password and admin credentials
- [ ] Install a password manager (1Password, Bitwarden, NordPass)

### Short-Term Actions (This Month)

- [ ] Update all devices (phones, computers, router firmware)
- [ ] Enable WPA3 on home WiFi if supported
- [ ] Create separate guest network for IoT devices
- [ ] Delete unused apps and social media accounts
- [ ] Set up encrypted messaging (Signal) for family communication
- [ ] Search for family members on people search sites and begin opt-out requests

### Ongoing Practices

- [ ] Review privacy settings quarterly
- [ ] Keep software and apps updated
- [ ] Use unique passwords for every account (via password manager)
- [ ] Verify unexpected requests through official channels
- [ ] Back up important data regularly
- [ ] Repeat data broker opt-out process twice yearly

### Family Education

- [ ] Discuss phishing awareness with all family members
- [ ] Teach children about social media privacy
- [ ] Establish rules for sharing location and personal information online
- [ ] Create family protocol for reporting suspicious messages/emails

---

## Document Information

**Created:** January 2026
**Purpose:** Digital privacy and security guidance for Australian families
**Sources:** OAIC, ACSC, EFA, CISA, Consumer Reports, cybersecurity research
**Review Frequency:** Annually or when significant privacy law changes occur

---

*This document is for informational purposes only and does not constitute legal advice. For specific privacy concerns, consult the OAIC or seek professional legal counsel.*
