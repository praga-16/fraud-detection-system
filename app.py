import streamlit as st
import requests
import pandas as pd

API_URL = "https://fraud-detection-system-tspk.onrender.com"
HEADERS = {"x-api-key": "mysecurekey123"}    # 🔐 SECURITY

st.set_page_config(page_title="Fraud Dashboard", layout="wide")

st.title("🚨 Claims Fraud Detection System")

# -----------------------------
# ⚙️ RULE CONFIG
# -----------------------------
st.sidebar.header("⚙️ Configure Rules")

threshold_address = st.sidebar.slider("Address Threshold", 2, 5, 3)
threshold_claim = st.sidebar.slider("Claim % Threshold", 100, 300, 200)
threshold_risk = st.sidebar.slider("High Risk Score", 30, 100, 60)

rules = {
    "address": threshold_address,
    "claim_percent": threshold_claim
}

# -----------------------------
# 📂 FILE UPLOAD (SECURE)
# -----------------------------
st.sidebar.header("📂 Upload CSV")

uploaded_file = st.sidebar.file_uploader("Upload claims", type=["csv"])

if uploaded_file:

    # 🔐 File size check
    if uploaded_file.size > 5 * 1024 * 1024:
        st.error("❌ File too large (Max 5MB)")
        st.stop()

    df_upload = pd.read_csv(uploaded_file)

    # 🔐 Column validation
    required_cols = [
        "claimant_id","name","address","policy_number",
        "claim_type","date_of_loss","claimed_value",
        "coverage","policy_start","third_party"
    ]

    if not all(col in df_upload.columns for col in required_cols):
        st.error("❌ Invalid CSV format")
        st.stop()

    payload = {
        "data": df_upload.to_dict(orient="records"),
        "rules": rules
    }

    try:
        res = requests.post(
            f"{API_URL}/api/ingest",
            json=payload,
            headers=HEADERS
        )

        if res.status_code == 200:
            st.sidebar.success("✅ Uploaded & Processed")
        else:
            st.sidebar.error("❌ Upload failed")

    except:
        st.sidebar.error("❌ Backend not running")

# -----------------------------
# 📊 FETCH DATA (SECURE)
# -----------------------------
try:
    claims = requests.get(f"{API_URL}/api/claims", headers=HEADERS).json()
except:
    claims = []

# -----------------------------
# 📊 DASHBOARD
# -----------------------------
if claims:
    df = pd.DataFrame(claims)

    # KPIs
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Claims", len(df))
    col2.metric("High Risk", len(df[df["fraud_score"] > threshold_risk]))
    col3.metric("Avg Score", round(df["fraud_score"].mean(), 2))

    st.divider()

    # Risk Label
    df["Risk"] = df["fraud_score"].apply(
        lambda x: "High 🔴" if x > 60 else "Medium 🟡" if x > 30 else "Low 🟢"
    )

    # -----------------------------
    # 🧠 PRIORITY EXPLANATION
    # -----------------------------
    def explain(row):
        if row["fraud_score"] > 80:
            return "High priority: multiple fraud signals + anomaly"
        elif row["fraud_score"] > 60:
            return "Medium priority: repeated suspicious patterns"
        return "Low priority"

    df["priority_reason"] = df.apply(explain, axis=1)

    # -----------------------------
    # 📋 TABLE
    # -----------------------------
    st.subheader("📋 Claims Table")
    st.dataframe(df)

    # -----------------------------
    # 🧑‍💼 CASE MANAGEMENT (REAL API)
    # -----------------------------
    st.subheader("🧑‍💼 Case Management")

    selected = st.selectbox("Select Claim", df["policy_number"])

    investigator = st.text_input("Assign Investigator")
    status = st.selectbox("Status", ["Open", "Under Investigation", "Closed"])
    outcome = st.selectbox("Outcome", ["Pending", "Confirmed Fraud", "Cleared"])

    if st.button("Update Case"):
        payload = {
            "policy_number": selected,
            "assigned_to": investigator,
            "status": status,
            "outcome": outcome
        }

        res = requests.patch(
            f"{API_URL}/api/update-case",
            json=payload,
            headers=HEADERS
        )

        if res.status_code == 200:
            st.success("✅ Case Updated in Backend")
        else:
            st.error("❌ Update failed")

    # -----------------------------
    # 🚨 HIGH RISK (SORTED)
    # -----------------------------
    st.subheader("🚨 High Risk Claims")

    high_df = df[df["fraud_score"] > threshold_risk].sort_values(
        by="fraud_score", ascending=False
    )

    st.dataframe(high_df)

    # -----------------------------
    # 📊 CHART
    # -----------------------------
    st.subheader("📊 Fraud Score Chart")
    st.bar_chart(df["fraud_score"])

    # -----------------------------
    # 🧠 RISK BREAKDOWN (WINNER FEATURE)
    # -----------------------------
    st.subheader("🧠 Risk Breakdown")

    st.dataframe(df[["policy_number","rule_score","ml_score","fraud_score"]])

    # -----------------------------
    # ⬇️ DOWNLOAD
    # -----------------------------
    st.subheader("⬇️ Download Reports")

    st.download_button(
        "Download Full Report",
        df.to_csv(index=False),
        "fraud_report.csv",
        "text/csv"
    )

    st.download_button(
        "Download High Risk",
        high_df.to_csv(index=False),
        "high_risk.csv",
        "text/csv"
    )

else:
    st.info("Upload a CSV to begin")
