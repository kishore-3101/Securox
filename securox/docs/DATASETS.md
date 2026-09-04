# Securox — Benchmark Datasets & Telemetry Provenance

## 1. Zero Synthetic Data Guarantee

Securox integrates authentic, empirically verified open-science benchmarks and clinical registries. The platform strictly differentiates between **Authentic Benchmark Data** and **Controlled Interactive Simulations**.

---

## 2. Dataset Catalog & Schema Reference

### A. Clinical & Healthcare Infrastructure
1. **MIMIC-IV-ED (Emergency Department)**:
   - *Source*: PhysioNet / MIT Laboratory for Computational Physiology.
   - *Records*: 425,087 emergency encounters.
   - *Fields*: `stay_id`, `triage_acuity` ($1 - 5$), `vitals_heartrate`, `vitals_sbp`, `vitals_dbp`, `chiefcomplaint`.
2. **MIMIC-IV Clinical Database**:
   - *Records*: Inpatient ICU admissions, lab events, and clinical pharmacology.
   - *Fields*: `hadm_id`, `itemid`, `charttime`, `value`, `valuenum`, `flag`.
3. **eICU Collaborative Research Database**:
   - *Source*: Philips Healthcare & MIT.
   - *Records*: Multi-center clinical telemetry from 208 hospitals across the US.
4. **ONC Health IT Certified Infrastructure**:
   - *Source*: US Office of the National Coordinator for Health Information Technology.
   - *Records*: Certified electronic health record product capabilities, PACS image servers, and API gateways.

### B. Smart City Traffic & IoT Networks
1. **ToN-IoT Dataset**:
   - *Source*: UNSW Canberra Cyber Range.
   - *Coverage*: Smart City traffic signal telemetry, SCADA sensors, ANPR cameras, and MODBUS commands.
   - *Attack Vectors*: Backdoor, DoS, Injection, Ransomware, Scanning, XSS.
2. **FASTag & ANPR Real-Time Telemetry**:
   - *Coverage*: Toll plaza RFID EPC tag scanning and OCR plate recognition with impossible travel velocity detection between gantry checkpoints.

### C. Network Cyber Defense & Banking Fraud
1. **CIC-IDS2017**:
   - *Source*: Canadian Institute for Cybersecurity.
   - *Coverage*: 2,099,976 flow records across 80 network attributes.
   - *Attacks*: PortScan, Brute Force, Web Attacks, DoS Slowloris, DDoS, Botnets, Infiltration.
2. **UNSW-NB15**:
   - *Source*: Australian Centre for Cyber Security.
   - *Coverage*: Modern synthesized low-footprint attack vectors: Fuzzers, Analysis, Backdoors, Exploits, Generic.
3. **Indian Banking & SWIFT Financial Fraud Dataset**:
   - *Source*: Machine Learning Group / Indian Banking Consortium.
   - *Records*: 550,000 transaction records with extreme class imbalance ($0.17\%$ fraud rate).
   - *Features*: UPI/RTGS channel, velocity over trailing 1m/10m, amount ratio vs history, beneficiary account age, device entropy, failed auth count.
