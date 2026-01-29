# DIY Security Electronics - Practical Build Guide

**Compiled from publicly available maker, ham radio, and open-source security resources**

---

## Table of Contents
1. [RF Detection Builds](#1-rf-detection-builds)
2. [Motion/Intrusion Detection Systems](#2-motionintrusion-detection-systems)
3. [Camera Systems (Local-Only)](#3-camera-systems-local-only)
4. [Communication Builds](#4-communication-builds)
5. [Power Independence](#5-power-independence)
6. [Sensor Integration Platform](#6-sensor-integration-platform)
7. [Australian Suppliers](#7-australian-suppliers)

---

## 1. RF Detection Builds

### 1.1 Simple Wideband RF Detector Circuit

**Purpose:** Detect hidden wireless devices (cameras, microphones, trackers) emitting RF signals.

#### Option A: Analog Devices MAX2015-Based Detector (100MHz - 3GHz)

**Source:** [Analog Devices Design Note](https://www.analog.com/en/resources/design-notes/circuit-detects-and-locates-hidden-rf-bugs.html)

**Performance:**
- Frequency range: 100MHz to 3000MHz
- Sensitivity: -35dBm (0.32uW)
- Sounds buzzer alarm when RF detected

**Components List:**
| Component | Part Number | Qty | Est. Cost (AUD) |
|-----------|-------------|-----|-----------------|
| Log Detector IC | MAX2015 | 1 | $15 |
| Comparator | MAX9075 | 1 | $5 |
| Buzzer (piezo) | - | 1 | $3 |
| RF Connector (SMA) | - | 1 | $5 |
| Capacitors (assorted) | 10pF-100nF | 10 | $5 |
| Resistors (assorted) | - | 10 | $3 |
| PCB or Protoboard | - | 1 | $5 |
| 9V Battery + Clip | - | 1 | $5 |
| Enclosure | - | 1 | $10 |
| **Total** | | | **~$56** |

**How It Works:**
The MAX2015 log detector senses RF signals at pin INHI and produces an output voltage proportional to the power level (0.5V to 2.0V range). The comparator triggers the buzzer when signal exceeds threshold.

**Location Finding Modification:**
Replace MAX9075 comparator with MAX4480 amplifier configured for gain of 1.5. This amplifies the output (0.75V to 3.0V) allowing you to locate bugs by following increasing signal strength.

**Skill Level:** Intermediate (SMD soldering required)

---

#### Option B: Simple FET-Based Wideband Detector

**Source:** [Homemade Circuits - RF Detector](https://www.homemade-circuits.com/2-simple-rf-detector-circuits-explored/)

**Performance:**
- Frequency range: Up to 100MHz (adjustable via coil)
- Simple construction, beginner-friendly

**Components List:**
| Component | Value/Type | Qty | Est. Cost (AUD) |
|-----------|------------|-----|-----------------|
| FET Transistor | 2N3819 or BF245 | 1 | $2 |
| LED (red or green) | 3mm | 1 | $0.50 |
| Resistor | 1k, 10k | 2 | $0.50 |
| Capacitor | 100pF | 1 | $0.50 |
| Coil L1 | See table below | 1 | $3 |
| Antenna (telescopic) | ~15cm | 1 | $5 |
| 9V Battery + Clip | - | 1 | $5 |
| Enclosure | - | 1 | $10 |
| **Total** | | | **~$27** |

**Coil Selection Table:**
| Target Frequency | Turns | Wire Gauge | Diameter |
|------------------|-------|------------|----------|
| 30-50 MHz | 12 | 22 AWG | 6mm |
| 50-100 MHz | 8 | 22 AWG | 6mm |
| 100-150 MHz | 5 | 22 AWG | 6mm |

**Wiring:**
```
Antenna --> 100pF --> Gate (FET)
                      |
                      Drain --> 1k --> LED --> +9V
                      |
                      Source --> 10k --> GND
                      |
                      L1 (parallel to Source-GND)
```

**Skill Level:** Beginner

---

#### Option C: 555 Timer + Schottky Diode Detector

**Source:** [Electronics For You - RF Signal Detector](https://www.electronicsforu.com/electronics-projects/rf-signal-detector)

**Components List:**
| Component | Value/Type | Qty | Est. Cost (AUD) |
|-----------|------------|-----|-----------------|
| IC | NE555 | 1 | $1 |
| IC Socket | 8-pin DIP | 1 | $0.50 |
| Schottky Diode | 1N5711 or BAT85 | 1 | $1 |
| Capacitors | 10nF, 100nF, 10uF | 3 | $2 |
| Resistors | 10k, 100k, 1M | 3 | $1 |
| LED | 3mm | 1 | $0.50 |
| Buzzer | 5V piezo | 1 | $3 |
| Antenna (wire) | 15cm | 1 | $0 |
| 9V Battery | - | 1 | $5 |
| **Total** | | | **~$14** |

**Skill Level:** Beginner

---

### 1.2 RTL-SDR Surveillance Detection Setup

**Purpose:** Wideband spectrum analysis to identify unknown RF transmissions in your environment.

**Source:** [RTL-SDR.com](https://www.rtl-sdr.com/)

#### Hardware Requirements

| Component | Description | Est. Cost (AUD) |
|-----------|-------------|-----------------|
| RTL-SDR V3 Dongle | RTL2832U + R820T2 tuner | $45 |
| Wideband Antenna | Discone or planar disk | $50-100 |
| USB Extension Cable | Shielded, 2m | $10 |
| Ferrite Chokes | Clip-on, USB noise reduction | $10 |
| **Total** | | **~$115-165** |

**Frequency Coverage:** 24MHz to 1.766GHz (with direct sampling for HF)

#### Software Options

**1. Khanfar Spectrum Analyzer Tools**
- Full Spectrum RTL-SDR Sweeper for wideband spectrum analysis
- Produces spectrum sweep over large bandwidth by rapidly re-tuning
- Automated signal detection and analysis reporting
- Supports RTL-SDR, Airspy, HackRF

**2. SDR# with Fast Scanner Plugin**
- Wide band scanning through ~2MHz chunks
- Automatically tunes to active signals
- Good for monitoring specific frequency ranges

**3. Freqwatch (Linux)**
- Uses rtl_power for wide spectrum scanning
- Automatically records active signals to database
- Supports multiple RTL-SDR dongles simultaneously
- GitHub: [shajen/rtl-sdr-scanner](https://github.com/shajen/rtl-sdr-scanner)

#### Frequency Scanning Procedure

1. **Baseline Scan:**
   ```bash
   rtl_power -f 24M:1700M:1M -g 50 -i 1 -e 1h baseline.csv
   ```
   This scans 24MHz-1700MHz in 1MHz steps, capturing baseline RF environment.

2. **Analyze Results:**
   Use heatmap.py to visualize: `python heatmap.py baseline.csv baseline.png`

3. **Identify Anomalies:**
   Compare subsequent scans to baseline. Look for:
   - Signals not associated with known devices (WiFi routers, cordless phones)
   - Intermittent transmissions
   - Signals in unusual frequency ranges

4. **Common Surveillance Device Frequencies:**
   | Device Type | Frequency Range |
   |-------------|-----------------|
   | Cheap wireless cameras | 900MHz, 1.2GHz, 2.4GHz |
   | GSM bugs | 850/900/1800/1900 MHz |
   | WiFi-based devices | 2.4GHz, 5GHz |
   | GPS trackers | 850/1800/1900 MHz (cellular) |
   | Bluetooth bugs | 2.4GHz |

#### Building a Wideband Discone Antenna

**Source:** [Instructables Discone Build](https://www.instructables.com/Discone/)

**Performance:** 25MHz to 1700MHz+ reception

**Materials:**
| Item | Description | Est. Cost (AUD) |
|------|-------------|-----------------|
| Aluminum Rods | 6mm diameter, 8x 60cm | $30 |
| Aluminum Sheet | For disc, 30cm diameter | $15 |
| SO-239 Connector | Chassis mount | $8 |
| Coax Cable | RG58, 10m | $20 |
| Mounting Hardware | U-bolts, brackets | $15 |
| PVC Pipe | For center support | $10 |
| **Total** | | **~$98** |

**Dimensions (for 130MHz lower limit):**
- Disc diameter: 58cm
- Cone element length: 58cm
- Cone angle: 45 degrees
- 8 cone elements evenly spaced

**Skill Level:** Intermediate

---

## 2. Motion/Intrusion Detection Systems

### 2.1 ESP32 PIR Sensor Network

**Purpose:** Distributed motion detection with wireless alerts.

**Sources:**
- [Random Nerd Tutorials - ESP32 PIR](https://randomnerdtutorials.com/esp32-pir-motion-sensor-interrupts-timers/)
- [Cytron - Home Security with ESP32](https://www.cytron.io/tutorial/home-security-system-with-esp32)

#### Single Node Components

| Component | Part Number | Qty | Est. Cost (AUD) |
|-----------|-------------|-----|-----------------|
| ESP32 DevKit | ESP32-WROOM-32 | 1 | $15 |
| PIR Sensor | HC-SR501 | 1 | $5 |
| Level Shifter | Bi-directional 3.3V/5V | 1 | $3 |
| Resistor | 1k (protection) | 1 | $0.10 |
| Jumper Wires | Assorted | 10 | $3 |
| USB Cable | Micro-USB | 1 | $5 |
| Enclosure | Weatherproof IP65 | 1 | $15 |
| **Per Node Total** | | | **~$46** |

#### Wiring Diagram

```
HC-SR501 PIR Sensor          ESP32
+------------------+         +------------------+
| VCC  |-----------+-------->| 5V (or VIN)      |
| OUT  |----[1k]---+-------->| GPIO 14          |
| GND  |-----------+-------->| GND              |
+------------------+         +------------------+

Note: HC-SR501 requires 4.8V-20V. Do NOT power from 3.3V.
The 1k resistor protects the ESP32 GPIO from 5V logic.
For production use, add a proper 5V→3.3V level shifter.
```

#### Arduino Code (Single Node with Telegram Alert)

```cpp
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <UniversalTelegramBot.h>

// WiFi credentials
const char* ssid = "YOUR_SSID";
const char* password = "YOUR_PASSWORD";

// Telegram Bot Token
#define BOT_TOKEN "YOUR_BOT_TOKEN"
#define CHAT_ID "YOUR_CHAT_ID"

// Pin definitions
#define PIR_PIN 14
#define LED_PIN 2

WiFiClientSecure client;
UniversalTelegramBot bot(BOT_TOKEN, client);

volatile bool motionDetected = false;
unsigned long lastTrigger = 0;
const unsigned long debounceTime = 10000; // 10 second debounce

void IRAM_ATTR detectsMovement() {
  if (millis() - lastTrigger > debounceTime) {
    motionDetected = true;
    lastTrigger = millis();
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(PIR_PIN, INPUT_PULLDOWN);
  pinMode(LED_PIN, OUTPUT);

  // Connect to WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected to WiFi");

  // Configure secure client
  client.setCACert(TELEGRAM_CERTIFICATE_ROOT);

  // Attach interrupt
  attachInterrupt(digitalPinToInterrupt(PIR_PIN), detectsMovement, RISING);

  // Startup notification
  bot.sendMessage(CHAT_ID, "Security Node Online", "");
}

void loop() {
  if (motionDetected) {
    digitalWrite(LED_PIN, HIGH);
    bot.sendMessage(CHAT_ID, "ALERT: Motion detected at Node 1!", "");
    Serial.println("Motion detected!");
    delay(1000);
    digitalWrite(LED_PIN, LOW);
    motionDetected = false;
  }
  delay(100);
}
```

**Skill Level:** Beginner-Intermediate

---

### 2.2 Magnetic Door/Window Sensors

**Purpose:** Detect when doors or windows are opened.

**Source:** [ESP32io - Door Sensor Tutorial](https://esp32io.com/tutorials/esp32-door-sensor)

#### Components (per sensor)

| Component | Description | Est. Cost (AUD) |
|-----------|-------------|-----------------|
| Reed Switch | MC-38 Wired (NO type) | $3 |
| ESP32 | ESP32-WROOM-32 | $15 |
| Resistor | 10k pull-up | $0.10 |
| Wire | 2-conductor, 5m | $5 |
| **Per Sensor Total** | | **~$23** |

#### Wiring

```
Reed Switch (MC-38)          ESP32
+------------------+         +------------------+
| Wire 1 |---------+-------->| GPIO 27          |
|        |         |    +--->| 3.3V             |
|        |         |    |    |                  |
| Wire 2 |---------+----|--->| GND              |
+------------------+    |    +------------------+
                        |
                    [10k Resistor]
                        |
                    GPIO 27

Alternative: Use internal pull-up:
  pinMode(27, INPUT_PULLUP);
  Then only connect switch between GPIO27 and GND.
```

#### Installation Notes

- Mount magnet on movable part (door/window)
- Mount reed switch on fixed frame
- Gap when closed: <15mm for reliable operation
- Use shielded cable for runs >3m to reduce interference

---

### 2.3 Pressure Mat Sensors

**Purpose:** Detect footsteps in specific locations (under rugs, mats, stairs).

**Source:** [Instructables - Pressure Sensitive Floor Mat](https://www.instructables.com/Pressure-Sensitive-Floor-Mat-Sensor/)

#### Option A: Velostat DIY Mat

**Components:**
| Component | Description | Est. Cost (AUD) |
|-----------|-------------|-----------------|
| Velostat Sheet | 30cm x 30cm | $15 |
| Copper Tape | Conductive, 25mm wide | $10 |
| Foam Sheet | 5mm thick | $5 |
| Cardboard | For backing | $0 |
| Wire | 2-conductor | $3 |
| ESP32 | For processing | $15 |
| Resistor | 10k (voltage divider) | $0.10 |
| **Total** | | **~$48** |

**Construction:**
1. Cut two pieces of cardboard slightly larger than desired mat size
2. Apply copper tape in parallel strips (5cm apart) on each cardboard piece
3. Connect alternate strips together to form two electrode arrays
4. Place velostat sheet between the two electrode arrays
5. Seal edges with tape
6. Connect electrodes to voltage divider circuit

**Wiring:**
```
3.3V ----[10k]----+---- Velostat Mat ---- GND
                  |
                  v
               ESP32 ADC Pin (GPIO 34)
```

**Arduino Code:**
```cpp
#define PRESSURE_PIN 34
#define THRESHOLD 500  // Adjust based on testing

void setup() {
  Serial.begin(115200);
}

void loop() {
  int pressure = analogRead(PRESSURE_PIN);

  if (pressure < THRESHOLD) {  // Velostat resistance drops with pressure
    Serial.println("Step detected!");
    // Trigger alert
  }
  delay(50);
}
```

#### Option B: Commercial Pressure Mat + ESP32

For more reliable detection, use commercial NC (normally closed) pressure mats:

| Component | Description | Est. Cost (AUD) |
|-----------|-------------|-----------------|
| Pressure Mat | Commercial NC, various sizes | $30-60 |
| ESP32 | - | $15 |
| **Total** | | **~$45-75** |

Wire as a simple switch using internal pull-up.

**Skill Level:** Beginner

---

### 2.4 Laser/IR Beam Break Sensors

**Purpose:** Create invisible tripwire barriers for perimeter detection.

**Sources:**
- [Jameco - Easy Laser Alarm](https://www.jameco.com/Jameco/workshop/JamecoBuilds/easy-laser-alarm.html)
- [Electronics For You - Laser Security Alarm](https://www.electronicsforu.com/electronics-projects/prototypes/laser-light-security-alarm)

#### Option A: Laser + Photoresistor (Indoor)

**Components:**
| Component | Description | Est. Cost (AUD) |
|-----------|-------------|-----------------|
| Laser Pointer | Red, 5mW class | $5 |
| Photoresistor (LDR) | 5mm | $2 |
| IC | NE555 Timer | $1 |
| Resistors | 10k, 100k | $1 |
| Capacitors | 10uF, 100nF | $1 |
| Buzzer | 5V piezo | $3 |
| Small Mirrors | For beam routing | $5 |
| Enclosure | Light-proof for LDR | $5 |
| **Total** | | **~$23** |

**Circuit (555 Monostable):**
```
       +9V
        |
       [10k]
        |
LDR ---+--- Pin 2 (Trigger) --- NE555 --- Pin 3 (Out) --- Buzzer --- GND
        |                         |
       GND                      [Standard 555 monostable circuit]
```

**Notes:**
- Enclose LDR in light-proof tube with small hole for laser
- Use mirrors to route beam around corners
- Two parallel beams (2 feet apart) reduces false triggers from small animals

#### Option B: IR Beam Break (Outdoor Rated)

**Source:** [Cirkit Designer - IR Beam Break Sensor](https://docs.cirkitdesigner.com/component/cd63cd85-7594-4628-bc14-8d2f4d298a52/ir-beam-break-sensor)

**Components:**
| Component | Description | Est. Cost (AUD) |
|-----------|-------------|-----------------|
| IR Beam Break Sensor | 5V, 10m range | $15 |
| ESP32 | - | $15 |
| Weatherproof Enclosure | IP65 | $20 |
| **Total** | | **~$50** |

**Wiring:**
```
IR Sensor                ESP32
+------------------+     +------------------+
| VCC (5V) |------>|---->| 5V               |
| GND      |------>|---->| GND              |
| OUT      |------>|---->| GPIO 14          |
+------------------+     +------------------+
```

**Performance:** Commercial IR beam sensors can range 10-100m depending on model.

**Skill Level:** Beginner

---

## 3. Camera Systems (Local-Only)

### 3.1 ESP32-CAM Motion-Activated System

**Purpose:** Low-cost cameras with local SD card storage.

**Sources:**
- [Random Nerd Tutorials - ESP32-CAM PIR](https://randomnerdtutorials.com/esp32-cam-pir-motion-detector-photo-capture/)
- [GitHub - ESP32-CAM_MJPEG2SD](https://github.com/s60sc/ESP32-CAM_MJPEG2SD)

#### Components (per camera)

| Component | Description | Est. Cost (AUD) |
|-----------|-------------|-----------------|
| ESP32-CAM | AI-Thinker board | $12 |
| PIR Sensor | AM312 (small) or HC-SR501 | $3-5 |
| MicroSD Card | 32GB Class 10 | $12 |
| USB-TTL Adapter | For programming | $5 |
| 5V Power Supply | 2A minimum | $10 |
| Enclosure | Weatherproof | $15 |
| **Per Camera Total** | | **~$57-60** |

#### Wiring

```
ESP32-CAM                PIR Sensor (AM312)
+--------------+         +------------------+
| 5V      |<------------>| VCC              |
| GND     |<------------>| GND              |
| GPIO 13 |<------------>| OUT              |
+--------------+         +------------------+

Note: GPIO 13 used for wake-up from deep sleep.
PIR must be positioned away from ESP32 to avoid WiFi interference.
```

#### Firmware Options

**1. ESP32-CAM_MJPEG2SD** (Recommended)
- Records JPEGs to SD card as AVI files
- Motion detection via PIR or software-based
- Web interface for viewing/downloading
- MJPEG streaming for NVR integration
- WebDAV server for remote file access
- Audio recording if microphone installed

**Installation:**
1. Download from [GitHub](https://github.com/s60sc/ESP32-CAM_MJPEG2SD)
2. Flash using Arduino IDE or PlatformIO
3. Configure via web interface at device IP

**2. CameraWifiMotion**
- Software-based motion detection (no PIR needed)
- Captures ~4 frames/second, compares for changes
- Email/FTP upload options
- GitHub: [alanesq/CameraWifiMotion](https://github.com/alanesq/CameraWifiMotion)

#### Camera Placement Considerations

- Mount 2.4m+ height, angled 15-30 degrees down
- Avoid direct sunlight on lens
- Consider IR illumination for night vision
- Use weatherproof housing for outdoor installation
- Position WiFi antenna vertically for best reception

**Skill Level:** Intermediate

---

### 3.2 Raspberry Pi NVR with Frigate

**Purpose:** Multi-camera NVR with AI object detection, fully local.

**Sources:**
- [Pi My Life Up - Frigate NVR](https://pimylifeup.com/raspberry-pi-frigate-nvr/)
- [GitHub - geerlingguy/pi-nvr](https://github.com/geerlingguy/pi-nvr)
- [Jeff Geerling - Building Pi Frigate NVR](https://www.jeffgeerling.com/blog/2024/building-pi-frigate-nvr-axzezs-interceptor-1u-case/)

#### Hardware Requirements

| Component | Description | Est. Cost (AUD) |
|-----------|-------------|-----------------|
| Raspberry Pi 5 | 8GB RAM recommended | $130 |
| NVMe SSD | 512GB for recordings | $80 |
| NVMe HAT | For Pi 5 | $30 |
| Coral USB TPU | For AI detection | $90 |
| Power Supply | Official Pi 5 27W | $25 |
| SD Card | 32GB for OS | $15 |
| Case | With active cooling | $30 |
| **Total** | | **~$400** |

#### Camera Requirements

Cameras should support:
- RTSP streaming (most IP cameras)
- H.264 codec (H.265 optional)
- Substream at 640x360 for detection
- Main stream at 1080p or 4K for recording

**Budget IP Cameras:** Reolink, Amcrest, Hikvision (~$60-150 each)

#### Frigate Installation (Docker)

**docker-compose.yml:**
```yaml
version: "3.9"
services:
  frigate:
    container_name: frigate
    privileged: true
    restart: unless-stopped
    image: ghcr.io/blakeblackshear/frigate:stable
    shm_size: "256mb"
    devices:
      - /dev/bus/usb:/dev/bus/usb  # Coral USB
    volumes:
      - /etc/localtime:/etc/localtime:ro
      - ./config:/config
      - /mnt/frigate:/media/frigate
      - type: tmpfs
        target: /tmp/cache
        tmpfs:
          size: 1000000000
    ports:
      - "5000:5000"
      - "8554:8554"  # RTSP feeds
      - "8555:8555/tcp"  # WebRTC
      - "8555:8555/udp"
    environment:
      FRIGATE_RTSP_PASSWORD: "your_password"
```

**config.yml (example for 2 cameras):**
```yaml
mqtt:
  enabled: True
  host: 192.168.1.100  # Your MQTT broker

detectors:
  coral:
    type: edgetpu
    device: usb

cameras:
  front_door:
    ffmpeg:
      inputs:
        - path: rtsp://user:pass@192.168.1.50:554/stream1
          roles:
            - detect
            - record
    detect:
      width: 1280
      height: 720
      fps: 5
    record:
      enabled: True
      retain:
        days: 7
    snapshots:
      enabled: True
      retain:
        default: 14

  backyard:
    ffmpeg:
      inputs:
        - path: rtsp://user:pass@192.168.1.51:554/stream1
          roles:
            - detect
            - record
    detect:
      width: 1280
      height: 720
      fps: 5
    record:
      enabled: True
```

#### Storage Planning

| Cameras | Resolution | Days Retained | Approx Storage |
|---------|------------|---------------|----------------|
| 2 | 1080p | 7 | ~200GB |
| 4 | 1080p | 7 | ~400GB |
| 4 | 1080p | 14 | ~800GB |

**Skill Level:** Intermediate-Advanced

---

### 3.3 Night Vision IR Illumination

**Purpose:** Enable night vision for cameras without built-in IR.

**Source:** [Instructables - DIY IR Illuminator](https://www.instructables.com/DIY-IR-Infrared-Illuminator-Night-Viewing-With/)

#### Wavelength Comparison

| Wavelength | Visibility | Range | Best For |
|------------|------------|-------|----------|
| 850nm | Faint red glow visible | Longer range, brighter | General security (visible deterrent) |
| 940nm | Completely invisible | 30-40% less range | Covert applications |

**Note:** Most security cameras are optimized for 850nm. Check camera specs before choosing wavelength.

#### DIY IR Illuminator Build

**Components:**
| Component | Description | Est. Cost (AUD) |
|-----------|-------------|-----------------|
| IR LEDs | 850nm, 5mm, 20x | $10 |
| Current Limiting Resistors | Based on LED specs | $2 |
| Transistor | 2N2222 or similar | $1 |
| Heat Sink | Aluminum | $5 |
| Power Supply | 12V 2A | $15 |
| Enclosure | Weatherproof with lens | $15 |
| **Total** | | **~$48** |

**Simple 12V Array Circuit:**
```
+12V
  |
  +--[100R]--+--[LED]--+--[LED]--+--[LED]--+-- GND
  |          |         |         |
  +--[100R]--+--[LED]--+--[LED]--+--[LED]--+
  |          |         |         |
  +--[100R]--+--[LED]--+--[LED]--+--[LED]--+
  (etc. for desired brightness)

Note: 3 LEDs in series with 100 ohm resistor for 12V supply.
Adjust resistor for your LED forward voltage.
```

**Alternative: Commercial IR Illuminators**
- CMVision IR illuminators: 850nm/940nm combo units
- Range: 50-60 meters
- Cost: ~$50-100 AUD

**Skill Level:** Beginner-Intermediate

---

## 4. Communication Builds

### 4.1 LoRa Mesh Network (Meshtastic)

**Purpose:** Long-range, off-grid communication and sensor network.

**Sources:**
- [Hackster.io - Build Private LoRa Mesh](https://www.hackster.io/Shilleh/build-a-private-lora-mesh-network-with-esp32-d08fdd)
- [DigiKey - DIY Meshtastic](https://www.digikey.com/en/maker/projects/meshyour-world-offgrid-mesh-network-with-esp32-lora/0995dca145dc469bbbbab06b38b95bd9)

#### Performance Specifications

- **Range:** 2-20+ km line-of-sight; several km in typical conditions
- **Battery Life:** Days to weeks depending on usage
- **Encryption:** AES-256
- **Mesh Capacity:** Dozens of nodes tested

#### Hardware Options

**Option A: Pre-built Boards (Easiest)**

| Board | Features | Est. Cost (AUD) |
|-------|----------|-----------------|
| Heltec LoRa32 V3 | ESP32 + SX1262 + OLED | $25 |
| LILYGO T-Beam | ESP32 + SX1276 + GPS + 18650 holder | $45 |
| RAK WisBlock | Modular, various options | $40-80 |
| XIAO ESP32S3 + Wio-SX1262 | Thumb-sized, Core Electronics AU | $40 |

**Option B: DIY Build**

| Component | Description | Est. Cost (AUD) |
|-----------|-------------|-----------------|
| ESP32-S3 DevKit | - | $15 |
| LoRa Module | SX1262 or SX1276 | $15 |
| OLED Display | 0.96" I2C | $5 |
| Antenna | 868/915MHz (AU uses 915MHz) | $10 |
| LiPo Battery | 18650 or pouch | $15 |
| TP4056 Charger | - | $3 |
| Enclosure | IP65 | $15 |
| **Total** | | **~$78** |

#### Wiring (ESP32 + SX1262)

```
SX1262 Module          ESP32-S3
+-------------+        +------------------+
| VCC    |------------>| 3.3V             |
| GND    |------------>| GND              |
| SCK    |------------>| GPIO 18          |
| MISO   |------------>| GPIO 19          |
| MOSI   |------------>| GPIO 23          |
| NSS    |------------>| GPIO 5           |
| RST    |------------>| GPIO 14          |
| DIO1   |------------>| GPIO 26          |
| BUSY   |------------>| GPIO 27          |
+-------------+        +------------------+
```

#### Meshtastic Firmware Installation

**Method 1: Web Flasher (Easiest)**
1. Go to [flasher.meshtastic.org](https://flasher.meshtastic.org)
2. Connect device via USB
3. Select board type
4. Click "Flash"

**Method 2: CLI**
```bash
pip install meshtastic
meshtastic --flash
```

#### Configuration

1. Install Meshtastic app (iOS/Android)
2. Connect via Bluetooth
3. Set region to ANZ (915MHz for Australia)
4. Create private channel with PSK (pre-shared key)
5. Share PSK with other nodes

#### Sensor Integration

ESP32 GPIO available for sensors. Example: temperature sensor reporting via mesh:

```cpp
#include <meshtastic.h>
#include <DHT.h>

DHT dht(GPIO_NUM_4, DHT22);

void sendSensorData() {
  float temp = dht.readTemperature();
  String msg = "Temp: " + String(temp) + "C";
  meshtastic_send_text(msg.c_str());
}
```

**Skill Level:** Beginner-Intermediate

---

### 4.2 ESP32 WiFi Mesh (painlessMesh)

**Purpose:** Short-range mesh network over WiFi for indoor sensor networks.

**Sources:**
- [Random Nerd Tutorials - ESP-MESH](https://randomnerdtutorials.com/esp-mesh-esp32-esp8266-painlessmesh/)
- [Circuit Digest - ESP Mesh Tutorial](https://circuitdigest.com/microcontroller-projects/how-to-configure-an-esp-mesh-network-using-arduino-ide-to-communicate-between-esp32-esp8266-and-nodemcu)

#### Characteristics

- **Range:** ~30-50m per node (WiFi range)
- **Self-organizing:** Nodes automatically discover and route
- **Payload:** JSON messages (larger than LoRa)
- **No central access point required**

#### Components (per node)

| Component | Description | Est. Cost (AUD) |
|-----------|-------------|-----------------|
| ESP32 DevKit | - | $15 |
| Sensor (optional) | DHT22, PIR, etc. | $5-10 |
| Power Supply | 5V USB | $5 |
| **Per Node Total** | | **~$25-30** |

#### Installation

Arduino IDE Library Manager:
- painlessMesh
- ArduinoJson
- TaskScheduler
- ESPAsyncTCP

#### Basic Code (Sensor Node)

```cpp
#include <painlessMesh.h>

#define MESH_PREFIX "SecurityMesh"
#define MESH_PASSWORD "SecurePass123"
#define MESH_PORT 5555

Scheduler userScheduler;
painlessMesh mesh;

void sendMessage();
Task taskSendMessage(TASK_SECOND * 10, TASK_FOREVER, &sendMessage);

void sendMessage() {
  String msg = "Node: " + String(mesh.getNodeId());
  msg += " | Motion: " + String(digitalRead(PIR_PIN));
  mesh.sendBroadcast(msg);
}

void receivedCallback(uint32_t from, String &msg) {
  Serial.printf("Received from %u: %s\n", from, msg.c_str());
}

void setup() {
  Serial.begin(115200);

  mesh.setDebugMsgTypes(ERROR | STARTUP);
  mesh.init(MESH_PREFIX, MESH_PASSWORD, &userScheduler, MESH_PORT);
  mesh.onReceive(&receivedCallback);

  userScheduler.addTask(taskSendMessage);
  taskSendMessage.enable();
}

void loop() {
  mesh.update();
}
```

**Skill Level:** Intermediate

---

### 4.3 Simple VHF/UHF Receiver for Monitoring

**Purpose:** Monitor local radio communications.

**Sources:**
- [ARRL - Ultra-Simple 6m Receiver](https://www.arrl.org/files/file/Technology/tis/info/pdf/9712039.pdf)
- [Nuts & Volts - Simple VHF Receiver](https://www.nutsvolts.com/magazine/article/a_simple_vhf_receiver)

**Note:** Receive-only equipment generally does not require a license. Transmitting requires appropriate amateur radio license.

#### Superregenerative Receiver (50-150MHz)

**Components:**
| Component | Description | Est. Cost (AUD) |
|-----------|-------------|-----------------|
| FET | J310 or BF245 | $3 |
| Audio Amp IC | LM386 | $2 |
| Variable Capacitor | 10-60pF | $8 |
| Coil | Air-wound (frequency dependent) | $2 |
| Resistors/Capacitors | Assorted | $10 |
| Potentiometer | 10k (volume) | $2 |
| Speaker | 8 ohm small | $5 |
| Antenna | Telescopic | $5 |
| 9V Battery | - | $5 |
| **Total** | | **~$42** |

**Build Notes:**
- Mount tuning coil away from conductive objects
- Build audio stage first, test before adding RF stage
- Use "dead bug" construction for RF section
- Sensitivity ~1uV achievable

**Better Alternative:** RTL-SDR dongle ($45) provides far superior performance with no construction required.

**Skill Level:** Advanced (RF construction)

---

### 4.4 GSM SMS Alert Module

**Purpose:** Send SMS alerts without internet dependency.

**Sources:**
- [Random Nerd Tutorials - ESP32 SIM800L SMS](https://randomnerdtutorials.com/esp32-sim800l-send-text-messages-sms/)
- [Instructables - GSM Security Alarm](https://www.instructables.com/GSM-Security-Alarm-SIM800L-SMS/)

#### Components

| Component | Description | Est. Cost (AUD) |
|-----------|-------------|-----------------|
| SIM800L Module | GSM/GPRS | $15 |
| ESP32 | Or Arduino Nano | $15 |
| LiPo Battery | 3.7V 2000mAh (power supply) | $15 |
| DC-DC Converter | 5V to 4V (for SIM800L) | $5 |
| SIM Card | Prepaid with SMS | $10 |
| Antenna | GSM 900/1800 | $5 |
| **Total** | | **~$65** |

**Critical Power Note:**
SIM800L requires 3.4V-4.4V at up to 2A peak during transmission. Standard USB power is insufficient. Use:
- LiPo battery (3.7V nominal) direct to module
- Or dedicated DC-DC converter rated for 2A

#### Wiring

```
SIM800L              ESP32
+--------+           +------------------+
| VCC  |<---4V DC--->| (External Supply)|
| GND  |<----------->| GND              |
| TXD  |------------>| GPIO 16 (RX2)    |
| RXD  |<------------| GPIO 17 (TX2)    |
| RST  |------------>| GPIO 4 (optional)|
+--------+           +------------------+
```

#### Code (Send SMS on Motion)

```cpp
#include <HardwareSerial.h>

HardwareSerial SIM800(2);  // Use UART2

#define PIR_PIN 14
#define PHONE_NUMBER "+614XXXXXXXX"

void setup() {
  Serial.begin(115200);
  SIM800.begin(9600, SERIAL_8N1, 16, 17);

  pinMode(PIR_PIN, INPUT);

  delay(3000);  // Wait for SIM800L to boot

  // Test AT command
  SIM800.println("AT");
  delay(1000);

  // Set SMS text mode
  SIM800.println("AT+CMGF=1");
  delay(1000);
}

void sendSMS(String message) {
  SIM800.print("AT+CMGS=\"");
  SIM800.print(PHONE_NUMBER);
  SIM800.println("\"");
  delay(1000);

  SIM800.print(message);
  delay(100);

  SIM800.write(26);  // Ctrl+Z to send
  delay(5000);
}

void loop() {
  if (digitalRead(PIR_PIN) == HIGH) {
    sendSMS("ALERT: Motion detected!");
    delay(60000);  // 1 minute cooldown
  }
  delay(100);
}
```

**Skill Level:** Intermediate

---

## 5. Power Independence

### 5.1 Solar Charging System for Security Electronics

**Purpose:** Off-grid power for remote sensors and cameras.

**Sources:**
- [Random Nerd Tutorials - Solar ESP32](https://randomnerdtutorials.com/power-esp32-esp8266-solar-panels-battery-level-monitoring/)
- [Instructables - Solar Power for ESP32](https://www.instructables.com/Solar-Power-for-ArduinoESP32/)

#### Basic System Components

| Component | Description | Est. Cost (AUD) |
|-----------|-------------|-----------------|
| Solar Panel | 6V 6W (or 5V 5W) | $25 |
| TP4056 Module | With protection circuit | $3 |
| 18650 Battery | 3000mAh | $15 |
| Battery Holder | Single 18650 | $3 |
| Voltage Regulator | MCP1700-3302E (3.3V LDO) | $2 |
| Diode | 1N5817 Schottky | $0.50 |
| Capacitors | 10uF, 100nF | $1 |
| Enclosure | Weatherproof | $15 |
| **Total** | | **~$65** |

#### Circuit Diagram

```
                        +--------------------+
Solar Panel 6V -------->| TP4056 (IN+/IN-)   |
                        |                    |
                        | B+/B- ------------>| 18650 Battery
                        |                    |
                        | OUT+/OUT- ---------|---> 1N5817 ---> MCP1700 --> 3.3V Out
                        +--------------------+              |
                                                            +---> ESP32 3.3V pin

Note: TP4056 modules with "protection" include over-discharge protection.
      The MCP1700 provides stable 3.3V from battery's 3.0-4.2V range.
```

#### Component Selection Guide

**Solar Panel Sizing:**
- ESP32 active: ~180mA average
- ESP32 deep sleep: ~10uA
- Daily consumption (active 10%): ~180mA * 2.4h + 0.01mA * 21.6h = 432mAh + ~0.2mAh = ~435mAh
- Solar panel should provide 3x daily consumption: ~1300mAh
- 5V 5W panel in good sun: ~1000mA for 4-5 hours = 4000-5000mAh (adequate)

**Battery Sizing:**
- 2-3 days autonomy for cloudy weather
- 3000mAh 18650 provides ~2 days with typical usage
- Use 2x 18650 in parallel for better autonomy

#### Power Optimization Tips

1. **Use Deep Sleep:**
   ```cpp
   esp_sleep_enable_timer_wakeup(300 * 1000000); // Wake every 5 minutes
   esp_deep_sleep_start();
   ```

2. **Reduce WiFi power:**
   ```cpp
   WiFi.setTxPower(WIFI_POWER_8_5dBm);  // Reduce from default 20dBm
   ```

3. **Disable Bluetooth if not used:**
   ```cpp
   btStop();
   ```

**Skill Level:** Intermediate

---

### 5.2 Battery Bank with BMS

**Purpose:** Larger capacity power storage for critical systems.

**Sources:**
- [DIY Solar Power Forum](https://diysolarforum.com/)
- [Home Assistant Community - LiFePO4 Solar](https://community.home-assistant.io/t/powering-esp32-with-solar-lifepo4/744978)

#### LiFePO4 vs Li-Ion Comparison

| Feature | Li-Ion (18650) | LiFePO4 |
|---------|----------------|---------|
| Voltage | 3.7V nominal | 3.2V nominal |
| Cycle Life | 500-1000 | 2000-5000 |
| Safety | Moderate | Excellent |
| Temperature Range | 0-45C | -20-60C |
| Self-Discharge | 2-3%/month | <1%/month |
| Cost | Lower | Higher |

**Recommendation:** LiFePO4 for permanent outdoor installations due to better safety and cycle life.

#### 12V Battery Bank Components

| Component | Description | Est. Cost (AUD) |
|-----------|-------------|-----------------|
| LiFePO4 Cells | 3.2V 50Ah x 4 | $200 |
| BMS | 4S 100A with balancing | $40 |
| Solar Charge Controller | 12V MPPT 20A | $80 |
| Solar Panel | 100W 12V | $120 |
| Fuses/Breakers | Various | $30 |
| Wiring | 10AWG, connectors | $30 |
| Enclosure | Battery box | $40 |
| **Total** | | **~$540** |

**Configuration:** 4 cells in series = 12.8V nominal (same as lead-acid)

#### Low Voltage Protection

Add LP3470 reset controller to disconnect load when battery low:

```
Battery + ---> LP3470 VCC ---> N-Channel MOSFET Gate
                   |
                 Reset Out --> (controls MOSFET)
                   |
                Threshold: Set for 11.5V (2.88V/cell)

When battery < 11.5V, MOSFET turns off, protecting battery.
```

**Skill Level:** Intermediate-Advanced

---

### 5.3 Automatic Mains/Battery Failover

**Purpose:** Seamless transition between mains and battery power.

#### Simple Diode-OR Failover

```
Mains 5V (USB) ----[1N5817]---+
                              |
                              +---> To Load (ESP32, etc.)
                              |
Battery (via regulator) --[1N5817]---+

Note: Diode with higher voltage (mains) supplies load.
      When mains fails, battery takes over automatically.
      Voltage drop: ~0.3V per Schottky diode.
```

#### Components

| Component | Description | Est. Cost (AUD) |
|-----------|-------------|-----------------|
| Schottky Diodes | 1N5817 x 2 | $1 |
| USB Power Supply | 5V 2A | $10 |
| Battery System | (from above) | varies |
| **Total** | | **~$11 + battery** |

**Skill Level:** Beginner

---

## 6. Sensor Integration Platform

### 6.1 Home Assistant for Local-Only Security

**Purpose:** Central hub for all sensors with no cloud dependency.

**Sources:**
- [Home Assistant Documentation](https://www.home-assistant.io/integrations)
- [GitHub - Alarmo Integration](https://github.com/nielsfaber/alarmo)

#### Hardware Requirements

| Component | Description | Est. Cost (AUD) |
|-----------|-------------|-----------------|
| Raspberry Pi 4/5 | 4GB+ RAM | $100-130 |
| SD Card | 32GB A2 rated | $15 |
| Power Supply | Official 15W/27W | $20 |
| SSD (optional) | For reliability | $50 |
| Case | With cooling | $20 |
| **Total** | | **~$205-235** |

#### Installation

**Method 1: Home Assistant OS (Recommended)**
1. Download HA OS image from home-assistant.io
2. Flash to SD card using Balena Etcher
3. Boot Pi, access at homeassistant.local:8123
4. Complete onboarding wizard

**Method 2: Docker**
```bash
docker run -d \
  --name homeassistant \
  --privileged \
  --restart=unless-stopped \
  -v /path/to/config:/config \
  -v /run/dbus:/run/dbus:ro \
  --network=host \
  ghcr.io/home-assistant/home-assistant:stable
```

#### Key Integrations

1. **Alarmo** - DIY alarm panel
2. **MQTT** - For ESP32 sensors
3. **Frigate** - NVR integration
4. **ESPHome** - ESP32/8266 device management

**Skill Level:** Intermediate

---

### 6.2 Mosquitto MQTT Broker Setup

**Purpose:** Message broker for sensor network.

**Sources:**
- [Random Nerd Tutorials - Mosquitto on Pi](https://randomnerdtutorials.com/how-to-install-mosquitto-broker-on-raspberry-pi/)
- [Pi My Life Up - MQTT Server](https://pimylifeup.com/raspberry-pi-mosquitto-mqtt-server/)

#### Installation

```bash
sudo apt update
sudo apt install -y mosquitto mosquitto-clients
```

#### Enable Remote Access

Edit `/etc/mosquitto/mosquitto.conf`:
```
listener 1883
allow_anonymous true  # For testing only

# For production, add authentication:
# password_file /etc/mosquitto/passwd
# allow_anonymous false
```

Restart service:
```bash
sudo systemctl restart mosquitto
```

#### Add Authentication (Recommended)

```bash
# Create password file
sudo mosquitto_passwd -c /etc/mosquitto/passwd your_username

# Update config to use password file
# Then restart mosquitto
```

#### Testing

Terminal 1 (Subscribe):
```bash
mosquitto_sub -h localhost -t "security/#" -v
```

Terminal 2 (Publish):
```bash
mosquitto_pub -h localhost -t "security/motion/front" -m "detected"
```

#### ESP32 MQTT Publishing

```cpp
#include <WiFi.h>
#include <PubSubClient.h>

const char* mqtt_server = "192.168.1.100";

WiFiClient espClient;
PubSubClient client(espClient);

void reconnect() {
  while (!client.connected()) {
    if (client.connect("ESP32_Motion_1")) {
      client.subscribe("security/commands");
    } else {
      delay(5000);
    }
  }
}

void setup() {
  WiFi.begin(ssid, password);
  client.setServer(mqtt_server, 1883);
}

void loop() {
  if (!client.connected()) reconnect();
  client.loop();

  if (motionDetected) {
    client.publish("security/motion/zone1", "1");
    motionDetected = false;
  }
}
```

**Skill Level:** Beginner-Intermediate

---

### 6.3 Alert Systems

#### Local Audio Alert

**Components:**
| Component | Description | Est. Cost (AUD) |
|-----------|-------------|-----------------|
| Siren | 12V 120dB | $20 |
| Relay Module | 5V control, 12V switch | $5 |
| ESP32 | For control | $15 |
| 12V Power Supply | 2A | $15 |
| **Total** | | **~$55** |

**Wiring:**
```
ESP32 GPIO --> Relay IN
ESP32 GND --> Relay GND
ESP32 3.3V --> Relay VCC

12V+ --> Relay NO (normally open)
Relay COM --> Siren +
Siren - --> 12V GND
```

#### SMS via GSM Module

See Section 4.4 for GSM SMS alert setup.

#### Push Notification via Telegram

Use ESP32 with UniversalTelegramBot library (see Section 2.1 for code example).

**Skill Level:** Beginner-Intermediate

---

### 6.4 Monitoring Dashboard

**Purpose:** Local display showing system status.

#### Option A: Web Dashboard (Home Assistant)

Home Assistant provides built-in dashboards accessible via browser on local network.

#### Option B: Dedicated Display

**Components:**
| Component | Description | Est. Cost (AUD) |
|-----------|-------------|-----------------|
| Raspberry Pi 4 | 2GB sufficient | $80 |
| 7" Touchscreen | Official Pi display | $100 |
| Case | With display mount | $30 |
| **Total** | | **~$210** |

**Setup:**
1. Install Raspberry Pi OS Lite
2. Install Chromium browser
3. Configure kiosk mode to display HA dashboard
4. Auto-start on boot

**Kiosk Script:**
```bash
#!/bin/bash
xset s noblank
xset s off
xset -dpms

chromium-browser --noerrdialogs --disable-infobars --kiosk \
  http://homeassistant.local:8123/lovelace/security
```

**Skill Level:** Intermediate

---

## 7. Australian Suppliers

### Major Retailers

| Supplier | Specialty | Website |
|----------|-----------|---------|
| **Core Electronics** | ESP32, Raspberry Pi, sensors, Meshtastic | core-electronics.com.au |
| **Jaycar** | General electronics, Arduino, components | jaycar.com.au |
| **Altronics** | Components, kits, tools | altronics.com.au |
| **Little Bird Electronics** | Maker boards, sensors | littlebird.com.au |
| **Pakronics** | Educational, sensors | pakronics.com.au |

### Specific Product Availability

#### ESP32/LoRa (Core Electronics)
- XIAO ESP32S3 + Wio-SX1262 LoRa: ~$40
- ESP32 LoRa 1-Channel Gateway: ~$60
- Heltec WiFi LoRa 32: ~$30

#### ESP32 (Jaycar)
- Duinotech ESP32 Main Board (XC3800): ~$30
- ESP32 Wearable Board (XC3810): ~$35
- LoRa Shields (XC4392): ~$40

#### Sensors (Jaycar/Core Electronics)
- PIR Sensor HC-SR501: ~$5
- Reed Switch: ~$3
- ESP32-CAM: ~$15

#### Power Components
- Solar Panels 5-6V: $15-30
- 18650 Batteries: $10-20 each
- TP4056 Modules: $3-5

### International Options

| Supplier | Notes | Shipping to AU |
|----------|-------|----------------|
| AliExpress | Cheapest, 2-4 week shipping | Free/low cost |
| DigiKey | Wide selection, fast | ~$15 |
| Mouser | Wide selection, fast | ~$20 |
| Amazon AU | Quick delivery, limited selection | Varies |

### Estimated Project Costs Summary

| Project | Components | Est. Total (AUD) |
|---------|------------|------------------|
| Basic RF Detector | FET circuit | $27 |
| Advanced RF Detector | MAX2015 | $56 |
| RTL-SDR Setup | Dongle + antenna | $115-165 |
| ESP32 PIR Node | Single sensor | $46 |
| Magnetic Door Sensor | Reed + ESP32 | $23 |
| Pressure Mat | DIY Velostat | $48 |
| IR Beam Break | Commercial sensor + ESP32 | $50 |
| ESP32-CAM System | Per camera | $57-60 |
| Raspberry Pi NVR | With Coral TPU | $400 |
| LoRa Mesh Node | Heltec board | $25 |
| GSM SMS Alert | SIM800L + ESP32 | $65 |
| Solar Power System | Basic | $65 |
| Battery Bank | LiFePO4 12V | $540 |
| Home Assistant Hub | Pi 4 + SSD | $235 |

---

## Appendix A: Quick Reference - Pin Mappings

### ESP32-WROOM-32 Common Pins

```
GPIO 2  - Built-in LED
GPIO 4  - General purpose (safe)
GPIO 5  - VSPI SS
GPIO 12 - Boot mode (avoid pull-high at boot)
GPIO 13 - General purpose (safe)
GPIO 14 - General purpose (safe)
GPIO 15 - Debug output at boot
GPIO 16 - UART2 RX
GPIO 17 - UART2 TX
GPIO 18 - VSPI SCK
GPIO 19 - VSPI MISO
GPIO 21 - I2C SDA
GPIO 22 - I2C SCL
GPIO 23 - VSPI MOSI
GPIO 25 - DAC1
GPIO 26 - DAC2
GPIO 27 - General purpose (safe)
GPIO 32-39 - ADC1 (analog input)
GPIO 34-39 - Input only (no pull-up/down)
```

### ESP32-CAM AI-Thinker Pins

```
GPIO 0  - Flash programming (pull low to flash)
GPIO 1  - UART TX (avoid)
GPIO 3  - UART RX (avoid)
GPIO 4  - Flashlight LED
GPIO 12 - SD Card (avoid)
GPIO 13 - Available (PIR recommended)
GPIO 14 - SD Card (avoid)
GPIO 15 - SD Card (avoid)
GPIO 16 - PSRAM (avoid)
```

---

## Appendix B: Frequency Reference

### Common Surveillance Device Frequencies

| Device Type | Frequency Range |
|-------------|-----------------|
| Cheap wireless cameras | 900MHz, 1.2GHz, 2.4GHz |
| WiFi devices | 2.4GHz (2400-2483 MHz), 5GHz |
| Bluetooth | 2.4GHz (2402-2480 MHz) |
| GSM (AU) | 900MHz, 1800MHz |
| 3G (AU) | 850MHz, 2100MHz |
| 4G LTE (AU) | 700MHz, 1800MHz, 2600MHz |
| GPS trackers | 1575.42 MHz (receive) + cellular |
| FM bugs | 88-108 MHz |
| UHF bugs | 400-470 MHz |
| Wireless microphones | VHF: 174-216 MHz, UHF: 470-698 MHz |

### Australian ISM Bands (License-Free)

| Band | Frequency | Max Power | Common Use |
|------|-----------|-----------|------------|
| 433 MHz | 433.05-434.79 | 25mW | Remote controls |
| 915 MHz | 915-928 | 1W EIRP | LoRa, IoT |
| 2.4 GHz | 2400-2483.5 | 4W EIRP | WiFi, Bluetooth |
| 5.8 GHz | 5725-5875 | 4W EIRP | WiFi |

---

## Appendix C: Safety Notes

### RF Equipment
- Always check local regulations before transmitting
- RTL-SDR is receive-only (no license required)
- LoRa in Australia must use 915-928 MHz band
- Amateur radio transmission requires license

### Electrical Safety
- Use appropriate fusing for battery systems
- LiPo/Li-Ion batteries can catch fire if damaged or overcharged
- Use modules with protection circuits (TP4056 with protect)
- Disconnect power before working on circuits

### Privacy and Legal
- Cameras on your own property: generally legal
- Recording others without consent: varies by state
- RF detection on your property: legal
- Intercepting others' communications: illegal

### Weatherproofing
- Use IP65+ rated enclosures for outdoor electronics
- Apply conformal coating to PCBs
- Use silicone sealant around cable entries
- Position solar panels to avoid standing water

---

## Sources and References

### RF Detection
- [Analog Devices - RF Bug Detector Circuit](https://www.analog.com/en/resources/design-notes/circuit-detects-and-locates-hidden-rf-bugs.html)
- [Homemade Circuits - RF Detector Circuits](https://www.homemade-circuits.com/2-simple-rf-detector-circuits-explored/)
- [RTL-SDR.com - Spectrum Analysis](https://www.rtl-sdr.com/)

### Motion/Intrusion
- [Random Nerd Tutorials - ESP32 PIR](https://randomnerdtutorials.com/esp32-pir-motion-sensor-interrupts-timers/)
- [ESP32io - Door Sensor](https://esp32io.com/tutorials/esp32-door-sensor)
- [Instructables - Pressure Mat](https://www.instructables.com/Pressure-Sensitive-Floor-Mat-Sensor/)

### Camera Systems
- [GitHub - ESP32-CAM_MJPEG2SD](https://github.com/s60sc/ESP32-CAM_MJPEG2SD)
- [GitHub - Frigate NVR Guide](https://github.com/theNetworkChuck/frigate-nvr-guide)
- [Jeff Geerling - Pi NVR Build](https://www.jeffgeerling.com/blog/2024/building-pi-frigate-nvr-axzezs-interceptor-1u-case/)

### Communication
- [Hackster.io - LoRa Mesh Network](https://www.hackster.io/Shilleh/build-a-private-lora-mesh-network-with-esp32-d08fdd)
- [Random Nerd Tutorials - painlessMesh](https://randomnerdtutorials.com/esp-mesh-esp32-esp8266-painlessmesh/)
- [Random Nerd Tutorials - ESP32 SIM800L SMS](https://randomnerdtutorials.com/esp32-sim800l-send-text-messages-sms/)

### Power Systems
- [Random Nerd Tutorials - Solar ESP32](https://randomnerdtutorials.com/power-esp32-esp8266-solar-panels-battery-level-monitoring/)
- [Voltaic Systems - Solar ESP32 Tutorial](https://blog.voltaicsystems.com/solar-powered-esp32-over-wifi-application-tutorial/)

### Integration
- [Home Assistant Documentation](https://www.home-assistant.io/integrations)
- [Random Nerd Tutorials - Mosquitto Setup](https://randomnerdtutorials.com/how-to-install-mosquitto-broker-on-raspberry-pi/)
- [GitHub - Alarmo](https://github.com/nielsfaber/alarmo)

---

*Document compiled January 2026. Verify current pricing and availability before purchasing.*
