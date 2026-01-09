
# UIDAI Aadhaar Analytics System

## 📌 Project Overview
This project is a **policy-grade analytics dashboard** designed for the **UIDAI Aadhaar Data Hackathon**. It traverses, processes, and visualizes Aadhaar Enrolment and Update datasets to provide actionable insights for government officials.

## 🎯 Objectives
1.  **Ingestion**: Automate merging of fragmented CSV datasets (State-wise/Time-wise).
2.  **Analytics**: Implement Descriptive, Diagnostic, Predictive, and Prescriptive layers.
3.  **Visualization**: Interactive Streamlit dashboard for policy decision support.

## 📂 Architecture
The project follows a modular architecture:

-   `ingestion/`: Handles dataset traversal and loading.
-   `preprocessing/`: Cleans and normalizes data (Date formats, Pincodes).
-   `analytics/`: Contains logic for all 4 analytics layers.
-   `dashboard/`: Streamlit web application.
-   `utils/`: Constants and helper functions.

## 🚀 How to Run
1.  **Prerequisites**: Python 3.9+, Pandas, Streamlit, Plotly, NumPy.
2.  **Install Dependencies**:
    ```bash
    pip install pandas streamlit plotly numpy
    ```
3.  **Run Dashboard**:
    ```bash
    streamlit run aadhaar_analytics/dashboard/app.py
    ```

## 📊 Analytics Layers
-   **Descriptive**: KPIs for Enrolments and Updates across States/Districts.
-   **Diagnostic**: Analysis of Update-to-Enrolment ratios to identify service pressure points.
-   **Predictive**: Moving Average & Linear Trend forecasting for resource planning (next 3 months).
-   **Prescriptive**: Rule-based recommendations for deploying Mobile Vans or Special Camps.

## 📝 Methodology
-   **Data Consistency**: All filenames are scanned recursively. Columns are normalized to handle naming inconsistencies.
-   **Aggregations**: Data is aggregated by State/District for performance.
-   **Forecasting**: Simple linear regression is used for explainability to non-technical stakeholders.

## 🏛 Impact
This system enables UIDAI to:
-   Identify high-load districts dynamically.
-   Predict surge in mandatory biometric updates for children (5/15 years).
-   Optimize placement of enrolment centers.

---
**Hackathon Submission** | **Team Antigravity**
