#!/usr/bin/env python3
"""
Dataset Preparation Script
Downloads Telco Customer Churn dataset from Kaggle, splits it into train/validation/test sets,
and prepares the test set for upload to Google Sheets.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
import kagglehub
import os
import json
from datetime import datetime

def download_dataset():
    """Download the Telco Customer Churn dataset from Kaggle"""
    print("=" * 60)
    print("Downloading Telco Customer Churn Dataset from Kaggle...")
    print("=" * 60)
    
    try:
        path = kagglehub.dataset_download("blastchar/telco-customer-churn")
        print(f"✓ Dataset downloaded to: {path}")
        
        # Find the CSV file
        csv_file = None
        for file in os.listdir(path):
            if file.endswith('.csv'):
                csv_file = os.path.join(path, file)
                break
        
        if not csv_file:
            raise FileNotFoundError("No CSV file found in downloaded dataset")
        
        print(f"✓ Found CSV file: {csv_file}")
        return csv_file
    except Exception as e:
        print(f"✗ Error downloading dataset: {e}")
        raise

def load_and_explore_dataset(csv_file):
    """Load the dataset and display basic information"""
    print("\n" + "=" * 60)
    print("Loading and Exploring Dataset...")
    print("=" * 60)
    
    df = pd.read_csv(csv_file)
    
    print(f"\nDataset Shape: {df.shape}")
    print(f"Total Records: {len(df)}")
    print(f"Total Columns: {len(df.columns)}")
    
    print("\nColumn Names:")
    for i, col in enumerate(df.columns, 1):
        print(f"  {i}. {col}")
    
    print("\nData Types:")
    print(df.dtypes)
    
    print("\nMissing Values:")
    print(df.isnull().sum())
    
    print("\nFirst Few Rows:")
    print(df.head())
    
    return df

def preprocess_dataset(df):
    """Preprocess the dataset for ML"""
    print("\n" + "=" * 60)
    print("Preprocessing Dataset...")
    print("=" * 60)
    
    df_processed = df.copy()
    
    # Handle TotalCharges - convert to numeric, replacing empty strings with 0
    if 'TotalCharges' in df_processed.columns:
        df_processed['TotalCharges'] = pd.to_numeric(
            df_processed['TotalCharges'], 
            errors='coerce'
        ).fillna(0)
        print("✓ Converted TotalCharges to numeric")
    
    # Convert Yes/No to 1/0 for binary columns
    binary_columns = [col for col in df_processed.columns 
                     if df_processed[col].dtype == 'object' 
                     and set(df_processed[col].unique()) <= {'Yes', 'No', 'yes', 'no'}]
    
    for col in binary_columns:
        df_processed[col] = df_processed[col].map({'Yes': 1, 'No': 0, 'yes': 1, 'no': 0})
        print(f"✓ Converted {col} to binary")
    
    # Convert SeniorCitizen if it exists and is numeric
    if 'SeniorCitizen' in df_processed.columns:
        df_processed['SeniorCitizen'] = pd.to_numeric(
            df_processed['SeniorCitizen'], 
            errors='coerce'
        ).fillna(0).astype(int)
    
    print(f"✓ Preprocessing complete")
    return df_processed

def split_dataset(df, train_ratio=0.7, val_ratio=0.15, test_ratio=0.15):
    """Split dataset into train, validation, and test sets"""
    print("\n" + "=" * 60)
    print("Splitting Dataset...")
    print("=" * 60)
    
    # First split: train+val vs test
    train_val_df, test_df = train_test_split(
        df, 
        test_size=test_ratio, 
        random_state=42,
        stratify=df.get('Churn', None) if 'Churn' in df.columns else None
    )
    
    # Second split: train vs val
    train_df, val_df = train_test_split(
        train_val_df,
        test_size=val_ratio / (train_ratio + val_ratio),
        random_state=42,
        stratify=train_val_df.get('Churn', None) if 'Churn' in train_val_df.columns else None
    )
    
    print(f"\nDataset Split:")
    print(f"  Training Set:   {len(train_df):,} records ({len(train_df)/len(df)*100:.1f}%)")
    print(f"  Validation Set: {len(val_df):,} records ({len(val_df)/len(df)*100:.1f}%)")
    print(f"  Test Set:       {len(test_df):,} records ({len(test_df)/len(df)*100:.1f}%)")
    
    if 'Churn' in df.columns:
        print(f"\nChurn Distribution:")
        print(f"  Training:   {train_df['Churn'].value_counts().to_dict()}")
        print(f"  Validation: {val_df['Churn'].value_counts().to_dict()}")
        print(f"  Test:       {test_df['Churn'].value_counts().to_dict()}")
    
    return train_df, val_df, test_df

def save_datasets(train_df, val_df, test_df, output_dir='.'):
    """Save the split datasets to CSV files"""
    print("\n" + "=" * 60)
    print("Saving Datasets...")
    print("=" * 60)
    
    train_path = os.path.join(output_dir, 'train_data.csv')
    val_path = os.path.join(output_dir, 'validation_data.csv')
    test_path = os.path.join(output_dir, 'test_data.csv')
    
    train_df.to_csv(train_path, index=False)
    print(f"✓ Training data saved to: {train_path}")
    
    val_df.to_csv(val_path, index=False)
    print(f"✓ Validation data saved to: {val_path}")
    
    test_df.to_csv(test_path, index=False)
    print(f"✓ Test data saved to: {test_path}")
    
    return train_path, val_path, test_path

def prepare_google_sheets_format(test_df):
    """Prepare test data in Google Sheets format"""
    print("\n" + "=" * 60)
    print("Preparing Data for Google Sheets...")
    print("=" * 60)
    
    # Create a copy for Google Sheets
    sheets_df = test_df.copy()
    
    # Rename columns to match expected format
    column_mapping = {
        'customerID': 'customerID',
        'gender': 'gender',
        'SeniorCitizen': 'SeniorCitizen',
        'Partner': 'Partner',
        'Dependents': 'Dependents',
        'tenure': 'tenure',
        'PhoneService': 'PhoneService',
        'MultipleLines': 'MultipleLines',
        'InternetService': 'InternetService',
        'OnlineSecurity': 'OnlineSecurity',
        'OnlineBackup': 'OnlineBackup',
        'DeviceProtection': 'DeviceProtection',
        'TechSupport': 'TechSupport',
        'StreamingTV': 'StreamingTV',
        'StreamingMovies': 'StreamingMovies',
        'Contract': 'Contract',
        'PaperlessBilling': 'PaperlessBilling',
        'PaymentMethod': 'PaymentMethod',
        'MonthlyCharges': 'MonthlyCharges',
        'TotalCharges': 'TotalCharges',
    }
    
    # Keep only the columns we need
    available_cols = [col for col in column_mapping.keys() if col in sheets_df.columns]
    sheets_df = sheets_df[available_cols]
    
    # Convert binary columns back to Yes/No for readability
    for col in sheets_df.columns:
        if sheets_df[col].dtype in [int, float]:
            if set(sheets_df[col].unique()) <= {0, 1, 0.0, 1.0}:
                sheets_df[col] = sheets_df[col].map({1: 'Yes', 0: 'No'})
    
    print(f"✓ Prepared {len(sheets_df)} records for Google Sheets")
    print(f"✓ Columns: {list(sheets_df.columns)}")
    
    return sheets_df

def create_upload_instructions(test_df_sheets):
    """Create instructions for uploading to Google Sheets"""
    print("\n" + "=" * 60)
    print("Google Sheets Upload Instructions")
    print("=" * 60)
    
    instructions = f"""
GOOGLE SHEETS UPLOAD INSTRUCTIONS
==================================

1. Open your Google Sheet:
   https://docs.google.com/spreadsheets/d/11tlFA84AZnfGJf1UeWBe5jjbF4oGIID4VuqK14qXejs/edit

2. Clear existing data (if any):
   - Select all cells (Ctrl+A)
   - Delete content

3. Add headers:
   - In row 1, add these column names:
     {', '.join(test_df_sheets.columns)}

4. Import test data:
   Option A (Recommended - Copy/Paste):
   - Open test_data_for_sheets.csv in a text editor
   - Copy all content
   - Paste into Google Sheet starting at cell A1
   
   Option B (Import CSV):
   - File > Import > Upload
   - Select test_data_for_sheets.csv
   - Replace existing sheet

5. Verify:
   - Check that all {len(test_df_sheets)} rows are imported
   - Verify all columns are present
   - Check data looks correct

6. Get your Sheet ID:
   - From URL: https://docs.google.com/spreadsheets/d/[SHEET_ID]/edit
   - Sheet ID: 11tlFA84AZnfGJf1UeWBe5jjbF4oGIID4VuqK14qXejs

Dataset Statistics:
- Total test records: {len(test_df_sheets)}
- Total columns: {len(test_df_sheets.columns)}
- Date prepared: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    print(instructions)
    return instructions

def main():
    """Main execution flow"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  Telco Customer Churn Dataset Preparation".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "=" * 58 + "╝")
    
    try:
        # Step 1: Download dataset
        csv_file = download_dataset()
        
        # Step 2: Load and explore
        df = load_and_explore_dataset(csv_file)
        
        # Step 3: Preprocess
        df_processed = preprocess_dataset(df)
        
        # Step 4: Split into train/val/test
        train_df, val_df, test_df = split_dataset(df_processed)
        
        # Step 5: Save datasets
        train_path, val_path, test_path = save_datasets(train_df, val_df, test_df)
        
        # Step 6: Prepare for Google Sheets
        test_df_sheets = prepare_google_sheets_format(test_df)
        sheets_path = 'test_data_for_sheets.csv'
        test_df_sheets.to_csv(sheets_path, index=False)
        print(f"✓ Google Sheets format saved to: {sheets_path}")
        
        # Step 7: Create upload instructions
        instructions = create_upload_instructions(test_df_sheets)
        
        # Save instructions to file
        with open('SHEETS_UPLOAD_INSTRUCTIONS.txt', 'w') as f:
            f.write(instructions)
        print(f"✓ Upload instructions saved to: SHEETS_UPLOAD_INSTRUCTIONS.txt")
        
        # Step 8: Summary
        print("\n" + "=" * 60)
        print("Dataset Preparation Complete!")
        print("=" * 60)
        print(f"\nGenerated Files:")
        print(f"  1. train_data.csv - Training set ({len(train_df)} records)")
        print(f"  2. validation_data.csv - Validation set ({len(val_df)} records)")
        print(f"  3. test_data.csv - Test set ({len(test_df)} records)")
        print(f"  4. test_data_for_sheets.csv - Ready for Google Sheets")
        print(f"  5. SHEETS_UPLOAD_INSTRUCTIONS.txt - Upload guide")
        
        print(f"\nNext Steps:")
        print(f"  1. Upload test_data_for_sheets.csv to your Google Sheet")
        print(f"  2. Use train_data.csv to train the XGBoost model")
        print(f"  3. Use validation_data.csv to validate the model")
        print(f"  4. Use test_data.csv for final testing")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

