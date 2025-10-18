
import gspread
import pandas as pd
import requests
import json
import os

# Placeholder for service account file path
SERVICE_ACCOUNT_FILE = "service_account.json"

# Placeholder for FastAPI model service URL
MODEL_SERVICE_URL = "https://8000-i0bfst9t6on99c9vfewou-b0de354a.manus.computer/predict_churn/"

# Placeholder for Google Sheet ID
GOOGLE_SHEET_ID = ""

def get_latest_customer_data(sheet_id, num_records=50):
    try:
        gc = gspread.service_account(filename=SERVICE_ACCOUNT_FILE)
        spreadsheet = gc.open_by_id(sheet_id)
        worksheet = spreadsheet.sheet1  # Assuming data is in the first sheet
        
        # Get all records and then select the latest num_records
        records = worksheet.get_all_records()
        latest_data = records[-num_records:]
        return latest_data
    except Exception as e:
        print(f"Error reading Google Sheet: {e}")
        return None

def predict_churn_with_model(customer_data):
    try:
        headers = {"Content-Type": "application/json"}
        response = requests.post(MODEL_SERVICE_URL, headers=headers, data=json.dumps(customer_data))
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()["churn_probabilities"]
    except requests.exceptions.RequestException as e:
        print(f"Error calling model service: {e}")
        return None

def summarize_churn_data(churn_probabilities):
    if not churn_probabilities:
        return "No churn data available for summarization."

    total_customers = len(churn_probabilities)
    churn_count = sum(1 for prob in churn_probabilities if prob >= 0.5) # Assuming 0.5 as churn threshold
    churn_rate = (churn_count / total_customers) * 100

    summary = f"Out of the latest {total_customers} customer records, {churn_count} customers are predicted to churn, resulting in a churn rate of {churn_rate:.2f}%."
    return summary

# Example usage (will be integrated with Gemini later)
if __name__ == "__main__":
    # This part will be triggered by the Gemini agent
    print("Fetching latest customer data...")
    customer_data = get_latest_customer_data(GOOGLE_SHEET_ID, num_records=50)

    if customer_data:
        print("Sending data to churn prediction model...")
        churn_probs = predict_churn_with_model(customer_data)
        
        if churn_probs is not None:
            summary = summarize_churn_data(churn_probs)
            print("Churn Prediction Summary:")
            print(summary)
        else:
            print("Failed to get churn predictions.")
    else:
        print("Failed to fetch customer data.")

