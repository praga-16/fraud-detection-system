# 🚨 Claims Fraud Detection System

## 📌 Overview
This project is a production-ready fraud detection platform built to identify suspicious insurance claims using rule-based logic and machine learning.

---

## 🚀 Features

- 📥 CSV-based claim ingestion
- ⚙️ Configurable fraud detection rules
- 🤖 ML anomaly detection (Isolation Forest)
- 📊 Fraud scoring (0–100)
- 🧠 Explainable risk insights
- 🚨 High-risk prioritization
- 🧑‍💼 Investigator workflow (assign, status, outcome)
- 🔗 Fraud network graph visualization
- 🔐 Secure API (API key authentication)
- ⬇️ Downloadable reports

---

## 🏗️ Architecture

- Backend: FastAPI (deployed on Render)
- Frontend: Streamlit (deployed on Streamlit Cloud)
- ML: Scikit-learn (Isolation Forest)
- Data Processing: Pandas

---

## 🌐 Live Demo

Frontend:  
https://fraud-detection-systemgit.streamlit.app/
<img width="1919" height="1010" alt="image" src="https://github.com/user-attachments/assets/849a1bfc-1bf6-43da-b22e-8fbf7bc0855f" />

Backend API:  
https://fraud-detection-system-tspk.onrender.com

---

## ⚙️ How to Run Locally

### Backend
```bash
uvicorn main:app --reload
