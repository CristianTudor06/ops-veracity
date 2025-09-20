# dashboard/dashboard.py
import streamlit as st
import requests
import time
import pandas as pd
import altair as alt



# --- THIS IS THE NEW CODE BLOCK ---
# Set the page configuration. This MUST be the first Streamlit command.
st.set_page_config(
    page_title="Ipsos Veracity",  # The title of the browser tab
    page_icon="🤖",                # The icon of the browser tab (can be an emoji)
    layout="wide"                 # Use the full width of the page
)
# --- END OF NEW CODE BLOCK ---

API_URL = "http://api:8000" # The name of the service in docker-compose

st.set_page_config(layout="wide")
st.title("Ipsos Veracity: AI Text Detection")

input_text = st.text_area(
    "Enter text to analyze:",
    "This is an example of text written by a human. It contains nuance, some minor grammatical imperfections, and a personal tone.",
    height=200
)

if st.button("Analyze Text"):
    if not input_text.strip():
        st.warning("Please enter some text to analyze.")
    else:
        with st.spinner("Submitting text for analysis..."):
            try:
                # 1. Submit the task
                submit_response = requests.post(f"{API_URL}/analyze", json={"text": input_text})
                submit_response.raise_for_status()
                task_id = submit_response.json()["task_id"]
                st.session_state['task_id'] = task_id
            except requests.exceptions.RequestException as e:
                st.error(f"Error connecting to the API: {e}")
                st.stop()

        # 2. Poll for the result
        with st.spinner("Model is processing... Please wait."):
            result_data = None
            while True:
                try:
                    result_response = requests.get(f"{API_URL}/results/{st.session_state['task_id']}")
                    result_response.raise_for_status()
                    result_data = result_response.json()
                    
                    if result_data["status"] == "complete":
                        break
                    time.sleep(1) # Wait 1 second before polling again
                except requests.exceptions.RequestException as e:
                    st.error(f"Error fetching results: {e}")
                    st.stop()
        
        # 3. Display the result
        st.success("Analysis Complete!")
        result = result_data["result"]
        
        prediction = result["prediction"]
        confidence = result["confidence"]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(label="Prediction", value=prediction)
        
        with col2:
            st.metric(label="Confidence Score", value=f"{confidence}%")

        # Visualize confidence
        if prediction == "AI-generated":
            progress_color = "red"
        else:
            progress_color = "green"
        
        st.write("### Confidence breakdown:")
        df = pd.DataFrame({
            "Category": ["AI-Generated", "Human-Written"],
            "Probability": [confidence, 100-confidence] if prediction == "AI-generated" else [100-confidence, confidence]
        })
        chart = alt.Chart(df).mark_bar().encode(
            x=alt.X('Category', sort=None), # sort=None keeps the order as is
            y='Probability',
            color=alt.Color('Category', scale=alt.Scale(domain=['Human-Written', 'AI-Generated'], range=['#2ca02c', '#d62728'])) # Green for Human, Red for AI
        ).properties(
            title='Prediction Probability'
        )
        st.altair_chart(chart, use_container_width=True)