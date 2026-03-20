import sqlite3
import pandas as pd

DB_NAME = "db/analytics.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def get_token_usage_by_model():
    query = """
    SELECT 
        model,
        SUM(input_tokens) as total_input_tokens,
        SUM(output_tokens) as total_output_tokens,
        SUM(cost_usd) as total_cost_usd,
        COUNT(*) as request_count
    FROM events
    WHERE event_name = 'api_request'
    GROUP BY model
    ORDER BY total_cost_usd DESC
    """
    with get_connection() as conn:
        return pd.read_sql_query(query, conn)

def get_daily_usage_trends():
    query = """
    SELECT 
        DATE(timestamp) as date,
        SUM(cost_usd) as daily_cost,
        SUM(input_tokens + output_tokens) as daily_tokens,
        COUNT(DISTINCT session_id) as daily_sessions,
        COUNT(DISTINCT email) as active_users
    FROM events
    GROUP BY date
    ORDER BY date
    """
    with get_connection() as conn:
        df = pd.read_sql_query(query, conn)
        df['date'] = pd.to_datetime(df['date'])
        return df

def get_tool_usage_stats():
    query = """
    SELECT 
        tool_name,
        COUNT(*) as usage_count,
        AVG(duration_ms) as avg_duration_ms,
        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as success_rate
    FROM events
    WHERE event_name IN ('tool_result', 'tool_decision')
    AND tool_name IS NOT NULL
    GROUP BY tool_name
    ORDER BY usage_count DESC
    """
    with get_connection() as conn:
        return pd.read_sql_query(query, conn)

def get_usage_by_practice():
    query = """
    SELECT 
        e.practice,
        SUM(ev.cost_usd) as total_cost,
        SUM(ev.input_tokens + ev.output_tokens) as total_tokens,
        COUNT(DISTINCT ev.email) as user_count
    FROM events ev
    JOIN employees e ON ev.email = e.email
    GROUP BY e.practice
    ORDER BY total_cost DESC
    """
    with get_connection() as conn:
        return pd.read_sql_query(query, conn)

def get_error_rates():
    query = """
    SELECT 
        model,
        COUNT(*) as error_count,
        status_code,
        error_message
    FROM events
    WHERE event_name = 'api_error'
    GROUP BY model, status_code, error_message
    ORDER BY error_count DESC
    """
    with get_connection() as conn:
        return pd.read_sql_query(query, conn)

def get_overall_metrics():
    query = """
    SELECT 
        SUM(cost_usd) as total_cost,
        SUM(input_tokens + output_tokens) as total_tokens,
        COUNT(DISTINCT session_id) as total_sessions,
        COUNT(DISTINCT email) as total_users
    FROM events
    """
    with get_connection() as conn:
        return pd.read_sql_query(query, conn).iloc[0].to_dict()

if __name__ == "__main__":
    # Quick test
    print("Overall Metrics:", get_overall_metrics())
    print("\nToken Usage by Model:\n", get_token_usage_by_model())
