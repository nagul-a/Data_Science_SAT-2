"""
src/feature_engineering.py
--------------------------
Feature Engineering and Preprocessing Pipeline for CH29: Cinema Revenue Insight.

CRITICAL DESIGN PRINCIPLE:
Data Leakage Prevention:
To predict future show ticket sales, we only use features available BEFORE a show commences.
We strictly EXCLUDE:
- `revenue` (derived directly from tickets * price)
- `occupancy_pct` (derived directly from tickets / capacity)
- identifiers (`booking_id`, `show_id`)

Permitted Pre-Show Candidate Features:
- Categorical: `genre`, `language`, `city`, `offer`
- Numerical/Binary: `show_hour`, `screen_capacity`, `ticket_price`, `is_weekend`, `holiday`, `release_week`
"""

import os
import pandas as pd
import numpy as np


FEATURE_COLS_CATEGORICAL = [
    "genre",
    "language",
    "city",
    "offer"
]

FEATURE_COLS_NUMERICAL = [
    "show_hour",
    "screen_capacity",
    "ticket_price",
    "is_weekend",
    "holiday",
    "release_week"
]

TARGET_COL = "tickets"


def extract_features(df):
    """
    Ensure all required features exist and are cleanly typed.
    """
    df = df.copy()
    
    # Fill offer NaN with 'None' if any
    df["offer"] = df["offer"].fillna("None")
    
    # Ensure types
    for col in FEATURE_COLS_NUMERICAL:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        
    for col in FEATURE_COLS_CATEGORICAL:
        df[col] = df[col].astype(str)
        
    df[TARGET_COL] = df[TARGET_COL].astype(int)
    
    return df


def split_chronological(df, split_ratio=0.80):
    """
    Perform a chronological train-test split based on show_date to simulate
    real-world future demand forecasting.
    """
    df = df.sort_values(by=["show_date", "show_time"]).reset_index(drop=True)
    
    split_index = int(len(df) * split_ratio)
    cutoff_date = df.iloc[split_index]["show_date"]
    
    train_df = df.iloc[:split_index].copy()
    test_df = df.iloc[split_index:].copy()
    
    print("\n" + "=" * 70)
    print("CHRONOLOGICAL TRAIN/TEST SPLIT")
    print("=" * 70)
    print(f" Total Records:        {len(df)}")
    print(f" Chronological Cutoff: {cutoff_date}")
    print(f" Training Set (Past):  {len(train_df)} shows ({len(train_df)/len(df)*100:.1f}%) | Dates: {train_df['show_date'].min()} to {train_df['show_date'].max()}")
    print(f" Test Set (Future):    {len(test_df)} shows ({len(test_df)/len(df)*100:.1f}%) | Dates: {test_df['show_date'].min()} to {test_df['show_date'].max()}")
    print("=" * 70)
    
    return train_df, test_df, cutoff_date


def get_feature_matrices(df):
    """
    Extract feature matrix X and target y, rigorously validating against data leakage.
    """
    # Strict data leakage check
    leaked_cols = {"revenue", "occupancy_pct", "tickets"}
    candidate_features = FEATURE_COLS_CATEGORICAL + FEATURE_COLS_NUMERICAL
    
    assert not any(col in candidate_features for col in ["revenue", "occupancy_pct"]), \
        "DATA LEAKAGE DETECTED: Target-derived metrics must NOT be in feature set!"
        
    X = df[candidate_features].copy()
    y = df[TARGET_COL].copy()
    
    return X, y


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, "output", "cleaned_cinema_data.csv")
    
    if os.path.exists(data_path):
        data = pd.read_csv(data_path)
        data = extract_features(data)
        train, test, cutoff = split_chronological(data)
        X_train, y_train = get_feature_matrices(train)
        print(f"Feature matrix X_train shape: {X_train.shape}")
        print(f"Target vector y_train shape: {y_train.shape}")
        print("Feature engineering verification successful.")
    else:
        print("Please run data_cleaning.py first.")
