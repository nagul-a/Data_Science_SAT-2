"""
src/predict_show.py
-------------------
Command-Line Interface (CLI) for Single Show Demand Forecasting.

Allows cinema managers at SilverScreen Cinemas to forecast expected ticket sales,
occupancy percentage, and revenue for an upcoming show using the trained RandomForest model.
"""

import os
import argparse
import pandas as pd
from train_model import train_and_evaluate, predict_single_show


def main():
    parser = argparse.ArgumentParser(description="Forecast ticket demand for an upcoming cinema show.")
    parser.add_argument("--genre", type=str, default="Action", help="Movie genre (e.g. Action, Sci-Fi, Comedy, Drama)")
    parser.add_argument("--language", type=str, default="Hindi", help="Movie language (e.g. Hindi, English, French)")
    parser.add_argument("--city", type=str, default="Mumbai", help="Cinema city (Mumbai, Delhi, Bengaluru, Chennai, Hyderabad)")
    parser.add_argument("--offer", type=str, default="None", help="Promotional offer applied (None, Family Pack 15%, Student Discount 20%, Early Bird 28%)")
    parser.add_argument("--hour", type=int, default=20, help="Show hour in 24-hr format (e.g. 10, 13, 17, 20, 22)")
    parser.add_argument("--capacity", type=int, default=250, help="Screen seating capacity (e.g. 150, 180, 200, 220, 250)")
    parser.add_argument("--price", type=float, default=380.0, help="Base ticket price in INR")
    parser.add_argument("--weekend", type=int, default=1, choices=[0, 1], help="1 if Saturday/Sunday else 0")
    parser.add_argument("--holiday", type=int, default=0, choices=[0, 1], help="1 if national holiday else 0")
    parser.add_argument("--week", type=int, default=1, choices=[1, 2, 3, 4], help="Release week of theatrical run (1-4)")
    
    args = parser.parse_args()
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(base_dir, "output")
    cleaned_data_path = os.path.join(output_dir, "cleaned_cinema_data.csv")
    
    if not os.path.exists(cleaned_data_path):
        print("[!] Cleaned dataset not found. Running data cleaning first...")
        import data_cleaning
        data_cleaning.main()
        
    df = pd.read_csv(cleaned_data_path)
    pipeline, _, _ = train_and_evaluate(df, output_dir)
    
    show_query = {
        "genre": args.genre,
        "language": args.language,
        "city": args.city,
        "offer": args.offer,
        "show_hour": args.hour,
        "screen_capacity": args.capacity,
        "ticket_price": args.price,
        "is_weekend": args.weekend,
        "holiday": args.holiday,
        "release_week": args.week
    }
    
    print("\n" + "=" * 60)
    print("SILVERSCREEN CINEMAS: PREDICTIVE SCHEDULING FORECAST")
    print("=" * 60)
    result = predict_single_show(pipeline, show_query)
    return result


if __name__ == "__main__":
    main()
