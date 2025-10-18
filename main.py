
from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import pandas as pd

app = FastAPI()

# Load the trained model, scaler, and feature names
model = joblib.load("xgboost_churn_model.pkl")
scaler = joblib.load("scaler.pkl")
model_features = joblib.load("model_features.pkl")

class CustomerData(BaseModel):
    gender: str
    SeniorCitizen: int
    Partner: str
    Dependents: str
    tenure: int
    PhoneService: str
    MultipleLines: str
    InternetService: str
    OnlineSecurity: str
    OnlineBackup: str
    DeviceProtection: str
    TechSupport: str
    StreamingTV: str
    StreamingMovies: str
    Contract: str
    PaperlessBilling: str
    PaymentMethod: str
    MonthlyCharges: float
    TotalCharges: float

@app.post("/predict_churn/")
async def predict_churn(data: list[CustomerData]):
    df = pd.DataFrame([d.model_dump() for d in data])

    # Preprocessing steps (must match training preprocessing)
    for col in ["OnlineSecurity", "OnlineBackup", "DeviceProtection", "TechSupport", "StreamingTV", "StreamingMovies", "MultipleLines"]:
        df[col] = df[col].replace({"No internet service": "No", "No phone service": "No"})
    
    df["Partner"] = df["Partner"].replace({"Yes": 1, "No": 0})
    df["Dependents"] = df["Dependents"].replace({"Yes": 1, "No": 0})
    df["PhoneService"] = df["PhoneService"].replace({"Yes": 1, "No": 0})

    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
    df["TotalCharges"] = df["TotalCharges"].fillna(df["TotalCharges"].mean())

    # One-hot encode categorical features
    categorical_cols = df.select_dtypes(include="object").columns
    df = pd.get_dummies(df, columns=categorical_cols, drop_first=True)

    # Ensure all columns from training are present, fill missing with 0
    for col in model_features:
        if col not in df.columns:
            df[col] = 0
    
    # Align columns to the order used during training
    df = df[model_features]

    # Scale numerical features
    df_scaled = scaler.transform(df)

    # Make predictions
    predictions = model.predict_proba(df_scaled)[:, 1] # Probability of churn

    return {"churn_probabilities": predictions.tolist()}

