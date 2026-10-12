"""
src/train_model.py
------------------
Machine Learning Demand Forecasting Pipeline for CH29: Cinema Revenue Insight.

Predicts `tickets` sold per show using pre-show operational features:
- Algorithm: RandomForestRegressor within Scikit-Learn Pipeline & ColumnTransformer.
- Preprocessing: OneHotEncoder (categories) + StandardScaler / Passthrough (numerical).
- Evaluation: Chronological train/test split.
- Benchmark: DummyRegressor (mean prediction baseline).
- Evaluation Metrics: Mean Absolute Error (MAE), Root Mean Squared Error (RMSE), R² Score.
- Deliverables:
  * output/model_metrics.csv (comparative model metrics)
  * output/test_predictions_vs_actuals.csv (test predictions vs actual counts)
  * Feature importance ranking
  * Interactive CLI prediction function for single show demonstration
"""

import os
import joblib
import pandas as pd
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.dummy import DummyRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from feature_engineering import (
    extract_features,
    split_chronological,
    get_feature_matrices,
    FEATURE_COLS_CATEGORICAL,
    FEATURE_COLS_NUMERICAL
)


RANDOM_SEED = 42


def build_pipeline():
    """
    Construct Scikit-learn Pipeline with ColumnTransformer:
    - OneHotEncoder for categorical features (handle_unknown='ignore')
    - StandardScaler for numerical features
    - RandomForestRegressor as estimator
    """
    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), FEATURE_COLS_CATEGORICAL),
            ("num", StandardScaler(), FEATURE_COLS_NUMERICAL),
        ],
        remainder="drop"
    )
    
    rf_pipeline = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("regressor", RandomForestRegressor(
            n_estimators=150,
            max_depth=12,
            min_samples_split=4,
            min_samples_leaf=2,
            random_state=RANDOM_SEED,
            n_jobs=-1
        ))
    ])
    
    baseline_pipeline = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("regressor", DummyRegressor(strategy="mean"))
    ])
    
    return rf_pipeline, baseline_pipeline


def compute_metrics(y_true, y_pred):
    """Calculate MAE, RMSE, and R² scores."""
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)
    return mae, rmse, r2


def train_and_evaluate(cleaned_df, output_dir):
    """
    Train Random Forest and Baseline model on chronological split,
    evaluate on test set, and save metrics and prediction comparisons.
    """
    print("\n" + "=" * 70)
    print("STEP 1: PREPARING FEATURES & CHRONOLOGICAL DATA SPLIT")
    print("=" * 70)
    
    df = extract_features(cleaned_df)
    train_df, test_df, cutoff_date = split_chronological(df, split_ratio=0.80)
    
    X_train, y_train = get_feature_matrices(train_df)
    X_test, y_test = get_feature_matrices(test_df)
    
    rf_pipeline, baseline_pipeline = build_pipeline()
    
    print("\n" + "=" * 70)
    print("STEP 2: TRAINING MODELS (RANDOM FOREST & DUMMY BASELINE)")
    print("=" * 70)
    print(" Training Baseline DummyRegressor (Historical Mean)...")
    baseline_pipeline.fit(X_train, y_train)
    y_test_pred_base = baseline_pipeline.predict(X_test)
    
    print(" Training RandomForestRegressor with Preprocessing Pipeline...")
    rf_pipeline.fit(X_train, y_train)
    y_test_pred_rf = rf_pipeline.predict(X_test)
    
    print("\n" + "=" * 70)
    print("STEP 3: COMPUTING EVALUATION METRICS ON UNSEEN FUTURE SHOWS")
    print("=" * 70)
    
    base_mae, base_rmse, base_r2 = compute_metrics(y_test, y_test_pred_base)
    rf_mae, rf_rmse, rf_r2 = compute_metrics(y_test, y_test_pred_rf)
    
    metrics_data = [
        {
            "Model": "Baseline (Mean Predictor)",
            "MAE (Tickets)": round(base_mae, 2),
            "RMSE (Tickets)": round(base_rmse, 2),
            "R2_Score": round(base_r2, 4),
            "Interpretation": "Naive baseline predicting mean ticket volume across all shows."
        },
        {
            "Model": "Random Forest Regressor",
            "MAE (Tickets)": round(rf_mae, 2),
            "RMSE (Tickets)": round(rf_rmse, 2),
            "R2_Score": round(rf_r2, 4),
            "Interpretation": "Multi-feature ensemble capturing non-linear interactions across timing, genre, and pricing."
        }
    ]
    
    metrics_df = pd.DataFrame(metrics_data)
    
    # Save metrics CSV
    metrics_csv_path = os.path.join(output_dir, "model_metrics.csv")
    metrics_df.to_csv(metrics_csv_path, index=False)
    print(f"[+] Saved evaluation metrics to: {metrics_csv_path}\n")
    print(metrics_df[["Model", "MAE (Tickets)", "RMSE (Tickets)", "R2_Score"]])
    
    # Metric explanation
    print("\n" + "-" * 70)
    print("MODEL EVALUATION SUMMARY:")
    print("-" * 70)
    print(f" * MAE (Mean Absolute Error): {rf_mae:.2f} tickets.")
    print(f"   On average, the Random Forest prediction is off by only ~{rf_mae:.1f} tickets per show.")
    print(f"   (Compared to the baseline error of {base_mae:.2f} tickets, an improvement of {((base_mae - rf_mae)/base_mae)*100:.1f}%).")
    print(f" * RMSE (Root Mean Squared Error): {rf_rmse:.2f} tickets.")
    print(f"   Penalizes large errors heavily; lower values confirm low variance in error magnitude.")
    print(f" * R² Score (Coefficient of Determination): {rf_r2:.4f} ({rf_r2*100:.1f}%).")
    print(f"   The model explains approximately {rf_r2*100:.1f}% of the variance in future show ticket sales,")
    print(f"   confirming strong predictive utility for cinema schedule planning.")
    print("-" * 70)
    
    # Save test predictions vs actuals comparison CSV
    comparison_df = test_df.copy()
    comparison_df["predicted_tickets"] = np.round(y_test_pred_rf).astype(int)
    comparison_df["prediction_error"] = comparison_df["predicted_tickets"] - comparison_df["tickets"]
    comparison_df["abs_error"] = np.abs(comparison_df["prediction_error"])
    comparison_df["predicted_revenue"] = (comparison_df["predicted_tickets"] * comparison_df["ticket_price"]).round(2)
    
    cols_to_save = [
        "booking_id", "show_date", "show_time", "cinema", "city", "movie", "genre",
        "screen_capacity", "ticket_price", "offer", "tickets", "predicted_tickets",
        "prediction_error", "abs_error", "revenue", "predicted_revenue"
    ]
    comparison_path = os.path.join(output_dir, "test_predictions_vs_actuals.csv")
    comparison_df[cols_to_save].to_csv(comparison_path, index=False)
    print(f"[+] Saved test predictions vs actuals comparison to: {comparison_path}")
    
    # Feature Importances Extraction
    feature_names = []
    # Get onehot category names
    cat_encoder = rf_pipeline.named_steps["preprocessor"].named_transformers_["cat"]
    cat_cols_encoded = cat_encoder.get_feature_names_out(FEATURE_COLS_CATEGORICAL)
    feature_names.extend(cat_cols_encoded)
    feature_names.extend(FEATURE_COLS_NUMERICAL)
    
    importances = rf_pipeline.named_steps["regressor"].feature_importances_
    feat_imp_df = pd.DataFrame({
        "Feature": feature_names,
        "Importance": importances
    }).sort_values(by="Importance", ascending=False).reset_index(drop=True)
    
    print("\n" + "=" * 70)
    print("TOP 10 MOST INFLUENTIAL FEATURES IN DEMAND PREDICTION:")
    print("=" * 70)
    for i, row in feat_imp_df.head(10).iterrows():
        print(f" {i+1:2d}. {row['Feature']:<30} Importance: {row['Importance']*100:5.2f}%")
    print("=" * 70)
    
    feat_imp_path = os.path.join(output_dir, "feature_importances.csv")
    feat_imp_df.to_csv(feat_imp_path, index=False)
    
    return rf_pipeline, metrics_df, comparison_df


def predict_single_show(pipeline, show_dict):
    """
    Convenience function for CLI-based single show demand prediction.
    """
    input_df = pd.DataFrame([show_dict])
    pred = pipeline.predict(input_df)[0]
    expected_tickets = int(round(pred))
    expected_revenue = round(expected_tickets * show_dict["ticket_price"], 2)
    expected_occupancy = round((expected_tickets / show_dict["screen_capacity"]) * 100, 2)
    
    print("\n--- SHOW DEMAND FORECAST ---")
    print(f" Movie:           {show_dict.get('genre')} | Language: {show_dict.get('language')}")
    print(f" Location:        {show_dict.get('city')} | Hall Capacity: {show_dict.get('screen_capacity')} seats")
    print(f" Timing:          Show Hour: {show_dict.get('show_hour')}:00 | Weekend: {bool(show_dict.get('is_weekend'))} | Holiday: {bool(show_dict.get('holiday'))}")
    print(f" Pricing & Offer: INR {show_dict.get('ticket_price')} ({show_dict.get('offer')}) | Release Week: Week {show_dict.get('release_week')}")
    print(f" -> Predicted Tickets:   {expected_tickets} seats")
    print(f" -> Projected Occupancy: {expected_occupancy}%")
    print(f" -> Projected Revenue:   INR {expected_revenue:,.2f}")
    print("----------------------------\n")
    
    return {
        "predicted_tickets": expected_tickets,
        "predicted_occupancy": expected_occupancy,
        "predicted_revenue": expected_revenue
    }


def main():
    """Main model training and demonstration."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(base_dir, "output")
    cleaned_data_path = os.path.join(output_dir, "cleaned_cinema_data.csv")
    
    if not os.path.exists(cleaned_data_path):
        raise FileNotFoundError(f"Cleaned dataset not found at {cleaned_data_path}. Run data_cleaning.py first!")
        
    df = pd.read_csv(cleaned_data_path)
    pipeline, metrics_df, _ = train_and_evaluate(df, output_dir)
    
    # Run sample prediction
    print("\nSample Upcoming Show Prediction:")
    sample_show = {
        "genre": "Action",
        "language": "Hindi",
        "city": "Mumbai",
        "offer": "None",
        "show_hour": 20,
        "screen_capacity": 250,
        "ticket_price": 380.0,
        "is_weekend": 1,
        "holiday": 1,
        "release_week": 1
    }
    predict_single_show(pipeline, sample_show)
    return pipeline, metrics_df


if __name__ == "__main__":
    main()
