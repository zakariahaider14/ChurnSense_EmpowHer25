#!/usr/bin/env python3
"""
Dataset Preparation Script v2
Splits the Telco Customer Churn dataset into train/validation/test sets,
and prepares the test set for upload to Google Sheets.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
import os
from datetime import datetime

def load_and_explore_dataset(csv_file):
    """Load the dataset and display basic information"""
    print("\n" + "=" * 60)
    print("Loading and Exploring Dataset...")
    print("=" * 60)
    
    df = pd.read_csv(csv_file)
    
    print(f"\n✓ Dataset loaded successfully!")
    print(f"\nDataset Shape: {df.shape}")
    print(f"Total Records: {len(df):,}")
    print(f"Total Columns: {len(df.columns)}")
    
    print("\nColumn Names:")
    for i, col in enumerate(df.columns, 1):
        print(f"  {i:2d}. {col}")
    
    print("\nData Types:")
    print(df.dtypes)
    
    print("\nMissing Values:")
    missing = df.isnull().sum()
    if missing.sum() == 0:
        print("  No missing values found!")
    else:
        print(missing[missing > 0])
    
    print("\nFirst 3 Rows:")
    print(df.head(3))
    
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
    
    # Convert SeniorCitizen if it exists and is numeric
    if 'SeniorCitizen' in df_processed.columns:
        df_processed['SeniorCitizen'] = pd.to_numeric(
            df_processed['SeniorCitizen'], 
            errors='coerce'
        ).fillna(0).astype(int)
    
    # Convert Yes/No to 1/0 for binary columns (except Churn which we keep as is)
    binary_columns = [col for col in df_processed.columns 
                     if col != 'Churn' 
                     and df_processed[col].dtype == 'object' 
                     and set(df_processed[col].unique()) <= {'Yes', 'No', 'yes', 'no'}]
    
    for col in binary_columns:
        df_processed[col] = df_processed[col].map({'Yes': 1, 'No': 0, 'yes': 1, 'no': 0})
        print(f"✓ Converted {col} to binary")
    
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
    
    print(f"\n✓ Dataset Split Successfully:")
    print(f"  Training Set:   {len(train_df):,} records ({len(train_df)/len(df)*100:.1f}%)")
    print(f"  Validation Set: {len(val_df):,} records ({len(val_df)/len(df)*100:.1f}%)")
    print(f"  Test Set:       {len(test_df):,} records ({len(test_df)/len(df)*100:.1f}%)")
    print(f"  Total:          {len(df):,} records")
    
    if 'Churn' in df.columns:
        print(f"\n✓ Churn Distribution:")
        print(f"  Training:   {dict(train_df['Churn'].value_counts())}")
        print(f"  Validation: {dict(val_df['Churn'].value_counts())}")
        print(f"  Test:       {dict(test_df['Churn'].value_counts())}")
    
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
    
    # Convert binary columns back to Yes/No for readability
    for col in sheets_df.columns:
        if col == 'Churn':
            continue
        if sheets_df[col].dtype in [int, float]:
            if set(sheets_df[col].unique()) <= {0, 1, 0.0, 1.0}:
                sheets_df[col] = sheets_df[col].map({1: 'Yes', 0: 'No'})
    
    print(f"✓ Prepared {len(sheets_df):,} records for Google Sheets")
    print(f"✓ Columns: {len(sheets_df.columns)}")
    print(f"  {', '.join(sheets_df.columns)}")
    
    return sheets_df

def create_upload_instructions(test_df_sheets, sheet_id):
    """Create instructions for uploading to Google Sheets"""
    print("\n" + "=" * 60)
    print("Google Sheets Upload Instructions")
    print("=" * 60)
    
    instructions = f"""
╔════════════════════════════════════════════════════════════════╗
║         GOOGLE SHEETS UPLOAD INSTRUCTIONS                      ║
╚════════════════════════════════════════════════════════════════╝

STEP 1: Open Your Google Sheet
────────────────────────────────
URL: https://docs.google.com/spreadsheets/d/{sheet_id}/edit

STEP 2: Clear Existing Data (if any)
──────────────────────────────────────
1. Select all cells (Ctrl+A or Cmd+A)
2. Press Delete to clear content

STEP 3: Add Column Headers
──────────────────────────
1. Click on cell A1
2. Add these column names in row 1:
   {', '.join(test_df_sheets.columns)}

STEP 4: Import Test Data
──────────────────────────
Option A (Recommended - Copy/Paste):
1. Open test_data_for_sheets.csv in a text editor
2. Copy all content (Ctrl+A, then Ctrl+C)
3. In Google Sheet, click cell A1
4. Paste (Ctrl+V or Cmd+V)
5. Wait for data to load

Option B (Using Google Sheets Import):
1. In Google Sheet, go to File > Import
2. Select "Upload" tab
3. Choose test_data_for_sheets.csv
4. Select "Replace current sheet"
5. Click Import

STEP 5: Verify Data
─────────────────────
1. Check that all {len(test_df_sheets):,} rows are imported
2. Verify all {len(test_df_sheets.columns)} columns are present
3. Scroll through to verify data looks correct
4. Check for any errors or missing values

STEP 6: Get Your Sheet ID
──────────────────────────
Your Sheet ID: {sheet_id}

STEP 7: Verify Sheet Sharing
──────────────────────────────
1. Click Share button (top right)
2. Make sure your service account has access:
   Email: churn-sheets-reader@main-aura-237918.iam.gserviceaccount.com
3. If not, add it with Viewer access

════════════════════════════════════════════════════════════════

DATASET STATISTICS:
──────────────────
Total test records: {len(test_df_sheets):,}
Total columns: {len(test_df_sheets.columns)}
Date prepared: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

NEXT STEPS:
──────────
1. Upload test_data_for_sheets.csv to your Google Sheet
2. Use train_data.csv to train the XGBoost model
3. Use validation_data.csv to validate the model
4. Use test_data.csv for final testing

════════════════════════════════════════════════════════════════
"""
    
    print(instructions)
    return instructions

def main():
    """Main execution flow"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  Telco Customer Churn Dataset Preparation v2".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "=" * 58 + "╝")
    
    try:
        # Step 1: Load and explore
        csv_file = '/home/ubuntu/WA_Fn-UseC_-Telco-Customer-Churn.csv'
        df = load_and_explore_dataset(csv_file)
        
        # Step 2: Preprocess
        df_processed = preprocess_dataset(df)
        
        # Step 3: Split into train/val/test
        train_df, val_df, test_df = split_dataset(df_processed)
        
        # Step 4: Save datasets
        train_path, val_path, test_path = save_datasets(train_df, val_df, test_df)
        
        # Step 5: Prepare for Google Sheets
        test_df_sheets = prepare_google_sheets_format(test_df)
        sheets_path = '/home/ubuntu/test_data_for_sheets.csv'
        test_df_sheets.to_csv(sheets_path, index=False)
        print(f"✓ Google Sheets format saved to: {sheets_path}")
        
        # Step 6: Create upload instructions
        sheet_id = "11tlFA84AZnfGJf1UeWBe5jjbF4oGIID4VuqK14qXejs"
        instructions = create_upload_instructions(test_df_sheets, sheet_id)
        
        # Save instructions to file
        instructions_path = '/home/ubuntu/SHEETS_UPLOAD_INSTRUCTIONS.txt'
        with open(instructions_path, 'w') as f:
            f.write(instructions)
        print(f"✓ Upload instructions saved to: {instructions_path}")
        
        # Step 7: Summary
        print("\n" + "=" * 60)
        print("✓ Dataset Preparation Complete!")
        print("=" * 60)
        print(f"\n📁 Generated Files:")
        print(f"  1. train_data.csv - Training set ({len(train_df):,} records)")
        print(f"  2. validation_data.csv - Validation set ({len(val_df):,} records)")
        print(f"  3. test_data.csv - Test set ({len(test_df):,} records)")
        print(f"  4. test_data_for_sheets.csv - Ready for Google Sheets")
        print(f"  5. SHEETS_UPLOAD_INSTRUCTIONS.txt - Upload guide")
        
        print(f"\n📋 Next Steps:")
        print(f"  1. Read SHEETS_UPLOAD_INSTRUCTIONS.txt")
        print(f"  2. Upload test_data_for_sheets.csv to your Google Sheet")
        print(f"  3. Verify the data is correctly imported")
        print(f"  4. Use train_data.csv to train the XGBoost model")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

