#!/usr/bin/env python3
"""Banking Corporate Credit Monitoring & Early Warning System (EWS) with XERJ.

Demonstrates how commercial banks and lending institutions use XERJ's:
1. Moving-window z-score anomaly detectors (_ml/anomaly_detectors) and continuous
   background datafeeds (_ml/datafeeds) to detect early enterprise distress (turnover slump,
   K-2 card index debt accumulation) before statutory delinquency cliffs.
2. Namespaced agent memory (/_memory/{borrower_inn}) to store qualitative field
   inspection acts (Monitoring Dalolatnomasi) and recall historical findings via hybrid search.

Co-developed in collaboration between NazoratAI (https://github.com/Zizx4uM/NazoratAI)
and the XERJ Community.
Author: Xajibayev Azizbek (@Zizx4uM) & XERJ Community.

Run it:
    xerj --insecure --data-dir ./data &        # start XERJ
    python3 recipes/banking_credit_ews.py

Optional env:
    XERJ_URL   (default http://localhost:9200)
"""

import datetime
import json
import os
import sys
import time
import urllib.error
import urllib.request

XERJ = os.environ.get("XERJ_URL", "http://localhost:9200").rstrip("/")
INDEX = "corporate_credit_telemetry"
DETECTOR = "borrower-turnover-slump"
DATAFEED = "borrower-turnover-feed"
BORROWER_INN = "300001000"  # Agro Tex Klaster MCHJ


def call(method, path, body=None):
    data = None
    headers = {}
    if body is not None:
        data = body.encode() if isinstance(body, str) else json.dumps(body).encode()
        headers["Content-Type"] = (
            "application/x-ndjson" if isinstance(body, str) else "application/json"
        )
    req = urllib.request.Request(f"{XERJ}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read()
            return json.loads(content) if content else {}
    except urllib.error.HTTPError as exc:
        err = exc.read().decode("utf-8", errors="replace")
        print(f"HTTP {exc.code} on {path}: {err}", file=sys.stderr)
        raise


def check_server():
    try:
        req = urllib.request.Request(f"{XERJ}/", method="GET")
        with urllib.request.urlopen(req) as resp:
            return resp.status == 200
    except Exception:
        return False


def main():
    print("=" * 72)
    print("  NazoratAI + XERJ: Banking Credit Early Warning Surveillance")
    print("  Developed by Xajibayev Azizbek (@Zizx4uM) & XERJ Community")
    print("=" * 72)

    if not check_server():
        print(f"XERJ server not reachable at {XERJ}.")
        print("Please start XERJ first:  xerj --insecure --data-dir ~/xerj-data &")
        sys.exit(0)

    # 1. Map telemetry index
    print("\n1. Mapping corporate credit telemetry index...")
    mapping = {
        "mappings": {
            "properties": {
                "@timestamp": {"type": "date"},
                "inn": {"type": "keyword"},
                "company_name": {"type": "text"},
                "daily_turnover_uzs": {"type": "double"},
                "k2_card_index_uzs": {"type": "double"},
                "electricity_kwh": {"type": "double"},
            }
        }
    }
    call("PUT", f"/{INDEX}", mapping)
    print(f"   Mapped index: {INDEX}")

    # 2. Ingest baseline time series (14 healthy days ~100M UZS daily turnover)
    print("\n2. Ingesting baseline borrower transactions (14 days healthy band)...")
    ndjson = []
    base_date = datetime.date(2026, 10, 1)
    for day in range(1, 15):
        ts = f"2026-10-{day:02d}T09:00:00Z"
        turnover = 100_000_000.0 + (day % 3) * 2_000_000.0
        doc = {
            "@timestamp": ts,
            "inn": BORROWER_INN,
            "company_name": "Agro Tex Klaster MCHJ",
            "daily_turnover_uzs": turnover,
            "k2_card_index_uzs": 0.0,
            "electricity_kwh": 4500.0,
        }
        ndjson.append(json.dumps({"index": {"_index": INDEX}}))
        ndjson.append(json.dumps(doc))

    # Ingest day 15: Acute Turnover Slump (-80% collapse, factory stopped)
    doc_spike = {
        "@timestamp": "2026-10-15T09:00:00Z",
        "inn": BORROWER_INN,
        "company_name": "Agro Tex Klaster MCHJ",
        "daily_turnover_uzs": 18_000_000.0,  # Sudden 82% collapse
        "k2_card_index_uzs": 450_000_000.0,  # Emergence of 2-Kartoteka debt
        "electricity_kwh": 800.0,
    }
    ndjson.append(json.dumps({"index": {"_index": INDEX}}))
    ndjson.append(json.dumps(doc_spike))

    call("POST", "/_bulk?refresh=true", "\n".join(ndjson) + "\n")
    print("   Ingested 15 days of borrower telemetry.")

    # 3. Create Moving-Window Anomaly Detector
    print("\n3. Creating moving-window z-score anomaly detector...")
    detector_config = {
        "source_index": INDEX,
        "time_field": "@timestamp",
        "function": "mean",
        "field": "daily_turnover_uzs",
        "bucket_span": "1d",
        "anomaly_threshold": 3.0,
        "description": "Daily turnover moving average early warning detector",
    }
    call("PUT", f"/_ml/anomaly_detectors/{DETECTOR}", detector_config)
    print(f"   Created detector: {DETECTOR}")

    # 4. Score on-demand
    print("\n4. Scoring borrower anomaly series...")
    score_res = call("POST", f"/_ml/anomaly_detectors/{DETECTOR}/_score")
    records = score_res.get("records", [])
    print(f"   Flagged {len(records)} anomalies breaking the 3σ baseline:")
    for r in records:
        print(f"   - Timestamp: {r.get('timestamp')}, Actual: {r.get('actual'):,.0f} UZS, Score: {r.get('record_score', 0):.2f}")

    # 5. Store qualitative field audit memory
    print(f"\n5. Storing field inspection observation into XERJ memory for INN {BORROWER_INN}...")
    mem_payload = {
        "text": "Favqulodda monitoring: Klasterga qarashli yigiruv sexida ta'mirlash ishlari cho'zilgan, asosiy xom-ashyo yetkazib berilishi to'xtagan.",
        "metadata": {
            "source": "NazoratAI Monitoring Dalolatnomasi",
            "inspector": "BXM Credit Officer",
            "date": "2026-10-15",
            "risk_flag": "OPERATIONAL_HALT",
        },
        "id": "audit-act-20261015",
    }
    call("POST", f"/_memory/{BORROWER_INN}", mem_payload)
    print("   Memory registered successfully.")

    # 6. Hybrid recall for credit dossier
    print("\n6. Recalling borrower memory for automated credit dossier...")
    recall_res = call("POST", f"/_memory/{BORROWER_INN}/_recall", {"query": "xom ashyo ta'minoti to'xtagan", "k": 3})
    hits = recall_res.get("hits", [])
    for h in hits:
        print(f"   [Score: {h.get('score', 0):.2f}] {h.get('text')}")

    print("\n" + "=" * 72)
    print("  ✅ NazoratAI + XERJ EWS workflow completed successfully.")
    print("=" * 72)


if __name__ == "__main__":
    main()
