"""
src/data_generation.py
----------------------
Multiplex Booking Dataset Generator for SilverScreen Cinemas.
Generates baseline relational datasets modeling multiplex booking operations.
"""

import os
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Set fixed random seed for reproducible results
RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)


def generate_movies():
    """
    Generate movies dataset with intentional inconsistent genre labels
    to test data cleaning and standardization.
    """
    movies_data = [
        {"movie_id": "M01", "movie": "Starlight Odyssey", "genre": "Sci-Fi", "language": "English", "runtime": 148, "certification": "PG-13"},
        {"movie_id": "M02", "movie": "Cyber Runner", "genre": "SciFi", "language": "English", "runtime": 125, "certification": "R"},  # Inconsistent genre
        {"movie_id": "M03", "movie": "Mumbai Express", "genre": "Action", "language": "Hindi", "runtime": 155, "certification": "UA"},
        {"movie_id": "M04", "movie": "Shadow Strike", "genre": "action", "language": "English", "runtime": 118, "certification": "PG-13"},  # Inconsistent genre
        {"movie_id": "M05", "movie": "Laugh Riot", "genre": "Comedy", "language": "Hindi", "runtime": 130, "certification": "U"},
        {"movie_id": "M06", "movie": "Crazy Summer", "genre": "comedy ", "language": "English", "runtime": 105, "certification": "PG-13"},  # Inconsistent genre with trailing space
        {"movie_id": "M07", "movie": "Whispering Pines", "genre": "Horror", "language": "English", "runtime": 98, "certification": "A"},
        {"movie_id": "M08", "movie": "Love in Paris", "genre": "Romance", "language": "French", "runtime": 112, "certification": "UA"},
        {"movie_id": "M09", "movie": "Dragon Kingdom", "genre": "Animation", "language": "English", "runtime": 102, "certification": "U"},
        {"movie_id": "M10", "movie": "Crimson Verdict", "genre": "Drama", "language": "Hindi", "runtime": 140, "certification": "UA"},
    ]
    return pd.DataFrame(movies_data)


def generate_cinemas():
    """
    Generate cinemas dataset with cinema details and seating capacities.
    """
    cinemas_data = [
        {"cinema_id": "C01", "cinema": "SilverScreen Downtown", "city": "Mumbai", "screen_capacity": 250},
        {"cinema_id": "C02", "cinema": "SilverScreen Galleria", "city": "Delhi", "screen_capacity": 200},
        {"cinema_id": "C03", "cinema": "SilverScreen Nexus", "city": "Bengaluru", "screen_capacity": 180},
        {"cinema_id": "C04", "cinema": "SilverScreen Forum", "city": "Chennai", "screen_capacity": 150},
        {"cinema_id": "C05", "cinema": "SilverScreen Central", "city": "Hyderabad", "screen_capacity": 220},
    ]
    return pd.DataFrame(cinemas_data)


def generate_pricing():
    """
    Generate pricing tiers, seat classes, ticket prices, and promotional offers.
    """
    pricing_data = [
        {"pricing_id": "P01", "seat_class": "Standard", "ticket_price": 250.0, "offer": "None"},
        {"pricing_id": "P02", "seat_class": "Premium", "ticket_price": 380.0, "offer": "None"},
        {"pricing_id": "P03", "seat_class": "Standard", "ticket_price": 200.0, "offer": "Student Discount 20%"},
        {"pricing_id": "P04", "seat_class": "Premium", "ticket_price": 320.0, "offer": "Family Pack 15%"},
        {"pricing_id": "P05", "seat_class": "Standard", "ticket_price": 180.0, "offer": "Early Bird 28%"},
        {"pricing_id": "P06", "seat_class": "VIP Recliner", "ticket_price": 550.0, "offer": "None"},
    ]
    return pd.DataFrame(pricing_data)


def generate_calendar(start_date="2026-08-01", days=60):
    """
    Generate calendar table across 60 days with weekdays, holidays, and release week cycles.
    """
    start = datetime.strptime(start_date, "%Y-%m-%d")
    calendar_rows = []
    
    # Selected national/regional holidays in the timeframe
    holidays_set = {"2026-08-15", "2026-08-28", "2026-09-04", "2026-09-17"}

    for i in range(days):
        current_date = start + timedelta(days=i)
        date_str = current_date.strftime("%Y-%m-%d")
        weekday = current_date.strftime("%A")
        holiday = 1 if date_str in holidays_set else 0
        
        # 4-week theatrical release cycle repeating across the calendar window
        release_week = ((i // 7) % 4) + 1
        
        calendar_rows.append({
            "show_date": date_str,
            "weekday": weekday,
            "holiday": holiday,
            "release_week": release_week
        })
        
    return pd.DataFrame(calendar_rows)


def generate_bookings(movies_df, cinemas_df, pricing_df, calendar_df, num_records=2200):
    """
    Generate synthetic bookings with realistic business logic and intentional anomalies:
    1. Controlled missing showtimes (~25 rows)
    2. Controlled duplicate bookings (~30 rows)
    3. Invalid negative or zero tickets (~15 rows)
    4. Capacity mismatches where tickets > screen_capacity (~15 rows)
    """
    standard_times = ["10:30", "13:45", "17:00", "20:15", "22:45"]
    screens = ["Screen 1", "Screen 2", "Screen 3"]
    
    # Map lookups for realistic occupancy calculation
    cinema_capacity_map = dict(zip(cinemas_df["cinema_id"], cinemas_df["screen_capacity"]))
    price_map = dict(zip(pricing_df["pricing_id"], pricing_df["ticket_price"]))
    calendar_map = {row["show_date"]: row for _, row in calendar_df.iterrows()}
    
    # Genre appeal multipliers for ticket sales
    genre_multipliers = {
        "M01": 1.25, "M02": 1.15, "M03": 1.30, "M04": 1.10,
        "M05": 1.05, "M06": 0.95, "M07": 0.90, "M08": 0.85,
        "M09": 1.10, "M10": 0.80
    }
    
    rows = []
    
    for i in range(1, num_records + 1):
        booking_id = f"BK{i:05d}"
        show_id = f"SH{(i % 600) + 1:04d}"
        cinema_id = random.choice(cinemas_df["cinema_id"].tolist())
        screen = random.choice(screens)
        movie_id = random.choice(movies_df["movie_id"].tolist())
        show_date = random.choice(calendar_df["show_date"].tolist())
        show_time = random.choice(standard_times)
        pricing_id = random.choice(pricing_df["pricing_id"].tolist())
        
        cal_info = calendar_map[show_date]
        capacity = cinema_capacity_map[cinema_id]
        ticket_price = price_map[pricing_id]
        
        # Calculate base occupancy factor based on business realities
        base_occ = 0.45
        
        # Weekend boost (Friday evening, Saturday, Sunday)
        if cal_info["weekday"] in ["Saturday", "Sunday"]:
            base_occ += 0.22
        elif cal_info["weekday"] == "Friday" and show_time in ["17:00", "20:15", "22:45"]:
            base_occ += 0.15
            
        # Holiday boost
        if cal_info["holiday"] == 1:
            base_occ += 0.20
            
        # Prime showtime boost (evening and night)
        if show_time in ["17:00", "20:15"]:
            base_occ += 0.15
        elif show_time == "10:30":
            base_occ -= 0.12
            
        # Movie genre multiplier
        base_occ *= genre_multipliers.get(movie_id, 1.0)
        
        # Release week decay (Week 1 = 1.0, Week 2 = 0.85, Week 3 = 0.70, Week 4 = 0.55)
        week_decay = {1: 1.05, 2: 0.90, 3: 0.75, 4: 0.60}.get(cal_info["release_week"], 0.8)
        base_occ *= week_decay
        
        # Add random noise
        noise = np.random.normal(0, 0.08)
        occ_rate = np.clip(base_occ + noise, 0.10, 0.96)
        
        # Realistic tickets sold
        tickets = int(round(capacity * occ_rate))
        revenue = round(tickets * ticket_price, 2)
        
        rows.append({
            "booking_id": booking_id,
            "show_id": show_id,
            "cinema_id": cinema_id,
            "screen": screen,
            "movie_id": movie_id,
            "show_date": show_date,
            "show_time": show_time,
            "pricing_id": pricing_id,
            "tickets": tickets,
            "revenue": revenue
        })
        
    bookings_df = pd.DataFrame(rows)
    
    # -------------------------------------------------------------
    # Inject intentional data quality issues for cleaning exercise:
    # -------------------------------------------------------------
    
    # 1. Missing showtimes (~25 rows)
    missing_time_indices = np.random.choice(bookings_df.index, size=25, replace=False)
    bookings_df.loc[missing_time_indices, "show_time"] = np.nan
    
    # 2. Invalid negative ticket counts (~15 rows)
    invalid_ticket_indices = np.random.choice(
        [idx for idx in bookings_df.index if idx not in missing_time_indices],
        size=15,
        replace=False
    )
    for idx in invalid_ticket_indices:
        bad_val = -random.randint(1, 10)
        bookings_df.loc[idx, "tickets"] = bad_val
        # Correspondingly revenue might also be corrupted
        bookings_df.loc[idx, "revenue"] = round(bad_val * price_map[bookings_df.loc[idx, "pricing_id"]], 2)
        
    # 3. Capacity mismatches (~15 rows where tickets > screen_capacity)
    capacity_mismatch_indices = np.random.choice(
        [idx for idx in bookings_df.index if idx not in missing_time_indices and idx not in invalid_ticket_indices],
        size=15,
        replace=False
    )
    for idx in capacity_mismatch_indices:
        cap = cinema_capacity_map[bookings_df.loc[idx, "cinema_id"]]
        excess_tickets = cap + random.randint(25, 75)
        bookings_df.loc[idx, "tickets"] = excess_tickets
        bookings_df.loc[idx, "revenue"] = round(excess_tickets * price_map[bookings_df.loc[idx, "pricing_id"]], 2)
        
    # 4. Duplicate bookings (~30 duplicated rows appended)
    dup_sample = bookings_df.sample(n=30, random_state=RANDOM_SEED)
    bookings_df = pd.concat([bookings_df, dup_sample], ignore_index=True)
    
    return bookings_df


def main():
    """Generate all datasets and write them to data/ folder."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    
    print("[*] Generating synthetic datasets for SilverScreen Cinemas...")
    
    movies_df = generate_movies()
    cinemas_df = generate_cinemas()
    pricing_df = generate_pricing()
    calendar_df = generate_calendar(start_date="2026-08-01", days=60)
    bookings_df = generate_bookings(movies_df, cinemas_df, pricing_df, calendar_df, num_records=2200)
    
    movies_path = os.path.join(data_dir, "movies.csv")
    cinemas_path = os.path.join(data_dir, "cinemas.csv")
    pricing_path = os.path.join(data_dir, "pricing.csv")
    calendar_path = os.path.join(data_dir, "calendar.csv")
    bookings_path = os.path.join(data_dir, "bookings.csv")
    
    movies_df.to_csv(movies_path, index=False)
    cinemas_df.to_csv(cinemas_path, index=False)
    pricing_df.to_csv(pricing_path, index=False)
    calendar_df.to_csv(calendar_path, index=False)
    bookings_df.to_csv(bookings_path, index=False)
    
    print(f"[+] Saved movies:   {movies_path} ({len(movies_df)} rows)")
    print(f"[+] Saved cinemas:  {cinemas_path} ({len(cinemas_df)} rows)")
    print(f"[+] Saved pricing:  {pricing_path} ({len(pricing_df)} rows)")
    print(f"[+] Saved calendar: {calendar_path} ({len(calendar_df)} rows)")
    print(f"[+] Saved bookings: {bookings_path} ({len(bookings_df)} rows)")
    print("[+] Dataset generation complete.")


if __name__ == "__main__":
    main()
