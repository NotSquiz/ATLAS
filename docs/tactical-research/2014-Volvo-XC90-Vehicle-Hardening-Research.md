# 2014 Volvo XC90 D5 - Vehicle Security and Emergency Preparedness Research

**Location:** Sunshine Coast, Queensland, Australia
**Vehicle:** 2014 Volvo XC90 D5 AWD (Turbo Diesel)
**Engine:** D5244T18 (2.4L 5-cylinder turbodiesel)
**Kerb Weight:** ~2,200kg
**Research Date:** January 2026

---

## Table of Contents

1. [Vehicle-Specific Vulnerabilities](#1-vehicle-specific-vulnerabilities)
2. [Hardening Options](#2-hardening-options)
3. [Emergency Preparedness](#3-emergency-preparedness)
4. [Maintenance for Reliability](#4-maintenance-for-reliability)
5. [Operational Use](#5-operational-use)
6. [Australian Suppliers](#6-australian-suppliers)
7. [Cost Summary](#7-cost-summary)

---

## 1. Vehicle-Specific Vulnerabilities

### 1.1 Keyless Entry / Relay Attacks

The 2014 XC90 (first generation, 2003-2014) is vulnerable to relay attacks, though with some caveats:

**How the attack works:**
- Thieves use relay devices that can capture key fob signals from up to 100 metres away
- The signal is amplified and transmitted to unlock the vehicle
- Keyless entry vehicles represent 48% of all thefts despite being only ~1% of vehicles on the road

**XC90-Specific Factors:**
- While relay attacks can unlock the vehicle, actually driving away is harder on Volvos
- The immobiliser requires a key registered through VIDA (Volvo's diagnostic software)
- Most thieves cannot access the VIDA programming required to register a new key
- The MAC-based authorisation on certain components adds another layer

**Risk Level:** MODERATE - Entry is possible, but driving away is more difficult than many other vehicles.

### 1.2 OBD Port Vulnerabilities

**The Threat:**
- Thieves can plug devices into the OBD-II port to:
  - Bypass ignition locks and immobilisers
  - Override the security system
  - Reprogram key fobs
  - Start the engine without the original key
- Victoria Police reports 1 in 5 stolen vehicles are taken via OBD port exploitation
- The attack can be executed quickly and discreetly (under 2 minutes)

**XC90 OBD Location:**
- Driver's side, under dashboard near steering column
- Standard OBD-II connector (16-pin)

### 1.3 CAN Bus Access Points

**Vulnerabilities:**
- CAN bus carries unencrypted messages between vehicle systems
- The 2014 model uses original CAN protocol with only 8-byte payloads (no encryption)
- Access points include:
  - OBD-II port (primary)
  - Headlight wiring harness (external access)
  - Tail light connectors
  - Door modules (if panels removed)

**Mitigation Priority:** HIGH - OBD port protection is the most practical intervention.

### 1.4 Key Fob Security

**2014 XC90 Key System:**
- Uses rolling code encryption (prevents simple signal cloning)
- However, relay attack captures the live signal, bypassing encryption
- No motion-activated sleep mode on older fobs (always transmitting)

---

## 2. Hardening Options

### 2.1 OBD Port Locks

**Recommended Products:**

| Product | Source | Price (AUD) | Features |
|---------|--------|-------------|----------|
| Autofidelity OBD Port Lock | autofidelity.com.au | ~$150-200 | Tamper-resistant steel, lifetime installation warranty |
| Auto Lines OBD2 Lock Kit | autolines.com.au | ~$80-120 | Two-piece design, specialty security screws, fits 1996+ |
| Street Sound Vision OBD Lock | streetsoundvision.com.au | ~$100 | Universal fit, security key included |

**Installation Notes:**
- DIY installation possible (15-30 minutes)
- Professional installation recommended for warranty
- Ensure you keep the removal key in a secure location (not in the car)

### 2.2 Steering Wheel Locks

**Recommended for XC90 (2002-2014):**

| Product | Type | Price (AUD) | Source |
|---------|------|-------------|--------|
| Mechanical Interceptor | Steering shaft | ~$200-300 | aleksracing.com |
| Python Steering Lock | Wheel lock | ~$150-250 | aleksracing.com |
| UKB4C Twin Bar | Wheel lock | ~$80-120 | Amazon AU/UK |

**Interceptor Advantages:**
- Mounts on steering shaft (near pedals)
- No traditional keyhole (resistant to lock-picks)
- Solid stainless steel construction
- Works at temperatures down to -58°F
- More difficult to defeat than standard wheel locks

### 2.3 Kill Switches

**Types Suitable for D5 Diesel:**

**1. Fuel Pump Kill Switch (Recommended)**
- Interrupts electrical circuit to fuel pump
- Engine cranks but won't start/run
- Location: Hidden toggle under dash, inside centre console, or under rear seat
- Cost: $20-50 DIY / $150-250 professional install
- Effectiveness: HIGH for opportunistic theft

**2. Ignition Kill Switch**
- Grounds the coil, preventing spark (less relevant for diesel)
- For diesel: interrupt glow plug relay or ECU power
- Cost: $30-80 DIY / $150-300 professional install

**3. Battery Kill Switch**
- Disconnects battery from electrical system
- Prevents all electrical functions
- More inconvenient for daily use
- Cost: $20-40 DIY

**Hidden Installation Locations:**
- Inside cigar lighter receptacle (hollow out element)
- Behind A-pillar trim
- Under rear seats (requires disassembly to find)
- Inside door pocket liner
- Magnetic reed switch (requires magnet to activate - no visible switch)

**Sequential Switch Option:**
- Multiple switches in specific order
- Significantly harder for thieves to discover and defeat

### 2.4 Faraday Pouches for Key Fobs

**Australian Suppliers:**

| Product | Source | Price (AUD) | Features |
|---------|--------|-------------|----------|
| Aus Security Products | aussecurityproducts.com.au | $25-40 | Water-resistant, blocks 100% of signals |
| SecurityBase Military-Grade | securitybase.com.au | $35-50 | 85dB shielding, MIL-STD-188-125 compliant |
| Sentriwise Faraday Pouch | sentriwise.com.au | $20-35 | Free express shipping Australia-wide |
| The Spy Store Pouch | thespystore.com.au | $25-40 | Dual layer, fits 2 fobs, 1300 681 609 support |
| Pacsafe RFID Blocking | pacsafe.com | $30-60 | Blocks up to 3GHz, premium brand |

**Usage Notes:**
- Place fob in the Faraday-lined back pocket (not front)
- Don't store sharp objects with the pouch (can damage shielding)
- Test effectiveness: fob in pouch should not unlock car from 1m away

### 2.5 Aftermarket Alarm Systems

**Recommended Systems Compatible with Volvo:**

| System | Features | Price Range (AUD) |
|--------|----------|-------------------|
| **Viper 5305V** | 2-way paging, 1/4 mile range, entry-level price | $300-500 |
| **Viper 5906VR** | 1.5km range, remote start, smartphone integration | $600-900 |
| **Pandora DXL Series** | 868MHz anti-clone, GPS tracking, ADR tag immobiliser | $800-1,500 |
| **Autowatch** | Premium security focus, less bells and whistles | $400-800 |

**Installation Considerations:**
- Professional installation recommended (~$200-400 labour)
- Volvo factory alarm can be disabled/integrated
- If key is chipped, bypass module required for remote start
- Directed Electronics brands (Viper, Python, Clifford) have best Volvo compatibility data

### 2.6 GPS Tracking Options

**Australian GPS Tracker Options:**

| Tracker | Type | Battery | Subscription | Features |
|---------|------|---------|--------------|----------|
| **Solid GPS** | Magnetic/portable | 3-12 months | $6.99/month | Movement alerts, 2-10 min updates, police dashboard sharing |
| **Black Knight GPS** | Hidden hardwire | Backup battery | $13.99/month | Non-removable SIM, anti-tamper, real-time tracking |
| **GPS Tracking Australia SU-2700** | 4G Cat M1 | Varies | Contact for pricing | Recovery mode, daily/live updates |
| **SPOT Trace** | Satellite | Solar/DC | ~$15/month | Works in remote areas (Globalstar), no cellular needed |

**Covert Placement Options:**
- Behind dashboard trim
- Inside spare wheel well
- Under rear seat cushion
- In engine bay (weatherproof housing required)
- Magnetic mount inside bumper

**Budget Alternative - Apple AirTag / Samsung SmartTag:**
- Cost: $45-60 per unit
- No subscription
- Less frequent updates than dedicated GPS
- Thieves with iPhones may receive "unknown AirTag" alerts
- Recommendation: Use 1-2 AirTags as backup to primary GPS tracker

---

## 3. Emergency Preparedness

### 3.1 Vehicle Emergency Kit for Australian Conditions

**Core Kit Contents:**

| Category | Items | Notes |
|----------|-------|-------|
| **Respiratory Protection** | 2x P2 charcoal valved respirators | For bushfire smoke |
| **Eye Protection** | Clear safety goggles (flame retardant) | Amber for low visibility |
| **Thermal Protection** | 2x wool blankets | Smother fires, radiant heat protection |
| **Hand Protection** | Leather riggers gloves | Heat resistant |
| **Burn Treatment** | Burn dressings, hydrogel | Rapidly cool injuries |
| **Communication** | Hand-crank radio/torch combo | No batteries required |
| **Visibility** | High-vis vest, torch with spare batteries | Night emergencies |
| **Documentation** | Photocopies of IDs, insurance, rego | In waterproof bag |

**Recommended Kits:**
- Survival Supplies Australia Bushfire Kit: $150-300
- Emergency BK Vehicle Kit (4-6 people): $200-350
- Fire and Rescue Australia Vehicle Kit: $180-280

### 3.2 Recovery Gear for XC90 (~2,200kg)

**Recovery Rating:** Mid-weight SUV - 8,000kg rated gear sufficient, 11,000kg recommended for margin.

**Essential Recovery Kit:**

| Item | Specification | Price (AUD) | Source |
|------|---------------|-------------|--------|
| **MAXTRAX Recovery Boards** | Classic or Mini | $290-340/pair | maxtrax.com.au |
| **Kinetic Recovery Rope** | 8,000-11,000kg, 9m | $150-250 | George4x4, Ironman 4x4 |
| **Soft Shackles** | 8,000-11,000kg (x2) | $40-80 | Replaces steel shackles (safer) |
| **Snatch Strap** | 8,000kg, 9m | $80-120 | Anaconda, BCF |
| **Tree Trunk Protector** | 3m, 8,000kg | $40-60 | Protects trees, anchor point |
| **Recovery Dampener** | Any rated | $40-80 | Absorbs energy if strap fails |
| **Air Compressor** | 12V, 150 PSI min | $150-300 | Tyre reinflation |
| **Tyre Deflator Kit** | Adjustable | $30-60 | Quick deflation for sand/mud |
| **Tyre Repair Kit** | Plug kit + patches | $40-80 | Puncture repair |

**Recommended Kits:**
- MAXTRAX Recovery System: From $450
- Saber Offroad 8K Kinetic Kit: ~$350
- Ironman 4x4 Recovery Kit: ~$400

### 3.3 Communication Equipment

**UHF CB Radio:**
- Emergency Channels: 5 and 35 (duplex)
- Convoy Channel: 10 (4WD clubs, national parks)
- Road Channels: 40 (trucks), 29 (road safety)
- Range: 30-40km line of sight (extendable via repeaters)
- Recommended: GME TX3350 or Uniden UH5060

**Satellite Communication:**

| Device | Type | Coverage | Subscription | Price (AUD) |
|--------|------|----------|--------------|-------------|
| **Garmin inReach Messenger Plus** | 2-way messaging | Global (Iridium) | From $20/month | $500-700 |
| **SPOT Gen4** | 1-way + SOS | Near-global (Globalstar) | From $15/month | $200-300 |
| **PLB (Personal Locator Beacon)** | SOS only | Global (SARSAT) | No subscription | $350-500 |
| **Satellite Phone** | Voice + data | Global (Iridium/Thuraya) | From $50/month | $1,200-2,500 |

**Recommendation:**
- Minimum: PLB (no subscription, SOS-only)
- Optimal: Garmin inReach + UHF CB combination
- For remote Outback: Satellite phone + PLB

### 3.4 Water and Supplies Storage

**Water Requirements:**
- Minimum: 4L per person per day
- Family of 4 for 3 days: 48L minimum
- Storage: 20L jerry cans (water-rated) or rigid water containers
- Consider water bladder in cargo area for bulk storage

**Emergency Food:**
- Minimum 3-day supply of non-perishable food
- Energy bars, canned goods, dried foods
- Don't forget can opener and utensils

**Climate Considerations (Sunshine Coast):**
- Summer temps regularly exceed 35°C
- Store water out of direct sunlight
- Rotate supplies every 6-12 months
- Include electrolyte sachets for heat exhaustion

### 3.5 First Aid Kit

**Recommended Contents:**

| Module | Key Items |
|--------|-----------|
| **Standard First Aid** | Bandages, gauze, antiseptic, scissors, tweezers, pain relief |
| **Burns Module** | Burn gel, burn dressings, hydrogel sachets |
| **Snake Bite Kit** | Compression bandages (pressure indicator), markers, emergency guide |
| **Trauma Module** | Tourniquet, Israeli bandage, chest seal |
| **Personal Medications** | Prescription meds, EpiPen if allergic, asthma inhalers |

**Recommended Kits:**
- St John Ambulance Snake Bite Kit: $35-50
- MAXTRAX Snake Bite Kit: $45-60
- Aero Healthcare Modular Kit: $100-200

**Placement:**
- Under front passenger seat (accessible to all)
- Ensure driver can reach without unbuckling
- Secondary kit in rear cargo area

### 3.6 Fire Extinguisher

**Recommended Type:** ABE Dry Chemical Powder

| Size | Use Case | Price (AUD) |
|------|----------|-------------|
| 1kg ABE | Minimum for passenger vehicle | $30-50 |
| 1.5kg ABE | Recommended for SUV | $40-60 |
| 2.5kg ABE | For touring/4WD use | $60-90 |

**Mounting:**
- Under front passenger seat (bracket required)
- Rear cargo area (heavy-duty bracket for larger units)
- Use short self-drilling pan head screws
- Check annually, replace after 5 years or if fails inspection

**Australian Standards:**
- Must comply with AS 1841
- No legal requirement for private vehicles (but highly recommended)
- Annual service recommended

**Suppliers:**
- Fire Extinguisher Online: fireextinguisheronline.com.au
- Fire One: fire-one.com.au
- Repco, Supercheap Auto (basic models)

---

## 4. Maintenance for Reliability

### 4.1 Common D5 Diesel Failure Points

**Priority Maintenance Items:**

| Component | Failure Mode | Prevention | Cost to Fix |
|-----------|--------------|------------|-------------|
| **DPF (Diesel Particulate Filter)** | Clogging from short trips | Regular highway driving, DPF regeneration cycles | $2,000-4,000 |
| **Fuel Injectors** | Premature failure (known issue in some serial numbers) | Quality fuel, regular servicing | $500-800 per injector |
| **Turbocharger** | Seal/actuator wear | Regular oil changes, avoid hard stops after highway driving | $2,500-4,500 |
| **Timing Belt** | Catastrophic failure if snaps | Replace every 150,000km or 10 years | $800-1,200 |
| **Auxiliary Belt** | Can wrap around timing belt causing damage | Replace every 100,000km | $200-400 |
| **Swirl Flaps** | Actuator arms break, can damage engine | Preventative replacement | $400-800 |
| **Fuel Filter Housing** | Plastic ears/connectors crack | Careful during filter changes, use genuine parts | $200-400 |
| **Cooling Fan** | Failure leads to overheating | Monitor temps, check fan operation | $400-800 |
| **High-Pressure Fuel Pump** | Rough idling, decreased efficiency | Quality fuel, regular servicing | $1,500-2,500 |

### 4.2 Critical Spare Parts to Carry

**Essential Spares:**

| Part | Reason | Approx Cost |
|------|--------|-------------|
| Fuel filter + O-rings | Known weak point, roadside replacement possible | $40-80 |
| Serpentine/auxiliary belt | Can fail unexpectedly, easy replacement | $60-120 |
| Coolant (2L) | Overheating prevention | $30-50 |
| Engine oil (2L) | D5 can consume oil, especially when older | $30-60 |
| Fuses (assorted) | Electrical faults | $10-20 |
| Hose clamps | Emergency repairs | $10-20 |
| Duct tape, cable ties | Universal fix-it supplies | $15-25 |

**Tools to Carry:**
- Basic socket set (10mm-19mm)
- Screwdriver set (Phillips, flathead)
- Pliers (standard and needle-nose)
- Adjustable wrench
- Torchlight (headlamp preferred)
- Jumper cables
- Tow rope/strap

### 4.3 Fuel Considerations

**Diesel Storage:**

| Regulation | Queensland/Australia |
|------------|---------------------|
| Maximum jerry cans | 250L total (combined vehicle + trailer) |
| Diesel classification | Combustible (not dangerous good like petrol) |
| Container requirements | AS/NZS 2906:2001 approved |
| Mounting | Can be mounted externally (unlike petrol) |
| Shelf life | 6-12 months in cool, dry conditions |

**Range Extension Options:**

1. **Jerry Cans (20L each)**
   - Pros: Flexible, removable, inexpensive
   - Cons: Manual transfer, roof weight affects handling
   - Capacity: 4x 20L = 80L extra range (~600-700km additional)

2. **Long Range Tank Replacement**
   - Pros: Lower centre of gravity, seamless integration
   - Cons: Expensive ($1,500-3,500 + installation), permanent
   - Capacity: Typically 90-140L total (vs ~70L stock)
   - **Note:** Must not exceed GVM - factor in all accessories

**XC90 D5 Fuel Economy:**
- Highway: ~7-8L/100km
- Mixed: ~9-11L/100km
- Stock tank (~70L): ~700-900km highway range
- With 80L extra: ~1,500km+ range

---

## 5. Operational Use

### 5.1 Escape Route Planning

**Sunshine Coast Specific Resources:**

| Resource | URL |
|----------|-----|
| Sunshine Coast Disaster Hub | disasterhub.sunshinecoast.qld.gov.au |
| QLD Fire Department Incidents | fire.qld.gov.au/Current-Incidents |
| Get Ready Queensland | getready.qld.gov.au/plan |

**Planning Principles:**
1. Identify multiple evacuation routes (primary may be blocked by smoke/fire)
2. Know Neighbourhood Safer Places (last resort shelter)
3. Keep physical maps (don't rely on phone/GPS)
4. Mark fuel stations on routes
5. Plan for pets and livestock
6. Develop household plan with all family members

**Key Actions:**
- Download council local evacuation procedures
- Check bushfire danger ratings daily in fire season (Sept-March)
- Know the difference between:
  - Watch and Act (prepare to leave)
  - Emergency Warning (leave immediately)
  - Directed Evacuation (ordered by District Disaster Coordinator)

### 5.2 Fuel Management

**Pre-Trip:**
- Fill tank before entering remote areas
- Calculate fuel requirements: distance / economy + 30% reserve
- Identify fuel stops on route
- Carry jerry cans for trips exceeding 500km from reliable fuel

**During Trip:**
- Top up at every opportunity in remote areas
- Monitor fuel economy for early warning of issues
- Record fuel consumption to detect problems

### 5.3 Tire Considerations

**Stock Sizes (2014 XC90):**
- 235/60R18 (common)
- 255/50R19
- 255/45R20

**All-Terrain Options Confirmed to Fit:**

| Tire | Size | Notes |
|------|------|-------|
| Hankook Dynapro ATM | 235/65R17, 245/65R17 | Owner tested, slightly larger |
| Nokian Rotiiva AT | 245/65R17 | Aramid sidewalls, rock ejector tread |
| General Grabber AT2/AT3 | 235/65R17 | Proven on XC90 in mud, sand, snow |
| Cooper AT3 | 235/60R18 | Good all-rounder |
| Continental TerrainContact AT | 235/60R18 | Highway-biased AT |

**Notes:**
- Larger sizes (245/65R17) may require speedometer calibration
- Keep all 4 tires same size/wear for AWD system health
- Rotate regularly to maintain even wear
- A/T tires will be slightly noisier than highway tires

### 5.4 Towing Capacity

**2014 XC90 D5 Specifications:**

| Specification | Value |
|---------------|-------|
| Braked towing capacity | 2,250 kg |
| Unbraked towing capacity | 750 kg |
| Towball load | 225 kg (10% of trailer weight) |
| Hitch type | Class 3, 2" square profile |
| Max tongue weight | ~225 kg |

**Notes:**
- Capacity reduces with passenger load (6 passengers = 800kg tow limit)
- Genuine Volvo hitch kit available (Kit088)
- Consider trailer brakes mandatory for loads over 750kg
- Electric brake controller installation recommended

**Suitable Trailers:**
- Small camper trailers (under 2,000kg)
- Box trailers (under 750kg unbraked, under 2,000kg braked)
- Boat trailers (check combined weight)
- NOT suitable for large caravans (2,500kg+)

---

## 6. Australian Suppliers

### 6.1 Security Equipment

**Sunshine Coast Area:**

| Business | Services | Contact |
|----------|----------|---------|
| **Coastal Auto Systems** | Alarms, immobilisers, GPS | coastalautosystems.com.au |
| **Smart Automotive Technologies** | Car alarms, dash cams, keyless entry | 07 5442 4833, smartautotech.com.au |
| **Mobile Auto Electrician Sunshine Coast** | Alarms, GPS, immobilisers (mobile service) | autoelectriciansunshinecoast.com.au |
| **Anthony Phelps Mobile Auto Electrics** | General auto electrical, Maroochydore | Contact via Google |
| **Harmac Automotive** | Auto electrical specialists | harmacauto.com.au |

**National Online:**

| Supplier | Products | Website |
|----------|----------|---------|
| Autofidelity | OBD locks (Melbourne-based) | autofidelity.com.au |
| Auto Lines Australia | OBD locks, security | autolines.com.au |
| SecurityBase | Faraday pouches | securitybase.com.au |
| Frankies Auto Electrics | Viper systems | frankiesautoelectrics.com.au |

### 6.2 Recovery Gear

| Supplier | Products | Website |
|----------|----------|---------|
| MAXTRAX | Recovery boards, straps, kits | maxtrax.com.au |
| Ironman 4x4 | Full recovery range | ironman4x4.com.au |
| ARB | Premium recovery gear | arb.com.au |
| Anaconda | Snatch straps, basic gear | anacondastores.com |
| BCF | Recovery gear, camping | bcf.com.au |
| George4x4 | Snatch straps, soft shackles | george4x4.com.au |
| Sparesbox | MAXTRAX, accessories | sparesbox.com.au |

### 6.3 GPS Tracking

| Supplier | Products | Website |
|----------|----------|---------|
| Solid GPS | Vehicle trackers | solidgps.com |
| Black Knight GPS | Anti-theft trackers | marks4wd.com |
| GPS Tracking Australia | 4G trackers | gpstrackingaustralia.com.au |
| Keep Track GPS | SPOT Trace satellite | keeptrackgps.com.au |

### 6.4 Emergency/Safety

| Supplier | Products | Website |
|----------|----------|---------|
| St John Ambulance | First aid kits | shop.stjohn.org.au |
| Survival Supplies Australia | Bushfire kits, snake bite kits | survivalsupplies.com.au |
| Fire Extinguisher Online | Vehicle extinguishers | fireextinguisheronline.com.au |
| Emergency BK | Vehicle emergency kits | emergencybk.com.au |
| TACMED Australia | Trauma/snake bite kits | tacmedaustralia.com.au |

### 6.5 Communication

| Supplier | Products | Website |
|----------|----------|---------|
| GME | UHF radios | gme.net.au |
| Uniden | UHF radios | uniden.com.au |
| Garmin | inReach satellite messengers | garmin.com/en-AU |
| Adventure Safety | PLBs, satellite devices | adventuresafety.com.au |

---

## 7. Cost Summary

### 7.1 Security Hardening (Prioritised)

| Priority | Item | Cost (AUD) |
|----------|------|------------|
| 1 | Faraday pouch (x2) | $50-80 |
| 2 | OBD port lock | $100-200 |
| 3 | Steering wheel lock (Interceptor) | $200-300 |
| 4 | Kill switch (professional install) | $150-250 |
| 5 | GPS tracker + 1yr subscription | $200-400 |
| 6 | Full alarm system (installed) | $500-1,200 |

**Minimum Security Package:** $350-530 (items 1-3)
**Comprehensive Security Package:** $1,200-2,430 (all items)

### 7.2 Emergency Preparedness

| Category | Cost Range (AUD) |
|----------|------------------|
| Bushfire emergency kit | $150-350 |
| Recovery gear (basic) | $400-600 |
| Recovery gear (comprehensive) | $800-1,200 |
| First aid kit (with snake bite) | $100-200 |
| Fire extinguisher + mount | $50-100 |
| UHF CB radio | $150-400 |
| Satellite messenger/PLB | $200-700 |
| Water storage (40L capacity) | $50-100 |

**Minimum Emergency Package:** $700-1,050
**Comprehensive Emergency Package:** $1,900-3,050

### 7.3 Maintenance/Reliability

| Item | Cost (AUD) |
|------|------------|
| Spare parts kit | $150-300 |
| Tool kit | $100-200 |
| Fuel jerry cans (4x 20L) | $150-250 |
| Long range tank (alternative) | $1,500-3,500 installed |

---

## Quick Reference Checklist

### Daily Security Habits
- [ ] Store key fob in Faraday pouch when at home
- [ ] Keep fob away from front door/windows
- [ ] Use steering lock for overnight parking
- [ ] Check OBD port lock is secure
- [ ] Verify GPS tracker is reporting (phone check)

### Pre-Trip Checklist
- [ ] Full fuel tank
- [ ] Check all fluid levels
- [ ] Tire pressure (including spare)
- [ ] Recovery gear accessible
- [ ] First aid kit stocked
- [ ] Fire extinguisher charged (green indicator)
- [ ] Communication devices charged
- [ ] Water supplies fresh
- [ ] Emergency contacts documented
- [ ] Route planned with alternatives

### Seasonal Maintenance
- [ ] Check DPF (avoid excessive short trips)
- [ ] Service fuel filter annually
- [ ] Rotate spare parts stock
- [ ] Test fire extinguisher (check gauge)
- [ ] Refresh water supplies
- [ ] Review evacuation routes before fire season

---

## References and Further Reading

**Security:**
- [RACV - OBD Port Lock Guide](https://www.racv.com.au/royalauto/transport/car-safety-security/prevent-push-start-car-theft-obd-lock.html)
- [Volvo Owners Club - Keyless Theft Discussion](https://www.volvoforums.org.uk/showthread.php?t=318597)
- [Kill Switch Installation Guide](https://dashcameras.net/car-kill-switch/)

**Emergency Preparedness:**
- [CFA Fire Ready Kit](https://www.cfa.vic.gov.au/plan-prepare/before-and-during-a-fire/fire-ready-kit)
- [Get Ready Queensland](https://www.getready.qld.gov.au/plan)
- [Sunshine Coast Council Disaster Hub](https://disasterhub.sunshinecoast.qld.gov.au/)

**Vehicle Maintenance:**
- [D5 Engine Reliability - Oz Volvo](https://ozvolvo.org/d/9604-high-mile-d5-engine-reliability)
- [XC90 Fuel Filter - Volvo Forums](https://www.volvoforums.org.uk/showthread.php?t=273012)

**Recovery and Touring:**
- [MAXTRAX Recovery Systems](https://maxtrax.com.au/collections/recovery-systems)
- [Fuel Carrying Guide - Unsealed 4x4](https://unsealed4x4.com.au/guide-to-fuel-carrying-options/)
- [Australian Fuel Storage Regulations](https://www.festanks.com.au/blog/australian-fuel-storage-regulations/)

---

*Document compiled January 2026. Prices and availability subject to change. Always verify current specifications with suppliers before purchase.*
