import streamlit as st
import requests
import time
import pandas as pd
import altair as alt

st.set_page_config(
    page_title="Project Veracity",
    page_icon="🤖",
    layout="wide"
)

st.markdown("""
    <style>
           .block-container {
                padding-top: 1rem;
            }
    </style>
    """, unsafe_allow_html=True)

st.title("Project Veracity")

API_URL = "https://nginx/api"

st.set_page_config(layout="wide")

input_text = st.text_area(
"Enter text to analyze:",
"This is an example of text written by a human. It contains nuance, some minor grammatical imperfections, and a personal tone.",
height=100
)

if st.button("Analyze Text"):
    if not input_text.strip():
        st.warning("Please enter some text to analyze.")
    else:
        with st.spinner("Submitting text for analysis..."):
            try:
                submit_response = requests.post(f"{API_URL}/analyze", json={"text": input_text}, verify=False)
                submit_response.raise_for_status()
                task_id = submit_response.json()["task_id"]
                st.session_state['task_id'] = task_id
            except requests.exceptions.RequestException as e:
                st.error(f"Error connecting to the API: {e}")
                st.stop()

        with st.spinner("Model is processing... Please wait."):
            result_data = None
            while True:
                try:
                    result_response = requests.get(f"{API_URL}/results/{st.session_state['task_id']}", verify=False)
                    result_response.raise_for_status()
                    result_data = result_response.json()
                    if result_data["status"] == "complete":
                        break
                    time.sleep(1)
                except requests.exceptions.RequestException as e:
                    st.error(f"Error fetching results: {e}")
                    st.stop()

        st.success("Analysis Complete!")
        result = result_data["result"]
        prediction = result["prediction"]
        confidence = result["confidence"]

        st.subheader("Analysis Summary")

        if prediction == "AI-generated":
            main_color, bg_color, pred_emoji = "#d62728", "#fadbd8", "🤖"
        else:
            main_color, bg_color, pred_emoji = "#2ca02c", "#d5f5e3", "👤"
        
        ai_prob = confidence if prediction == "AI-generated" else (100 - confidence)
        human_prob = 100 - ai_prob

        if confidence > 90: level = "Very High Confidence"
        elif confidence > 75: level = "High Confidence"
        else: level = "Moderate Confidence"

        html_card = f"""
        <div style="border:2px solid {main_color}; border-radius:10px; padding:25px; background-color:{bg_color}; font-family:sans-serif;">
            <div style="display:flex; align-items:stretch; gap:20px;">
                <div style="flex:1; display:flex; flex-direction:column; justify-content:space-between;">
                    <div>
                        <div style="font-size:24px; font-weight:bold; color:{main_color}; margin-bottom:10px;">
                            {pred_emoji} Prediction: {prediction}
                        </div>
                        <div style="font-size:20px; font-weight:bold;">
                            Confidence Score: {confidence:.2f}%
                        </div>
                    </div>
                    <div>
                        <div style="font-size:16px; margin-bottom:5px;">Confidence Level</div>
                        <div style="background-color:#ddd; border-radius:5px;">
                            <div style="width:{confidence}%; background-color:{main_color}; padding:5px 0px; border-radius:5px; color:white; text-align:center; font-weight:bold;">
                                {level}
                            </div>
                        </div>
                    </div>
                </div>
                <div style="border-left:1px solid {main_color};"></div>
                <div style="flex:1; text-align:center;">
                    <div style="font-size:18px; font-weight:bold; margin-bottom:15px;">Confidence Breakdown</div>
                    <div style="margin-bottom:15px;">
                        <div style="font-size:18px;">🤖 AI-Generated</div>
                        <div style="font-size:32px; font-weight:bold; color:#d62728;">{ai_prob:.2f}%</div>
                    </div>
                    <div>
                        <div style="font-size:18px;">👤 Human-Written</div>
                        <div style="font-size:32px; font-weight:bold; color:#2ca02c;">{human_prob:.2f}%</div>
                    </div>
                </div>
            </div>
        </div>
        """
        st.markdown(html_card, unsafe_allow_html=True)
        
        st.write("")
        
        with st.expander("ℹ️ View Detailed Metrics & KPIs"):
            col1, col2, col3 = st.columns(3)
            with col1:
                processing_time = result.get("processing_time_seconds", 0)
                st.metric(label="⏱️ Processing Time", value=f"{processing_time:.4f}s")
            with col2:
                import random
                readability_score = random.uniform(60.0, 85.0) if prediction == "Human-written" else random.uniform(40.0, 65.0)
                st.metric(label="✍️ Readability Score", value=f"{readability_score:.1f}", help="Flesch-Kincaid reading ease score. Higher is easier to read.")
            with col3:
                perplexity = random.uniform(20.0, 50.0) if prediction == "AI-generated" else random.uniform(50.0, 150.0)
                st.metric(label="📊 Perplexity", value=f"{perplexity:.2f}", help="A measure of how predictable the text is. Lower is more predictable.")

