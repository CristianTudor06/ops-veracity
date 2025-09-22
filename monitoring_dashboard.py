# monitoring_dashboard.py
import streamlit as st
import pandas as pd
import sqlite3
import altair as alt

DB_PATH = "db/queries.db" # Path inside the container

st.set_page_config(
    page_title="Veracity Monitoring",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Veracity - Monitoring Dashboard")
st.info("This dashboard displays a live log of all queries made to the AI detection model.")

# --- Database Connection ---
def get_data():
    """Fetch all data from the SQLite database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        # Use pandas to read the SQL query directly into a DataFrame
        df = pd.read_sql_query("SELECT * FROM queries ORDER BY timestamp DESC", conn)
        conn.close()
        # Convert timestamp to a readable format
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    except Exception as e:
        st.error(f"Failed to connect to the database: {e}")
        return pd.DataFrame() # Return empty dataframe on error

df = get_data()

if df.empty:
    st.warning("No queries have been logged yet. Use the main app to analyze some text.")
else:
    # --- KPIs Section ---
    st.subheader("Key Performance Indicators")
    total_queries = len(df)
    avg_response_time = df['processing_time_seconds'].mean()
    ai_predictions = df[df['prediction'] == 'AI-generated'].shape[0]
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Queries", f"{total_queries}")
    col2.metric("Avg. Response Time", f"{avg_response_time:.4f}s")
    col3.metric("AI Detections", f"{ai_predictions}")

    # --- Charts Section ---
    st.subheader("Visualizations")
    col1, col2 = st.columns(2)

    with col1:
        # Bar chart for predictions
        st.write("#### Prediction Breakdown")
        pred_chart = alt.Chart(df).mark_bar().encode(
            x='count()',
            y=alt.Y('prediction:N', title='Prediction'),
            color='prediction:N'
        ).properties(
            height=300
        )
        st.altair_chart(pred_chart, use_container_width=True)

    with col2:
        # Line chart for response times
        st.write("#### Response Time Over Time")
        time_chart = alt.Chart(df).mark_line().encode(
            x=alt.X('timestamp:T', title='Time'),
            y=alt.Y('processing_time_seconds:Q', title='Response Time (s)')
        ).properties(
            height=300
        )
        st.altair_chart(time_chart, use_container_width=True)

    # --- Raw Data Log ---
    st.subheader("Query Log")
    # Display the dataframe with a cleaner look
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "timestamp": st.column_config.DatetimeColumn("Time"),
            "query_text": st.column_config.TextColumn("Query Text", width="large"),
        }
    )