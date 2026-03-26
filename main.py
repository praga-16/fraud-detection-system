from fastapi import FastAPI, Header, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
import pandas as pd
from sklearn.ensemble import IsolationForest

app = FastAPI()

# -----------------------------
# 🔐 SECURITY (API KEY)
# -----------------------------
API_KEY = "mysecurekey123"

def verify_api_key(x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

# -----------------------------
# 🌐 CORS (Frontend Protection)
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],  # Streamlit
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory DB
claims_db = []

# -----------------------------
# 🧹 CLEAN DATA
# -----------------------------
def clean_data(df):
    df['claimant_id'] = df['claimant_id'].fillna("UNKNOWN")
    df['name'] = df['name'].fillna("Unknown")
    df['address'] = df['address'].fillna("Unknown")
    df['third_party'] = df['third_party'].fillna("Unknown")

    df['claimed_value'] = pd.to_numeric(df['claimed_value'], errors='coerce').fillna(0)
    df['coverage'] = pd.to_numeric(df['coverage'], errors='coerce').fillna(1)

    df['date_of_loss'] = pd.to_datetime(df['date_of_loss'], errors='coerce')
    df['policy_start'] = pd.to_datetime(df['policy_start'], errors='coerce')

    # 🔥 Validation
    df = df[df['claimed_value'] >= 0]
    df = df[df['coverage'] > 0]
    df = df[df['date_of_loss'].notna()]
    df = df[df['policy_start'].notna()]

    return df

# -----------------------------
# ⚙️ RULE ENGINE (CONFIGURABLE)
# -----------------------------
def rule_engine(df, rules):
    scores = []
    reasons = []

    for _, row in df.iterrows():
        score = 0
        reason = []

        # Rule 1: Same address
        if len(df[df['address'] == row['address']]) >= rules["address"]:
            score += 20
            reason.append("Multiple claims from same address")

        # Rule 2: Frequent claims
        if len(df[df['claimant_id'] == row['claimant_id']]) > 2:
            score += 20
            reason.append("Frequent claims by claimant")

        # Rule 3: High claim %
        if row['claimed_value'] > (rules["claim_percent"]/100) * row['coverage']:
            score += 25
            reason.append("Claim exceeds threshold")

        # Rule 4: Third-party repeat
        if df['third_party'].value_counts().get(row['third_party'], 0) > 2:
            score += 15
            reason.append("Repeated third-party involvement")

        # Rule 5: Early claim
        diff = (row['date_of_loss'] - row['policy_start']).days
        if diff < 30:
            score += 20
            reason.append("Claim soon after policy start")

        scores.append(score)
        reasons.append(", ".join(reason))

    df['rule_score'] = scores
    df['reasons'] = reasons
    return df

# -----------------------------
# 🤖 ML MODEL
# -----------------------------
def ml_model(df):
    model = IsolationForest(contamination=0.2)

    features = df[['claimed_value', 'coverage']]

    df['anomaly'] = model.fit_predict(features)

    # ML scoring
    df['ml_score'] = df['anomaly'].apply(lambda x: 20 if x == -1 else 0)

    return df

# -----------------------------
# 📥 API: INGEST
# -----------------------------
@app.post("/api/ingest")
def ingest(payload: Dict, x_api_key: str = Header(None)):
    verify_api_key(x_api_key)

    global claims_db

    data = payload["data"]
    rules = payload["rules"]

    df = pd.DataFrame(data)

    df = clean_data(df)
    df = rule_engine(df, rules)
    df = ml_model(df)

    # Final score
    df['fraud_score'] = df['rule_score'] + df['ml_score']

    # -----------------------------
    # 🧑‍💼 WORKFLOW FIELDS
    # -----------------------------
    df["status"] = "Open"
    df["assigned_to"] = "Unassigned"
    df["outcome"] = "Pending"

    claims_db = df.to_dict(orient="records")

    return {"message": "Data processed", "count": len(claims_db)}

# -----------------------------
# 📊 API: GET ALL CLAIMS
# -----------------------------
@app.get("/api/claims")
def get_claims(x_api_key: str = Header(None)):
    verify_api_key(x_api_key)
    return claims_db

# -----------------------------
# 🚨 API: HIGH RISK
# -----------------------------
@app.get("/api/high-risk")
def high_risk(x_api_key: str = Header(None)):
    verify_api_key(x_api_key)

    return sorted(
        [c for c in claims_db if c['fraud_score'] > 60],
        key=lambda x: x['fraud_score'],
        reverse=True
    )

# -----------------------------
# 🔄 API: UPDATE CASE
# -----------------------------
@app.patch("/api/update-case")
def update_case(payload: Dict = Body(...), x_api_key: str = Header(None)):
    verify_api_key(x_api_key)

    global claims_db

    policy_number = payload["policy_number"]

    for claim in claims_db:
        if claim["policy_number"] == policy_number:
            claim["assigned_to"] = payload.get("assigned_to", claim["assigned_to"])
            claim["status"] = payload.get("status", claim["status"])
            claim["outcome"] = payload.get("outcome", claim["outcome"])
            return {"message": "Case updated successfully"}

    raise HTTPException(status_code=404, detail="Claim not found")

# -----------------------------
# 🏠 HOME
# -----------------------------
@app.get("/")
def home():
    return {"message": "Fraud Detection API Running 🚀"}