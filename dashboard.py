import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.analytics_engine import (
    get_overall_metrics,
    get_token_usage_by_model,
    get_daily_usage_trends,
    get_tool_usage_stats,
    get_usage_by_practice,
    get_error_rates,
    get_connection
)

@st.cache_data
def get_filtered_data(practice_filter, level_filter):
    # Only select columns we actually use in the dashboard to reduce memory and transfer time
    columns = "ev.id, ev.timestamp, ev.event_name, ev.session_id, ev.email, ev.model, ev.cost_usd, ev.input_tokens, ev.output_tokens, ev.duration_ms, ev.success, ev.tool_name"
    query = """
    SELECT {columns}, e.practice, e.level 
    FROM events ev
    JOIN employees e ON ev.email = e.email
    WHERE (e.practice IN ({practice_placeholders}) OR {practice_all})
    AND (e.level IN ({level_placeholders}) OR {level_all})
    """
    
    params = []
    practice_placeholders = ",".join(["?"] * len(practice_filter)) if practice_filter else "NULL"
    practice_all = "1" if not practice_filter else "0"
    params.extend(practice_filter)
    
    level_placeholders = ",".join(["?"] * len(level_filter)) if level_filter else "NULL"
    level_all = "1" if not level_filter else "0"
    params.extend(level_filter)
    
    final_query = query.format(
        columns=columns,
        practice_placeholders=practice_placeholders,
        practice_all=practice_all,
        level_placeholders=level_placeholders,
        level_all=level_all
    )
    
    with get_connection() as conn:
        return pd.read_sql_query(final_query, conn, params=params)

# Page configuration
st.set_page_config(
    page_title="Claude Code Usage Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Styling
st.markdown("""
<style>
    .main {
        background-color: #0e1117;
    }
    .stMetric {
        background-color: #161b22;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #30363d;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.title("Claude Code Analytics Platform")

# Filters
with get_connection() as conn:
    practices = pd.read_sql_query("SELECT DISTINCT practice FROM employees", conn)['practice'].tolist()
    levels = pd.read_sql_query("SELECT DISTINCT level FROM employees ORDER BY level", conn)['level'].tolist()

selected_practices = st.sidebar.multiselect("Filter by Practice", practices)
selected_levels = st.sidebar.multiselect("Filter by Level", levels)

st.sidebar.info("This dashboard provides insights into Claude Code telemetry data across the engineering organization.")

# Header
st.title("📊 Claude Code Usage Analytics")
st.markdown("---")

# Data loading with filters
filtered_df = get_filtered_data(tuple(selected_practices), tuple(selected_levels))

if filtered_df.empty:
    st.warning("No data found for the selected filters.")
    st.stop()

# Metrics Overview
# Note: Since the metrics and complex aggregates are now filtered, we compute them from the fetched dataframe
total_tokens = filtered_df['input_tokens'].sum() + filtered_df['output_tokens'].sum()
total_cost = filtered_df['cost_usd'].sum()
total_sessions = filtered_df['session_id'].nunique()
total_users = filtered_df['email'].nunique()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Cost (USD)", f"${total_cost:,.2f}")
with col2:
    st.metric("Total Tokens", f"{total_tokens:,.0f}")
with col3:
    st.metric("Total Sessions", f"{total_sessions:,.0f}")
with col4:
    st.metric("Active Users", f"{total_users:,.0f}")

st.markdown("---")

# Row 1: Trends
st.subheader("📈 Usage Trends Over Time")
trends_df = filtered_df.copy()
trends_df['date'] = pd.to_datetime(trends_df['timestamp'], errors='coerce').dt.date
daily_trends = trends_df.groupby('date').agg({
    'cost_usd': 'sum',
    'input_tokens': 'sum',
    'output_tokens': 'sum',
    'session_id': 'nunique'
}).reset_index()
daily_trends['daily_tokens'] = daily_trends['input_tokens'] + daily_trends['output_tokens']

tab1, tab2 = st.tabs(["Token Usage", "Cost & Sessions"])

with tab1:
    fig_tokens = px.area(
        daily_trends, x="date", y="daily_tokens",
        title="Daily Token Consumption",
        color_discrete_sequence=["#58a6ff"],
        labels={"daily_tokens": "Total Tokens"}
    )
    fig_tokens.update_layout(template="plotly_dark", height=400)
    st.plotly_chart(fig_tokens, use_container_width=True)

with tab2:
    fig_cost = px.line(
        daily_trends, x="date", y=["cost_usd", "session_id"],
        title="Daily Cost and Session Count",
        labels={"value": "Count / USD", "cost_usd": "Cost (USD)", "session_id": "Sessions"},
        template="plotly_dark",
        height=400
    )
    st.plotly_chart(fig_cost, use_container_width=True)

# Row 2: Model and Practice Analysis
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("🤖 Model Distribution")
    model_dist = filtered_df[filtered_df['event_name'] == 'api_request'].groupby('model')['cost_usd'].sum().reset_index()
    fig_model = px.pie(
        model_dist, values="cost_usd", names="model",
        hole=0.4, title="Cost Share by Model",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig_model.update_layout(template="plotly_dark", height=400)
    st.plotly_chart(fig_model, use_container_width=True)

with col_right:
    st.subheader("🏢 Usage by Engineering Practice")
    practice_dist = filtered_df.groupby('practice')['cost_usd'].sum().reset_index()
    fig_practice = px.bar(
        practice_dist, x="practice", y="cost_usd",
        title="Total Cost by Practice",
        color="practice",
        template="plotly_dark",
        height=400
    )
    st.plotly_chart(fig_practice, use_container_width=True)

# Row 3: Tool Performance
st.subheader("🛠️ Tool Performance and Popularity")
tool_summary = filtered_df[filtered_df['event_name'].isin(['tool_result', 'tool_decision']) & filtered_df['tool_name'].notnull()]
tool_stats = tool_summary.groupby('tool_name').agg({
    'id': 'count',
    'duration_ms': 'mean',
    'success': 'mean'
}).reset_index().rename(columns={'id': 'usage_count', 'duration_ms': 'avg_duration_ms', 'success': 'success_rate'})
tool_stats['success_rate'] *= 100

col_t1, col_t2 = st.columns([2, 1])

with col_t1:
    fig_tool_usage = px.bar(
        tool_stats.sort_values("usage_count", ascending=False).head(10), x="tool_name", y="usage_count",
        title="Top 10 Most Used Tools",
        color="success_rate",
        color_continuous_scale="RdYlGn",
        labels={"usage_count": "Calls", "success_rate": "Success %"},
        template="plotly_dark",
        height=400
    )
    st.plotly_chart(fig_tool_usage, use_container_width=True)

with col_t2:
    st.write("Average Duration (ms) by Tool")
    st.dataframe(
        tool_stats[["tool_name", "avg_duration_ms", "success_rate"]].sort_values("avg_duration_ms", ascending=False).head(15),
        use_container_width=True,
        hide_index=True
    )

# Footer
st.markdown("---")
