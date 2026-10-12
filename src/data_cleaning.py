"""
src/data_cleaning.py
--------------------
Data Cleaning and Preparation Pipeline for CH29: Cinema Revenue Insight.

This module performs:
1. Dataset inspection (dimensions, data types, nulls, duplicates, descriptive statistics).
2. De-duplication of confirmed duplicate booking records.
3. Standardization of inconsistent genre labels.
4. Handling missing showtimes using a documented imputation rule.
5. Detection and removal of invalid negative/zero ticket transactions.
6. Investigation and adjustment of physical capacity mismatches.
7. Foreign key and primary key referential integrity validation.
8. Merging all tables into a unified analytical dataset.
9. Exporting the cleaned merged dataset to output/cleaned_cinema_data.csv.
10. Reporting before-and-after data quality metrics.
"""

import os
import pandas as pd
import numpy as np


def load_raw_datasets(data_dir):
    """Load all raw CSV datasets from data directory."""
    print("=" * 70)
    print("STEP 1: LOADING RAW DATASETS")
    print("=" * 70)
    
    datasets = {
        "bookings": pd.read_csv(os.path.join(data_dir, "bookings.csv")),
        "movies": pd.read_csv(os.path.join(data_dir, "movies.csv")),
        "cinemas": pd.read_csv(os.path.join(data_dir, "cinemas.csv")),
        "pricing": pd.read_csv(os.path.join(data_dir, "pricing.csv")),
        "calendar": pd.read_csv(os.path.join(data_dir, "calendar.csv")),
    }
    
    for name, df in datasets.items():
        print(f" -> {name.upper():<10} Shape: {df.shape[0]} rows, {df.shape[1]} columns")
        
    return datasets


def inspect_datasets(datasets):
    """Inspect data types, missing values, and duplicates across all tables."""
    print("\n" + "=" * 70)
    print("STEP 2: DATA INSPECTION & QUALITY AUDIT")
    print("=" * 70)
    
    for name, df in datasets.items():
        print(f"\n--- [{name.upper()} DATASET] ---")
        print(f"Missing Values:\n{df.isnull().sum()[df.isnull().sum() > 0] if df.isnull().sum().any() else ' None'}")
        dup_count = df.duplicated().sum()
        print(f"Duplicate Rows: {dup_count}")
        if name == "bookings":
            dup_ids = df["booking_id"].duplicated().sum()
            print(f"Duplicate booking_id occurrences: {dup_ids}")
            neg_tickets = (df["tickets"] < 0).sum()
            print(f"Negative ticket counts detected: {neg_tickets}")


def clean_bookings(bookings_df, cinemas_df):
    """
    Clean bookings table:
    - Deduplicate identical records
    - Handle missing showtimes
    - Filter invalid ticket counts
    - Investigate and resolve capacity mismatches
    """
    print("\n" + "=" * 70)
    print("STEP 3: CLEANING BOOKINGS DATA")
    print("=" * 70)
    
    initial_rows = len(bookings_df)
    
    # 1. Deduplication
    # We remove exact duplicate rows first, and keep the first occurrence of duplicate booking_id
    dups_exact = bookings_df.duplicated().sum()
    bookings_df = bookings_df.drop_duplicates(keep="first")
    dups_id = bookings_df.duplicated(subset=["booking_id"]).sum()
    bookings_df = bookings_df.drop_duplicates(subset=["booking_id"], keep="first")
    print(f" [Action] Removed {dups_exact + dups_id} duplicate booking records.")
    
    # 2. Handle missing showtimes
    missing_times = bookings_df["show_time"].isnull().sum()
    # Documented Rule: Impute missing showtime with modal prime evening slot '20:15'
    imputed_time = "20:15"
    bookings_df["show_time"] = bookings_df["show_time"].fillna(imputed_time)
    print(f" [Action] Handled {missing_times} missing showtimes by imputing with standard prime slot '{imputed_time}'.")
    
    # 3. Detect and remove invalid negative or non-integer ticket counts
    invalid_tickets = (bookings_df["tickets"] <= 0) | bookings_df["tickets"].isnull()
    num_invalid = invalid_tickets.sum()
    bookings_df = bookings_df[~invalid_tickets].copy()
    bookings_df["tickets"] = bookings_df["tickets"].astype(int)
    print(f" [Action] Removed {num_invalid} records with invalid non-positive ticket counts (system errors).")
    
    # 4. Detect and investigate capacity mismatches
    cap_map = dict(zip(cinemas_df["cinema_id"], cinemas_df["screen_capacity"]))
    bookings_df["screen_capacity"] = bookings_df["cinema_id"].map(cap_map)
    
    mismatch_mask = bookings_df["tickets"] > bookings_df["screen_capacity"]
    num_mismatches = mismatch_mask.sum()
    print(f" [Investigation] Detected {num_mismatches} capacity mismatches (tickets sold > screen capacity).")
    print("   -> Resolution: Capped tickets at physical screen capacity to reflect true maximum seating.")
    
    # Adjust tickets to capacity
    bookings_df.loc[mismatch_mask, "tickets"] = bookings_df.loc[mismatch_mask, "screen_capacity"]
    
    # Drop temporary screen_capacity column prior to merge
    bookings_df = bookings_df.drop(columns=["screen_capacity"])
    
    print(f" -> Bookings: Started with {initial_rows} rows, cleaned to {len(bookings_df)} rows.")
    return bookings_df


def clean_movies(movies_df):
    """
    Standardize inconsistent genre labels and clean text fields in movies table.
    """
    print("\n" + "=" * 70)
    print("STEP 4: STANDARDIZING MOVIES METADATA")
    print("=" * 70)
    
    print(" Raw unique genres before standardization:", movies_df["genre"].unique().tolist())
    
    # Strip whitespace
    movies_df["genre"] = movies_df["genre"].astype(str).str.strip()
    
    # Standardization dictionary for inconsistent labels
    genre_mapping = {
        "SciFi": "Sci-Fi",
        "action": "Action",
        "comedy": "Comedy",
    }
    
    movies_df["genre"] = movies_df["genre"].replace(genre_mapping)
    print(" Standardized unique genres:", sorted(movies_df["genre"].unique().tolist()))
    return movies_df


def validate_referential_integrity(bookings_df, movies_df, cinemas_df, pricing_df, calendar_df):
    """Validate foreign keys before merging."""
    print("\n" + "=" * 70)
    print("STEP 5: VALIDATING REFERENTIAL INTEGRITY")
    print("=" * 70)
    
    missing_movies = set(bookings_df["movie_id"]) - set(movies_df["movie_id"])
    missing_cinemas = set(bookings_df["cinema_id"]) - set(cinemas_df["cinema_id"])
    missing_pricing = set(bookings_df["pricing_id"]) - set(pricing_df["pricing_id"])
    missing_dates = set(bookings_df["show_date"]) - set(calendar_df["show_date"])
    
    print(f" Unmatched movie IDs:   {len(missing_movies)} {missing_movies}")
    print(f" Unmatched cinema IDs:  {len(missing_cinemas)} {missing_cinemas}")
    print(f" Unmatched pricing IDs: {len(missing_pricing)} {missing_pricing}")
    print(f" Unmatched dates:       {len(missing_dates)} {missing_dates}")
    
    assert len(missing_movies) == 0, "Foreign key violation: Unmatched movie_id found!"
    assert len(missing_cinemas) == 0, "Foreign key violation: Unmatched cinema_id found!"
    assert len(missing_pricing) == 0, "Foreign key violation: Unmatched pricing_id found!"
    assert len(missing_dates) == 0, "Foreign key violation: Unmatched show_date found!"
    print(" [+] All primary and foreign keys are valid and aligned.")


def merge_and_enrich(bookings_df, movies_df, cinemas_df, pricing_df, calendar_df):
    """
    Merge all cleaned datasets and calculate clean derived fields:
    - revenue = tickets * ticket_price
    - occupancy_pct = (tickets / screen_capacity) * 100
    - show_hour = hour of show_time
    - is_weekend = 1 if Saturday/Sunday else 0
    """
    print("\n" + "=" * 70)
    print("STEP 6: MERGING AND ENRICHING DATA")
    print("=" * 70)
    
    # 1. Merge bookings with movies
    merged = bookings_df.merge(movies_df, on="movie_id", how="left")
    
    # 2. Merge with cinemas
    merged = merged.merge(cinemas_df, on="cinema_id", how="left")
    
    # 3. Merge with pricing
    merged = merged.merge(pricing_df, on="pricing_id", how="left")
    
    # 4. Merge with calendar
    merged = merged.merge(calendar_df, on="show_date", how="left")
    
    # Recalculate revenue based on cleaned tickets and verified ticket_price
    merged["revenue"] = (merged["tickets"] * merged["ticket_price"]).round(2)
    
    # Calculate occupancy percentage per show
    merged["occupancy_pct"] = ((merged["tickets"] / merged["screen_capacity"]) * 100).round(2)
    
    # Extract show_hour
    merged["show_hour"] = pd.to_datetime(merged["show_time"], format="%H:%M").dt.hour
    
    # Define weekend indicator
    merged["is_weekend"] = merged["weekday"].isin(["Saturday", "Sunday"]).astype(int)
    
    # Standardize offer column to 'None' where no promotional discount was applied
    merged["offer"] = merged["offer"].fillna("None")
    
    print(f" [+] Successfully merged datasets into unified DataFrame: {merged.shape[0]} rows, {merged.shape[1]} columns")
    return merged


def print_summary_comparison(initial_bookings_count, cleaned_df):
    """Print before-and-after cleaning statistics."""
    print("\n" + "=" * 70)
    print("BEFORE-AND-AFTER CLEANING SUMMARY")
    print("=" * 70)
    print(f" Total Raw Bookings Recorded:          {initial_bookings_count:,}")
    print(f" Cleaned Valid Bookings Retained:       {len(cleaned_df):,}")
    print(f" Total Records Removed / Resolved:     {initial_bookings_count - len(cleaned_df):,}")
    print(f" Total Tickets Sold (Cleaned):          {cleaned_df['tickets'].sum():,}")
    print(f" Total Revenue Generated (Cleaned):     INR {cleaned_df['revenue'].sum():,.2f}")
    overall_occ = (cleaned_df['tickets'].sum() / cleaned_df['screen_capacity'].sum()) * 100
    print(f" Overall Cinema Occupancy:             {overall_occ:.2f}%")
    print("=" * 70)


def main():
    """Main data cleaning execution routine."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    output_dir = os.path.join(base_dir, "output")
    os.makedirs(output_dir, exist_ok=True)
    
    # Load
    datasets = load_raw_datasets(data_dir)
    initial_count = len(datasets["bookings"])
    
    # Inspect
    inspect_datasets(datasets)
    
    # Clean components
    cleaned_bookings = clean_bookings(datasets["bookings"], datasets["cinemas"])
    cleaned_movies = clean_movies(datasets["movies"])
    
    # Validate keys
    validate_referential_integrity(
        cleaned_bookings,
        cleaned_movies,
        datasets["cinemas"],
        datasets["pricing"],
        datasets["calendar"]
    )
    
    # Merge and enrich
    cleaned_df = merge_and_enrich(
        cleaned_bookings,
        cleaned_movies,
        datasets["cinemas"],
        datasets["pricing"],
        datasets["calendar"]
    )
    
    # Save cleaned merged dataset
    output_csv = os.path.join(output_dir, "cleaned_cinema_data.csv")
    cleaned_df.to_csv(output_csv, index=False)
    print(f"\n[+] Cleaned merged dataset saved to: {output_csv}")
    
    # Print before-and-after statistics
    print_summary_comparison(initial_count, cleaned_df)


if __name__ == "__main__":
    main()
