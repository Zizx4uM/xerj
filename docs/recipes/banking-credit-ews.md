# Corporate Credit Monitoring & Early Warning System (EWS) with XERJ

**Goal:** Monitor corporate borrowers across a commercial loan portfolio in real time, detecting cash-flow collapses and 2-Kartoteka (*K-2 card index*) arrears weeks before loans hit statutory overdue cliffs (45-day sub-standard and 90-day NPL), while maintaining an auditable qualitative memory of branch inspection acts.

Developed in partnership between **[NazoratAI](https://github.com/Zizx4uM/NazoratAI)** ([Xajibayev Azizbek](https://github.com/Zizx4uM)) and the **[XERJ Community](https://github.com/xerj-org/xerj)**.

---

## The Banking Surveillance Problem

In corporate banking credit departments, credit monitoring officers monitor hundreds of enterprise facilities across vital industrial sectors (textile clusters, greenhouses, construction materials, food processing). Traditionally:

1. **Static Delinquency Blindspots:** Central Bank regulations trigger emergency inspections at **45 days overdue** (Yellow / Substandart) and legal foreclosure at **90 days overdue** (Red / NPL). Relying solely on static overdue days means the bank acts only *after* default has set in.
2. **Seasonal Variance:** Agricultural and textile businesses fluctuate naturally across seasons. A fixed percentage threshold triggers false alarms during scheduled downtimes.
3. **Fragmented Field Reports:** Field inspection acts (*Monitoring Dalolatnomasi*) are completed in Word and PDF by branch officers, remaining siloed from real-time core banking alerts.

---

## How XERJ Solves It

```
                               ┌──────────────────────────────────────────────┐
                               │       Daily Core Banking Account Feeds       │
                               │  (Turnover UZS, K-2 Arrears, Smart Meters)   │
                               └──────────────────────┬───────────────────────┘
                                                      │
                                                      ▼
                               ┌──────────────────────────────────────────────┐
                               │      XERJ Node (Single Rust Binary)          │
                               │                                              │
                               │  1. Moving-Window z-Score (_ml)              │
                               │     - Learns normal borrower variance        │
                               │     - Flags anomalous 3σ breaks              │
                               │  2. Continuous Background Datafeed           │
                               │     - Scores incoming days on a timer        │
                               │  3. Namespaced Qualitative Memory            │
                               │     - /_memory/{inn} for inspection acts     │
                               └──────────────────────┬───────────────────────┘
                                                      │
                                                      ▼
                               ┌──────────────────────────────────────────────┐
                               │    NazoratAI Early Warning Risk Pipeline     │
                               │  - Multi-class ML Classifier + TreeSHAP      │
                               │  - Automated ReportLab PDF Audit Dossiers    │
                               │  - Streamlit Executive Watchlist Radar       │
                               └──────────────────────────────────────────────┘
```

1. **Statistical Anomaly Detection (`_ml/anomaly_detectors` & `_ml/datafeeds`):**
   XERJ's Elasticsearch-compatible moving-window $z$-score engine learns each borrower's normal turnover band and flags acute deviations without hand-tuned hardcoded limits.
2. **Namespaced Inspection Memory (`/_memory/{borrower_inn}`):**
   Each corporate borrower's INN is an isolated namespace storing qualitative field inspection notes, recallable via BM25, dense vectors, or hybrid fusion.

---

## Walkthrough

### 1. Map the Credit Telemetry Index

```bash
curl -XPUT localhost:9200/corporate_credit_telemetry -H 'Content-Type: application/json' -d '{
  "mappings": {
    "properties": {
      "@timestamp":         { "type": "date" },
      "inn":                { "type": "keyword" },
      "company_name":       { "type": "text" },
      "daily_turnover_uzs": { "type": "double" },
      "k2_card_index_uzs":  { "type": "double" },
      "electricity_kwh":    { "type": "double" }
    }
  }
}'
```

### 2. Create the Moving-Window Anomaly Detector

Point the detector at `daily_turnover_uzs` with a 1-day bucket span and a 3.0$\sigma$ threshold:

```bash
curl -XPUT localhost:9200/_ml/anomaly_detectors/turnover-slump-detector \
  -H 'Content-Type: application/json' -d '{
    "source_index": "corporate_credit_telemetry",
    "time_field":   "@timestamp",
    "function":     "mean",
    "field":        "daily_turnover_uzs",
    "bucket_span":  "1d",
    "anomaly_threshold": 3.0,
    "description":  "Daily account turnover collapse early warning"
  }'
```

### 3. Attach a Continuous Datafeed

Attach a datafeed that watches incoming Core Banking batches every minute:

```bash
curl -XPUT localhost:9200/_ml/datafeeds/turnover-feed \
  -H 'Content-Type: application/json' -d '{
    "job_id":    "turnover-slump-detector",
    "frequency": "60s"
  }'

curl -XPOST localhost:9200/_ml/datafeeds/turnover-feed/_start
```

### 4. Qualitative Field Memory (`/_memory/{inn}`)

When a branch credit officer visits the borrower's production site, field findings are stored directly into XERJ's isolated memory namespace:

```bash
curl -XPOST localhost:9200/_memory/300001000 -H 'Content-Type: application/json' -d '{
  "text": "Favqulodda monitoring: Klasterga qarashli yigiruv sexida ta'mirlash ishlari cho'zilgan, asosiy xom-ashyo yetkazib berilishi to'xtagan.",
  "metadata": {
    "source": "NazoratAI Monitoring Dalolatnomasi",
    "inspector": "BXM Credit Officer",
    "risk_flag": "OPERATIONAL_HALT"
  },
  "id": "audit-act-20261015"
}'
```

### 5. Recall Findings for Audit Dossiers

When assembling the executive credit audit dossier, query the borrower's memory with hybrid fusion:

```bash
curl -XPOST localhost:9200/_memory/300001000/_recall -H 'Content-Type: application/json' -d '{
  "query": "xom ashyo ta'minoti to'xtagan",
  "hybrid": true,
  "k": 3
}'
```

---

## Executable Recipe

A complete standalone script is available at [`recipes/banking_credit_ews.py`](../../recipes/banking_credit_ews.py).

Run it:

```bash
xerj --insecure --data-dir ~/xerj-data &
python3 recipes/banking_credit_ews.py
```

---

## Acknowledgments & Co-Credits

This integration is co-authored by:
* **[Xajibayev Azizbek](https://github.com/Zizx4uM)** — Creator and Lead Architect of [NazoratAI](https://github.com/Zizx4uM/NazoratAI), commercial banking credit surveillance and early warning platform.
* **[XERJ Open Source Community](https://github.com/xerj-org/xerj)** — Local-first high-speed search, anomaly detection, and vector engine.
