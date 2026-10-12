# Cinema Revenue Insight (CH29) — SilverScreen Multiplex Analytics

**Organization:** SilverScreen Cinemas  
**Challenge ID:** CH29  
**Domain:** Multiplex Operations & Theatrical Box Office Analytics  
**Primary Business Question:** *What operational and content factors drive ticket sales, screen occupancy, and revenue across cinema shows?*

---

## 1. Project Overview

SilverScreen Cinemas operates multiple multiplex cinema locations across major metropolitan areas in India (Mumbai, Delhi, Bengaluru, Chennai, Hyderabad). Multiplex operations are constrained by two primary economic factors:
1. **Fixed capacity:** Each auditorium has a hard physical ceiling of available seats per screening (150–250 seats).
2. **Perishable inventory:** An unsold seat generates zero revenue once a screening begins.

This project analyzes historical booking records across 5 multiplex branches, 10 feature films, and 6 seating/pricing tiers over an 8-week theatrical run. The analytical pipeline encompasses:
- End-to-end data auditing, deduplication, imputation, and anomaly resolution.
- Exploratory Data Analysis answering 6 core business questions on timing, genres, pricing offers, and locations.
- Chronologically validated machine learning model predicting ticket demand without data leakage.
- Automated 9-sheet executive Excel dashboard (`excel/cinema_dashboard.xlsx`).
- Actionable operational and scheduling recommendations for theatre managers.

---

## 2. Project Structure

```text
SAT2/
├── data/                               # Relational CSV datasets
│   ├── bookings.csv                    # Show-level booking transactions
│   ├── movies.csv                      # Movie metadata (genre, runtime, language)
│   ├── cinemas.csv                     # Multiplex locations & hall capacities
│   ├── pricing.csv                     # Seating classes & promotional discounts
│   └── calendar.csv                    # Calendar dimensions (day, holiday, release week)
├── notebooks/
│   └── cinema_analysis.ipynb           # Interactive analysis & visualization notebook
├── src/
│   ├── data_cleaning.py                # Data audit, deduplication, and cleaning pipeline
│   ├── eda_analysis.py                 # EDA analysis & chart generation
│   ├── feature_engineering.py          # Feature preprocessing & chronological split
│   ├── train_model.py                  # Random Forest & Baseline regression models
│   ├── predict_show.py                 # CLI demand prediction tool
│   ├── build_dashboard.py              # 9-sheet Excel workbook builder
│   └── data_generation.py              # Data generator utility
├── output/
│   ├── cleaned_cinema_data.csv         # Cleaned, unified analytical dataset (2,185 rows)
│   ├── model_metrics.csv               # MAE, RMSE, and R² scores
│   ├── feature_importances.csv         # Top predictive drivers ranking
│   ├── test_predictions_vs_actuals.csv # Test evaluation predictions
│   ├── genre_performance.csv           # Aggregated genre table
│   ├── showtime_performance.csv        # Aggregated showtime table
│   ├── weekend_performance.csv         # Weekday vs. weekend table
│   ├── cinema_performance.csv          # Branch performance table
│   ├── offer_performance.csv           # Promotional offers table
│   ├── release_week_performance.csv    # Theatrical decay table
│   └── charts/                         # High-res visualization plots (PNG)
│       ├── chart1_revenue_by_genre.png
│       ├── chart2_occupancy_by_showtime.png
│       ├── chart3_weekend_vs_weekday.png
│       ├── chart4_cinema_performance.png
│       ├── chart5_offer_performance.png
│       └── chart6_release_week_demand.png
├── excel/
│   └── cinema_dashboard.xlsx           # 9-sheet formatted workbook with OpenPyXL charts
├── main.py                             # Master pipeline runner
├── requirements.txt                    # Python dependencies
├── .gitignore                          # Version control ignore list
└── README.md                           # Project documentation
```

---

## 3. Dataset Architecture

The project models a normalized relational schema across five tables:

| Dataset | Primary Key | Foreign Keys | Key Attributes |
| :--- | :--- | :--- | :--- |
| `bookings.csv` | `booking_id` | `cinema_id`, `movie_id`, `pricing_id`, `show_date` | `show_time`, `screen`, `tickets`, `revenue` |
| `movies.csv` | `movie_id` | — | `movie`, `genre`, `language`, `runtime`, `certification` |
| `cinemas.csv` | `cinema_id` | — | `cinema`, `city`, `screen_capacity` |
| `pricing.csv` | `pricing_id` | — | `seat_class`, `ticket_price`, `offer` |
| `calendar.csv` | `show_date` | — | `weekday`, `holiday`, `release_week` |

---

## 4. Data Cleaning & Preparation

The raw transactional data contained real-world data quality issues that were audited and cleaned in `src/data_cleaning.py`:

1. **Deduplication:** Identified and dropped 30 duplicate booking records to prevent double-counting.
2. **Missing Showtime Imputation:** 25 records had missing showtimes. These were imputed with the modal prime-evening screening time (`20:15`).
3. **Invalid Ticket Transactions:** Detected and removed 15 corrupted records with negative ticket quantities.
4. **Capacity Mismatch Reconciliation:** Identified 15 transactions where ticket counts exceeded physical auditorium capacity. Ticket numbers were capped to the physical hall ceiling (`screen_capacity`).
5. **Categorical Standardization:** Standardized inconsistent genre strings (e.g., `'SciFi'` → `'Sci-Fi'`, `'action'` → `'Action'`, whitespace trimmed).
6. **Referential Integrity:** Verified 100% key matching across foreign keys prior to joining.
7. **Cleaned Dataset:** The final cleaned dataset contains **2,185 valid shows**, representing **219,848 tickets sold** and **INR 70,018,680.00** in total box office revenue.

---

## 5. Exploratory Data Analysis & Key Findings

### Q1: Which genres generate the most revenue?
- **Action** is the primary box office driver, generating **INR 17.00M** across 459 shows with an average occupancy of **58.2%**.
- **Sci-Fi** ranks second with **INR 15.91M** (455 shows, 58.0% occupancy).
- **Drama** recorded the lowest revenue at **INR 5.45M** (384 shows) and lowest occupancy (**39.4%**).

### Q2: Which showtimes have higher occupancy?
- Prime evening slots show the highest attendance:
  - **17:00 (5:00 PM):** **60.4%** average occupancy.
  - **20:15 (8:15 PM):** **58.6%** average occupancy.
- Morning slots (**10:30 AM**) have the lowest turnout at **36.6%** occupancy, reflecting significant underutilized capacity during business hours.

### Q3: How do weekends differ from weekdays?
- **Occupancy Uplift:** Weekend screenings achieve **63.2%** occupancy compared to **45.2%** on weekdays (+18.0 percentage point uplift).
- **Revenue per Show:** Weekends generate an average of **INR 40,073.34 per show** vs. **INR 28,821.53** on weekdays (+39.0% increase).

### Q4: Which cinema locations perform best?
- **SilverScreen Downtown (Mumbai)** generated the highest total revenue at **INR 18.09M** across 550 shows (50.4% occupancy).
- **SilverScreen Central (Hyderabad)** followed with **INR 15.75M** (468 shows, 50.4% occupancy).
- **SilverScreen Forum (Chennai)** generated **INR 10.82M** across 417 shows (51.2% occupancy).

### Q5: How do pricing tiers and promotional offers perform?
- **Family Pack (15% off, Premium)** generated the highest promotional revenue (**INR 11.11M**, 49.6% occupancy).
- Standard promotional tiers (**Student Discount 20%** and **Early Bird 28%**) generated **INR 7.11M** and **INR 6.63M** respectively, maintaining ~48–51% occupancy.

### Q6: How does demand decay across release weeks?
- **Week 1:** **INR 25.49M** total revenue across 629 shows (**62.3%** average occupancy).
- **Week 2:** **INR 17.65M** (502 shows, **54.0%** occupancy).
- **Week 3:** **INR 15.16M** (538 shows, **46.3%** occupancy).
- **Week 4:** **INR 11.72M** (516 shows, **36.4%** occupancy).
- Box office revenue declines by **54.0%** from Week 1 to Week 4.

---

## 6. Machine Learning Predictive Model

### Model Architecture & Leakage Prevention
To predict demand for upcoming shows before scheduling:
- **Target Variable:** `tickets` (integer seat count).
- **Features Used (Pre-show only):** `genre`, `language`, `city`, `offer`, `show_hour`, `screen_capacity`, `ticket_price`, `is_weekend`, `holiday`, `release_week`.
- **Leakage Prevention:** Post-show metrics (`revenue`, `occupancy_pct`) are strictly excluded from the feature space.
- **Validation Split:** Chronological 80/20 train-test split (cutoff: September 17, 2026).
  - Train: 1,748 shows (August 1 to September 17)
  - Test: 437 shows (September 17 to September 29)

### Pipeline & Evaluation Results
The pipeline uses Scikit-learn's `ColumnTransformer` with `OneHotEncoder` and `StandardScaler`, paired with a `RandomForestRegressor` (150 trees):

| Model | MAE (Tickets) | RMSE (Tickets) | $R^2$ Score |
| :--- | :---: | :---: | :---: |
| **Baseline (Historical Mean)** | 37.34 | 45.29 | -0.0941 |
| **Random Forest Regressor** | **16.53** | **22.99** | **0.7180** |

The Random Forest model reduces prediction error by **55.7%** over the naive baseline and explains **71.8%** of variance in future show ticket sales.

### Top Demand Drivers
1. `show_hour` (20.70%) — Time of screening is the strongest single predictor.
2. `release_week` (17.62%) — Position in the theatrical lifecycle.
3. `screen_capacity` (17.22%) — Physical auditorium ceiling.
4. `is_weekend` (14.04%) — Weekend surge effect.
5. `holiday` (4.37%) — National calendar holidays.
6. `genre_Action` (3.90%) — High-demand genre appeal.
7. `ticket_price` (3.09%) — Pricing sensitivity.

---

## 7. Business Takeaways & Strategic Recommendations

### Key Analytical Takeaways
1. **Prime Evening & Weekend Concentration:** Over 60% of box office revenue is generated during evening hours (17:00–22:00) and weekend slots. Morning slots (10:30 AM) run at only 36.6% occupancy.
2. **Steep Theatrical Decay Curve:** Demand drops by 54.0% between Week 1 and Week 4, making it inefficient to keep older titles in large 200+ seat screens.

### Operational Recommendations
1. **Dynamic Screen Reallocation (Screen Swapping):** Starting in Week 3 of a movie's run, multiplex programmers should move aging titles to smaller 150-seat auditoriums and allocate large 250-seat auditoriums to new opening-week releases.
2. **Off-Peak Matinee Pricing:** Implement a 20–25% "Early Bird Matinee" discount for weekday 10:30 AM shows. Since fixed operating costs are already incurred, filling empty seats stimulates concession revenue without cannibalizing prime evening demand.
3. **Selective Weekend Surcharges:** Given low price sensitivity and high weekend demand (63.2% occupancy), a 10–12% weekend surcharge on premium/VIP seating tiers can expand margins with minimal volume loss.

### Correlation vs. Causation Considerations
While VIP Recliner tickets (INR 550) correlate with higher revenue per show, increasing ticket prices across low-performing genres or morning showtimes will not cause revenue to rise. Premium tiers succeed because of high customer willingness-to-pay for luxury viewing of major titles, not the price point itself.

---

## 8. Excel Dashboard (`excel/cinema_dashboard.xlsx`)

The automated workbook contains 9 formatted sheets built with OpenPyXL:
1. **`Summary`:** Executive KPI cards (Revenue, Tickets Sold, Occupancy, Weekend Uplift, Model $R^2$), project details, and core takeaways.
2. **`Cleaned Data`:** Formatted table of the cleaned dataset with financial number formats.
3. **`Genre Analysis`:** Genre revenue, tickets, and occupancy table with an embedded column chart.
4. **`Showtime Analysis`:** Show hour occupancy breakdown with an embedded column chart.
5. **`Weekend Analysis`:** Weekday vs. Weekend comparative metrics and chart.
6. **`Cinema Analysis`:** City branch revenue breakdown and chart.
7. **`Offer Analysis`:** Promotional package revenue and volume breakdown.
8. **`Release Trend`:** 4-week theatrical decay curve table and trendline chart.
9. **`Model Metrics`:** Model vs. baseline performance table and top feature importances.

---

## 9. How to Run the Project

### Installation
Ensure Python 3.10+ is installed:
```bash
pip install -r requirements.txt
```

### Run the Full Pipeline
Run the entire automated pipeline with a single command:
```bash
python main.py
```

### Run Individual Modules
```bash
# Data Cleaning & Preparation
python src/data_cleaning.py

# Exploratory Data Analysis & Visualizations
python src/eda_analysis.py

# ML Model Training & Evaluation
python src/train_model.py

# Excel Dashboard Generation
python src/build_dashboard.py

# Interactive Single-Show Prediction
python src/predict_show.py --genre "Action" --city "Mumbai" --hour 20 --capacity 250 --price 380 --weekend 1 --week 1
```

### Interactive Notebook
Open [`notebooks/cinema_analysis.ipynb`](file:///d:/SAT2/notebooks/cinema_analysis.ipynb) in VS Code or JupyterLab to explore the step-by-step analysis interactively.
