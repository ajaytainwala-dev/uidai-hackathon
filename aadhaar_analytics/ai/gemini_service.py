
import os
import google.generativeai as genai
import logging

class GeminiService:
    def __init__(self, api_key):
        self.api_key = api_key
        self.model = None
        self.setup()

    def setup(self):
        if not self.api_key:
            return
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        except Exception as e:
            logging.error(f"Failed to setup Gemini: {e}")

    def generate_response(self, prompt):
        if not self.model:
            return "⚠️ Gemini API Key not provided or invalid. Please check the sidebar."
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"❌ Error generating AI response: {str(e)}"

    def explain_kpis(self, kpis, state_filter):
        prompt = f"""
        You are the **Chief Data Strategy Officer for the Government of India (UIDAI)**.
        
        **Objective**: Decode societal trends from Aadhaar usage statistics to guide national policy.
        
        **Context**: Analyzing ecosystem health for Region: **{state_filter or 'All India'}**.
        
        **Data Snapshot**:
        - **Total Enrolment Base**: {kpis.get('total_enrolments')} (Represents the static population backbone)
        - **Demographic Updates**: {kpis.get('total_demo_updates')} (Represents societal mobility: migration, marriage, name corrections)
        - **Biometric Updates**: {kpis.get('total_bio_updates')} (Represents aging population & child-to-adult transitions)
        
        **Analysis Required**:
        1.  **Maturity Diagnosis**: Is this region in 'Acquisition Mode' (High Enrolment) or 'Maintenance Mode' (High Updates)? What does this say about the region's development?
        2.  **Societal Indicator**: High Demographic updates often correlate with high migration or urbanization. High Biometric updates correlate with a strict compliance ecosystem (Schools/Banks). Interpret the ratio.
        3.  **Risk Flag**: Does the data suggest "Data Rot"? (e.g. if Enrolment is high but Updates are near zero, residents are holding obsolete data).
        
        **Output**: Provide a sharp, executive-level insight block (2-3 sentences max) focusing on the *implications* of these numbers, not just restating them. Use bolding for emphasis.
        """
        return self.generate_response(prompt)

    def analyze_trends(self, trend_df, context="Enrolment"):
        # Summarize data for prompt to save tokens
        summary = trend_df.to_csv(index=False)
        
        prompt = f"""
        You are a **Special Investigator for Demographic Anomalies**.
        
        **Context**: You are analyzing **{context}** trends over time to detect hidden societal patterns.
        
        **Data Stream (CSV)**:
        {summary}
        
        **Investigative Tasks**:
        1.  **Pattern Recognition**: Identify seasonality linked to Indian societal events (e.g., Peaks in May-July = School Admissions? Peaks in March = Financial Year benefits?).
        2.  **Anomaly Detection**: Spot any "Non-Organic" spikes. A sudden vertical surge in a specific age group without a clear driver is a **security red flag** (Potential Fraud/Infiltration).
        3.  **Future Projection**: Based on the trajectory, look 3 months ahead. Are we facing a capacity crash?
        
        **Output Format**:
        - **🎯 Primary Driver**: The main societal force driving current numbers.
        - **⚠️ Critical Anomaly**: Any data point that looks suspicious or broken.
        - **🔮 Strategic Forecast**: One sentence prediction for the next quarter.
        """
        return self.generate_response(prompt)

    def recommend_policy(self, high_pressure_districts):
        if high_pressure_districts.empty:
            return "✅ **System Status Green**: No immediate critical interventions required. Maintain current operational cadence."
            
        # Take top 5 for context
        top_5 = high_pressure_districts.head(5).to_dict(orient='records')
        
        prompt = f"""
        You are the **Principal Advisor to the CEO of UIDAI**.
        
        **Problem Statement**: The following districts are showing **Critical Stress Signs** (High Enrolment/Update ratios vs Capacity).
        
        **Critical Zones**:
        {top_5}
        
        **Task**: Draft a **Ministerial Decision Note** to resolve this bottleneck immediately.
        
        **Required Framework**:
        1.  **Diagnosis**: Why are these specific districts crashing? (e.g. Is it a border district? An education hub? A metro migration corridor?) - *Infer based on generic knowledge of Indian geography if possible, or strictly from the high load numbers.*
        2.  **Tactical Intervention (Immediate)**: Suggest specific deployments (e.g., "Deploy 15 Mobile Aadhaar Vans to District X", "Activate 'Camp Mode' in secondary schools").
        3.  **Strategic Fix (Long Term)**: Suggest a policy shift (e.g., "Relax document norms for migrant laborers in these zones" or "Incentivize Private Operators").
        
        **Tone**: Authoritative, Urgent, and Solution-Oriented.
        """
        return self.generate_response(prompt)
