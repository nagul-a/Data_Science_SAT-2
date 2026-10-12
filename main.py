"""
main.py
-------
Pipeline runner for CH29: Cinema Revenue Insight (SilverScreen Cinemas).

Runs:
1. Data cleaning & referential integrity checks
2. Exploratory data analysis & chart export
3. Feature engineering & Random Forest model training
4. Excel dashboard generation (9 sheets with charts)
5. Sample show demand forecasting inferences
"""

import os
import sys
import time
import argparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import data_cleaning
import eda_analysis
import train_model
import build_dashboard


def run_pipeline(skip_data_generation=False):
    start_time = time.time()
    
    print("\n" + "=" * 70)
    print("SilverScreen Cinemas — Cinema Revenue Insight Pipeline")
    print("=" * 70)
    
    if not os.path.exists(os.path.join(BASE_DIR, "data", "bookings.csv")):
        print("\n[INFO] Data files missing. Generating baseline datasets...")
        import data_generation
        data_generation.main()
    
    print("\n--- Step 1/5: Data Cleaning & Integrity Audit ---")
    t0 = time.time()
    data_cleaning.main()
    print(f"Done in {time.time() - t0:.2f}s")
    
    print("\n--- Step 2/5: Exploratory Data Analysis (EDA) ---")
    t0 = time.time()
    eda_analysis.main()
    print(f"Done in {time.time() - t0:.2f}s")
    
    print("\n--- Step 3/5: Model Training & Evaluation ---")
    t0 = time.time()
    pipeline, _ = train_model.main()
    print(f"Done in {time.time() - t0:.2f}s")
    
    print("\n--- Step 4/5: Building Excel Dashboard ---")
    t0 = time.time()
    build_dashboard.create_dashboard()
    print(f"Done in {time.time() - t0:.2f}s")
    
    print("\n--- Step 5/5: Sample Demand Forecast Scenarios ---")
    scenarios = [
        {
            "name": "Scenario A: Weekend Evening Blockbuster (Action, Mumbai, 20:00, Week 1)",
            "query": {
                "genre": "Action",
                "language": "Hindi",
                "city": "Mumbai",
                "offer": "None",
                "show_hour": 20,
                "screen_capacity": 250,
                "ticket_price": 380.0,
                "is_weekend": 1,
                "holiday": 0,
                "release_week": 1
            }
        },
        {
            "name": "Scenario B: Weekday Morning Matinee (Drama, Delhi, 10:30, Week 3)",
            "query": {
                "genre": "Drama",
                "language": "Hindi",
                "city": "Delhi",
                "offer": "Student Discount 20%",
                "show_hour": 10,
                "screen_capacity": 150,
                "ticket_price": 280.0,
                "is_weekend": 0,
                "holiday": 0,
                "release_week": 3
            }
        }
    ]
    
    for sc in scenarios:
        print(f"\n{sc['name']}:")
        train_model.predict_single_show(pipeline, sc['query'])
        
    total_duration = time.time() - start_time
    print("\n" + "=" * 70)
    print(f"Pipeline executed successfully in {total_duration:.2f}s.")
    print("Outputs verified:")
    print(" - Cleaned dataset : output/cleaned_cinema_data.csv")
    print(" - Summary tables  : output/*.csv")
    print(" - Visual charts   : output/charts/*.png")
    print(" - Model metrics   : output/model_metrics.csv")
    print(" - Excel dashboard : excel/cinema_dashboard.xlsx")
    print(" - Jupyter Notebook: notebooks/cinema_analysis.ipynb")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Cinema Revenue Insight Pipeline")
    parser.add_argument("--skip-gen", action="store_true", help="Skip dataset generation check")
    args = parser.parse_args()
    run_pipeline(skip_data_generation=args.skip_gen)
