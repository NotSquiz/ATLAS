# Getting data from your Urbanworx scale to ATLAS: A complete integration guide

The Urbanworx UXSMHSC2 can feed data into your custom ATLAS system, but it requires a multi-step workaround since budget BIA scales lack direct APIs. The most reliable pathway is **scale → companion app → Apple Health/Google Fit → automated export tool → ATLAS**. For Android users, the open-source app **openScale** may offer a more direct route by connecting to the scale via Bluetooth and exporting to CSV or MQTT without the proprietary app.

## Your scale likely uses Fitdays, a white-label app shared by dozens of generic BIA scales

The specific model number "UXSMHSC2" doesn't appear in public documentation—it's likely an Australian retailer SKU. However, Urbanworx smart scales (including the related UX-Libra-8B) almost certainly use **Fitdays**, developed by Guangdong ICOMON Technology. This app powers over 3 million users across numerous white-label scale brands.

**Download links:**
- iOS: https://apps.apple.com/us/app/fitdays/id1434527961
- Android: https://play.google.com/store/apps/details?id=cn.fitdays.fitdays

The Fitdays app syncs with **Apple Health, Google Fit, Samsung Health, and Fitbit**—this integration capability is your pathway to extracting data. The app supports up to **24 user profiles** and includes features like baby weighing mode. User reviews rate it 3.5-3.8/5, with common complaints about Bluetooth connectivity and an outdated interface.

If Fitdays doesn't connect, alternative white-label apps that may work include **1byone Health** (supports CSV/PDF export), **Arboleaf** (supports CSV export and is HIPAA/GDPR compliant), or **Feelfit**. Try each until one pairs successfully—these scales use standardized Bluetooth protocols.

## The scale measures 13 body composition metrics through 4-electrode BIA

Your UXSMHSC2 uses **4-electrode bioelectrical impedance analysis**, with electrodes embedded in the glass platform under each foot. A small electrical current passes through your body to estimate composition based on how different tissues conduct electricity.

The scale itself only displays weight—all other metrics appear in the companion app: **body fat percentage, muscle mass, bone mass, body water percentage, visceral fat rating, BMR (basal metabolic rate), metabolic age, subcutaneous fat, protein percentage, fat-free body weight, skeletal muscle mass, and BMI**. Technical specifications include a **180kg maximum capacity**, Bluetooth 4.0+ connectivity, and typical weight accuracy of ±0.1kg.

**Critical accuracy caveat:** Budget 4-electrode BIA scales can deviate **21-34% from DEXA scans** for body fat measurements. Results vary significantly based on hydration, time of day, and recent exercise. Use these metrics for tracking trends rather than absolute values—consistency in measurement timing matters more than the numbers themselves.

## Data export requires using health platforms as intermediaries

The Fitdays app has **no native CSV or PDF export**. Your data extraction strategy depends on routing measurements through Apple Health or Google Fit, then using third-party tools to pull the data out.

**For iOS users (recommended approach):** Enable Fitdays sync to Apple Health. Then use **Health Auto Export** ($4.99, https://www.healthexportapp.com) which provides REST API endpoints, MQTT broker integration, JSON/CSV export, and direct Home Assistant support. This app can automatically push new measurements to your ATLAS system via webhooks. Alternative: The free **Heartbridge** project (https://github.com/mm/heartbridge) combines iOS Shortcuts with a Python CLI to export health data.

**For Android users:** Google Fit's REST API is being **deprecated in 2026**, so migrate to **Health Connect** which is now Android's standard health data platform. The **TaskerHealthConnect** plugin (https://github.com/RafhaanShah/TaskerHealthConnect) lets you read health data as JSON and trigger automations. Alternatively, the **openScale** app can bypass the proprietary app entirely.

**Via Fitbit (most reliable API):** If you sync to Fitbit, their Web API offers excellent programmatic access. The body data endpoints (`GET /1/user/-/body/log/weight/date/{date}.json`) return JSON with weight, BMI, and body fat. However, most third-party scales only sync **weight and BMI**—not the full body composition metrics—to Fitbit.

## openScale offers direct Bluetooth access without proprietary apps

The **openScale** project (https://github.com/oliexdev/openScale) is an open-source Android app with **2,100+ GitHub stars** that connects directly to 25+ scale brands via Bluetooth. It tracks weight, BMI, body fat, muscle mass, and other metrics with full CSV export and MQTT publishing capability.

Supported scales include Xiaomi, Renpho, Yunmai, and many generic Bluetooth models. Your Urbanworx may work if it uses a common Bluetooth protocol. If not, openScale's wiki provides a guide for reverse-engineering new scales using Bluetooth HCI snoop logs and Wireshark analysis.

For home automation integration, the **lolouk44/xiaomi_mi_scale** Docker project publishes measurements via MQTT with auto-discovery for Home Assistant. A typical pipeline: **Scale → Raspberry Pi with Python/bleak → MQTT broker → Node-RED processing → InfluxDB storage → Grafana visualization**. Body composition formulas (BMI, BMR, body fat estimates) are well-documented in openScale's wiki and can be calculated from raw weight data if your scale doesn't provide them natively.

## Your practical ATLAS integration pathway

Based on your existing Garmin integration and goal of feeding data to ATLAS, here's the recommended approach:

**Simplest path (iOS):** Fitdays → Apple Health → Health Auto Export → REST webhook to ATLAS. Configure Health Auto Export to POST new body measurements as JSON to your ATLAS endpoint. This requires minimal coding and runs automatically.

**Most control (Android):** openScale → MQTT → custom Python script → ATLAS. Install openScale, pair with your scale, enable MQTT publishing to a Mosquitto broker, then write a Python subscriber that transforms the data and pushes to ATLAS.

**Hybrid approach:** If neither works directly with your scale, use the proprietary app for measurement, sync to Apple Health or Google Fit, then parse the exported data. Apple Health data exports as XML that Python libraries like **apple-health-parser** (https://pypi.org/project/apple-health-parser/) can process.

**Key limitation to understand:** Most budget scale apps only sync **weight** to third-party platforms—the detailed body composition metrics often stay locked in the proprietary app. This is the fundamental frustration with generic BIA scales and why Withings commands a premium.

## Withings provides what your Urbanworx cannot: a real API

The Withings Body Comp ($199) or Body Smart ($99) represent the upgrade path when you want reliable programmatic access. Withings is the **only major consumer scale manufacturer with a documented public REST API**.

Their developer portal (https://developer.withings.com) provides OAuth 2.0 authentication, comprehensive endpoint documentation, Python libraries (`withings-api` on PyPI), and webhook notifications for real-time data updates. Rate limits are generous at **120 requests per minute**. You can query all historical measurements, filter by date range, and receive JSON responses with precise timestamps.

Beyond API access, Withings Body Comp adds metrics your Urbanworx can't measure: **visceral fat index** (not just percentage), **vascular age** via pulse wave velocity, **standing heart rate**, and **electrodermal activity** for nerve health assessment. The multi-frequency BIA technology is more accurate than single-frequency budget scales, with clinical validation studies showing body fat accuracy within **±7.4% of DEXA** versus the 20-30% variance typical of cheap scales.

For your ATLAS system, a Withings scale would eliminate the intermediary steps entirely: scale measurement → webhook notification → ATLAS API ingestion. If your health optimization work justifies the $199 investment, Withings Body Comp provides the cleanest data pipeline.

## Conclusion

Your Urbanworx UXSMHSC2 can contribute data to ATLAS, but expect a multi-hop journey: proprietary app to health platform to export tool to your system. Start by confirming whether Fitdays pairs with your scale, then enable Apple Health or Google Fit sync. For iOS, Health Auto Export provides the easiest webhook-based extraction. For Android, evaluate whether openScale can connect directly—if so, you gain CSV export and MQTT publishing without app dependencies.

The fundamental limitation isn't technical capability but business model: budget scale manufacturers have no incentive to provide APIs since their margins come from hardware, not data services. Withings occupies a unique market position by monetizing ecosystem integration, which is why they're the only consumer scale with proper developer tools. When your ATLAS project matures and reliable body composition tracking becomes essential, the Withings Body Comp at $199 eliminates the extraction workarounds entirely.