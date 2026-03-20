#!/usr/bin/env python3
import json
import sqlite3
import pandas as pd
import os
from datetime import datetime

DB_NAME = "db/analytics.db"
SCHEMA_FILE = "db/database_schema.sql"
TELEMETRY_FILE = "data/telemetry_logs.jsonl"
EMPLOYEE_FILE = "data/employees.csv"

def init_db():
    print(f"Initializing database {DB_NAME}...")
    conn = sqlite3.connect(DB_NAME)
    with open(SCHEMA_FILE, 'r') as f:
        schema = f.read()
    conn.executescript(schema)
    conn.commit()
    return conn

def ingest_employees(conn):
    print(f"Ingesting employees from {EMPLOYEE_FILE}...")
    df = pd.read_csv(EMPLOYEE_FILE)
    df.to_sql('employees', conn, if_exists='replace', index=False)
    print(f"  Ingested {len(df)} employees.")

def parse_event(event_id, event_data):
    """Extracts relevant fields from a single telemetry event."""
    body = event_data.get("body", "")
    attrs = event_data.get("attributes", {})
    
    # Common fields
    ts_str = attrs.get("event.timestamp", "")
    if ts_str.endswith("Z"):
        ts_str = ts_str[:-1]
    
    try:
        timestamp = datetime.fromisoformat(ts_str)
    except ValueError:
        timestamp = None

    return {
        "id": event_id,
        "timestamp": timestamp,
        "event_body": body,
        "event_name": attrs.get("event.name", ""),
        "session_id": attrs.get("session.id", ""),
        "user_id": attrs.get("user.id", ""),
        "email": attrs.get("user.email", ""),
        "model": attrs.get("model", None),
        "cost_usd": float(attrs.get("cost_usd", 0)) if attrs.get("cost_usd") else 0.0,
        "input_tokens": int(attrs.get("input_tokens", 0)) if attrs.get("input_tokens") else 0,
        "output_tokens": int(attrs.get("output_tokens", 0)) if attrs.get("output_tokens") else 0,
        "cache_read_tokens": int(attrs.get("cache_read_tokens", 0)) if attrs.get("cache_read_tokens") else 0,
        "cache_creation_tokens": int(attrs.get("cache_creation_tokens", 0)) if attrs.get("cache_creation_tokens") else 0,
        "duration_ms": int(attrs.get("duration_ms", 0)) if attrs.get("duration_ms") else 0,
        "tool_name": attrs.get("tool_name", None),
        "decision": attrs.get("decision", None),
        "success": attrs.get("success", "false").lower() == "true",
        "prompt_length": int(attrs.get("prompt_length", 0)) if attrs.get("prompt_length") else 0,
        "error_message": attrs.get("error", None),
        "status_code": attrs.get("status_code", None)
    }

def ingest_telemetry(conn):
    print(f"Ingesting telemetry from {TELEMETRY_FILE}...")
    events_to_insert = []
    
    if not os.path.exists(TELEMETRY_FILE):
        print(f"Error: {TELEMETRY_FILE} not found.")
        return

    with open(TELEMETRY_FILE, 'r') as f:
        for line_num, line in enumerate(f):
            try:
                batch = json.loads(line)
                log_events = batch.get("logEvents", [])
                for log_event in log_events:
                    event_id = log_event.get("id")
                    message_json = log_event.get("message", "{}")
                    event_data = json.loads(message_json)
                    parsed = parse_event(event_id, event_data)
                    events_to_insert.append(parsed)
            except Exception as e:
                print(f"Error parsing line {line_num + 1}: {e}")

    if events_to_insert:
        df = pd.DataFrame(events_to_insert)
        df.to_sql('events', conn, if_exists='append', index=False)
        print(f"  Ingested {len(events_to_insert)} events.")

def main():
    conn = init_db()
    try:
        ingest_employees(conn)
        ingest_telemetry(conn)
        print("Ingestion complete.")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
