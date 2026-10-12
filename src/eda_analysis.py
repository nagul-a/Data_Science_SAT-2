"""
src/eda_analysis.py
-------------------
Exploratory Data Analysis (EDA) for CH29: Cinema Revenue Insight.

Answers the 6 Core Business Questions for SilverScreen Cinemas:
1. Which genres generate the most revenue?
2. Which showtimes have higher occupancy?
3. How do weekends differ from weekdays?
4. Which cinemas perform best?
5. How do offers relate to bookings and revenue?
6. How does release week influence demand?

Computes all required aggregated metrics, saves summary CSV tables in output/,
and exports 6 high-resolution labelled charts to output/charts/.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Set style aesthetics
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.size"] = 10
plt.rcParams["axes.titlesize"] = 12
plt.rcParams["axes.labelsize"] = 11


def load_cleaned_data(output_dir):
    """Load cleaned cinema dataset."""
    filepath = os.path.join(output_dir, "cleaned_cinema_data.csv")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Cleaned dataset not found at {filepath}. Run data_cleaning.py first!")
    df = pd.read_csv(filepath)
    return df


def calculate_overall_kpis(df):
    """Calculate and display high-level executive KPIs."""
    total_revenue = df["revenue"].sum()
    total_tickets = df["tickets"].sum()
    total_capacity = df["screen_capacity"].sum()
    overall_occupancy = (total_tickets / total_capacity) * 100
    avg_occupancy_per_show = df["occupancy_pct"].mean()
    avg_ticket_price = df["revenue"].sum() / total_tickets
    total_shows = len(df)
    
    print("\n" + "=" * 70)
    print("SILVERSCREEN CINEMAS - EXECUTIVE KPI DASHBOARD")
    print("=" * 70)
    print(f" Total Shows Analyzed:        {total_shows:,}")
    print(f" Total Tickets Sold:          {total_tickets:,}")
    print(f" Total Revenue:               INR {total_revenue:,.2f} ({total_revenue/1e6:.2f} Million)")
    print(f" Total Seat Capacity Offered: {total_capacity:,}")
    print(f" Overall Seat Occupancy:      {overall_occupancy:.2f}%")
    print(f" Mean Show Occupancy:         {avg_occupancy_per_show:.2f}%")
    print(f" Average Realized Price:      INR {avg_ticket_price:.2f} per ticket")
    print("=" * 70)
    
    return {
        "total_shows": total_shows,
        "total_tickets": total_tickets,
        "total_revenue": total_revenue,
        "total_capacity": total_capacity,
        "overall_occupancy": overall_occupancy,
        "avg_occupancy_per_show": avg_occupancy_per_show,
        "avg_ticket_price": avg_ticket_price
    }


def analyze_genres(df, output_dir, charts_dir):
    """Q1: Which genres generate the most revenue?"""
    print("\n[Q1] Analyzing Revenue by Movie Genre...")
    
    genre_summary = df.groupby("genre").agg(
        shows=("booking_id", "count"),
        total_tickets=("tickets", "sum"),
        total_capacity=("screen_capacity", "sum"),
        total_revenue=("revenue", "sum"),
        avg_occupancy_pct=("occupancy_pct", "mean")
    ).reset_index()
    
    genre_summary["overall_occupancy_pct"] = (
        (genre_summary["total_tickets"] / genre_summary["total_capacity"]) * 100
    ).round(2)
    genre_summary["avg_revenue_per_show"] = (
        genre_summary["total_revenue"] / genre_summary["shows"]
    ).round(2)
    
    genre_summary = genre_summary.sort_values(by="total_revenue", ascending=False).reset_index(drop=True)
    
    # Save CSV
    csv_path = os.path.join(output_dir, "genre_performance.csv")
    genre_summary.to_csv(csv_path, index=False)
    print(f" [+] Saved genre performance table to {csv_path}")
    print(genre_summary[["genre", "total_tickets", "total_revenue", "avg_occupancy_pct", "avg_revenue_per_show"]])
    
    # Chart 1
    fig, ax1 = plt.subplots(figsize=(10, 5.5))
    colors = ["#E11D48", "#2563EB", "#059669", "#D97706", "#7C3AED", "#0891B2", "#475569"]
    
    bars = ax1.bar(
        genre_summary["genre"],
        genre_summary["total_revenue"] / 1e6,
        color=colors[:len(genre_summary)],
        edgecolor="#1E293B",
        linewidth=0.8,
        alpha=0.9
    )
    
    ax1.set_ylabel("Total Revenue (Million INR)", fontsize=11, fontweight="bold", color="#0F172A")
    ax1.set_title("SilverScreen Cinemas: Total Revenue & Occupancy Rate by Genre", fontsize=13, fontweight="bold", pad=15)
    ax1.set_xlabel("Movie Genre", fontsize=11, fontweight="bold")
    ax1.grid(axis="y", linestyle="--", alpha=0.3)
    
    # Add values on bars
    for bar in bars:
        h = bar.get_height()
        ax1.annotate(f"₹{h:.2f}M",
                     xy=(bar.get_x() + bar.get_width() / 2, h),
                     xytext=(0, 4), textcoords="offset points",
                     ha="center", va="bottom", fontsize=9, fontweight="bold")
        
    # Secondary axis for occupancy %
    ax2 = ax1.twinx()
    ax2.plot(genre_summary["genre"], genre_summary["avg_occupancy_pct"], color="#0F172A", marker="o", linewidth=2.2, label="Avg Occupancy %")
    ax2.set_ylabel("Avg Occupancy (%)", fontsize=11, fontweight="bold", color="#0F172A")
    ax2.set_ylim(20, 85)
    ax2.grid(False)
    
    for i, txt in enumerate(genre_summary["avg_occupancy_pct"]):
        ax2.annotate(f"{txt:.1f}%", (i, txt), xytext=(0, 7), textcoords="offset points", ha="center", fontsize=8.5, fontweight="bold", color="#0F172A")
        
    plt.tight_layout()
    chart_path = os.path.join(charts_dir, "chart1_revenue_by_genre.png")
    plt.savefig(chart_path, dpi=300)
    plt.close()
    print(f" [+] Saved Chart 1 to {chart_path}")
    
    return genre_summary


def analyze_showtimes(df, output_dir, charts_dir):
    """Q2: Which showtimes have higher occupancy?"""
    print("\n[Q2] Analyzing Occupancy by Showtime...")
    
    time_summary = df.groupby(["show_time", "show_hour"]).agg(
        shows=("booking_id", "count"),
        total_tickets=("tickets", "sum"),
        total_capacity=("screen_capacity", "sum"),
        total_revenue=("revenue", "sum"),
        avg_occupancy_pct=("occupancy_pct", "mean")
    ).reset_index()
    
    time_summary["overall_occupancy_pct"] = (
        (time_summary["total_tickets"] / time_summary["total_capacity"]) * 100
    ).round(2)
    time_summary = time_summary.sort_values(by="show_hour").reset_index(drop=True)
    
    # Save CSV
    csv_path = os.path.join(output_dir, "showtime_performance.csv")
    time_summary.to_csv(csv_path, index=False)
    print(f" [+] Saved showtime performance table to {csv_path}")
    print(time_summary[["show_time", "show_hour", "shows", "total_tickets", "avg_occupancy_pct", "total_revenue"]])
    
    # Chart 2
    fig, ax = plt.subplots(figsize=(9, 5))
    bar_colors = ["#94A3B8" if occ < 45 else ("#059669" if occ > 55 else "#2563EB") for occ in time_summary["avg_occupancy_pct"]]
    
    bars = ax.bar(time_summary["show_time"], time_summary["avg_occupancy_pct"], color=bar_colors, edgecolor="#1E293B", width=0.55)
    ax.set_title("SilverScreen Cinemas: Average Occupancy Rate by Show Time Slot", fontsize=13, fontweight="bold", pad=15)
    ax.set_xlabel("Show Time", fontsize=11, fontweight="bold")
    ax.set_ylabel("Average Occupancy (%)", fontsize=11, fontweight="bold")
    ax.set_ylim(0, 80)
    ax.axhline(50, color="#E11D48", linestyle="--", linewidth=1.2, label="50% Occupancy Benchmark")
    
    for bar in bars:
        h = bar.get_height()
        ax.annotate(f"{h:.1f}%",
                    xy=(bar.get_x() + bar.get_width() / 2, h),
                    xytext=(0, 4), textcoords="offset points",
                    ha="center", va="bottom", fontsize=9.5, fontweight="bold")
        
    ax.legend(loc="upper left")
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    plt.tight_layout()
    chart_path = os.path.join(charts_dir, "chart2_occupancy_by_showtime.png")
    plt.savefig(chart_path, dpi=300)
    plt.close()
    print(f" [+] Saved Chart 2 to {chart_path}")
    
    return time_summary


def analyze_weekend_vs_weekday(df, output_dir, charts_dir):
    """Q3: How do weekends differ from weekdays?"""
    print("\n[Q3] Analyzing Weekend vs Weekday Performance...")
    
    df["day_category"] = df["is_weekend"].map({1: "Weekend (Sat-Sun)", 0: "Weekday (Mon-Fri)"})
    
    weekend_summary = df.groupby("day_category").agg(
        shows=("booking_id", "count"),
        total_tickets=("tickets", "sum"),
        total_capacity=("screen_capacity", "sum"),
        total_revenue=("revenue", "sum"),
        avg_occupancy_pct=("occupancy_pct", "mean"),
        avg_revenue_per_show=("revenue", "mean"),
        avg_tickets_per_show=("tickets", "mean")
    ).reset_index()
    
    weekend_summary["overall_occupancy_pct"] = (
        (weekend_summary["total_tickets"] / weekend_summary["total_capacity"]) * 100
    ).round(2)
    weekend_summary["avg_revenue_per_show"] = weekend_summary["avg_revenue_per_show"].round(2)
    weekend_summary["avg_tickets_per_show"] = weekend_summary["avg_tickets_per_show"].round(2)
    
    # Save CSV
    csv_path = os.path.join(output_dir, "weekend_performance.csv")
    weekend_summary.to_csv(csv_path, index=False)
    print(f" [+] Saved weekend performance table to {csv_path}")
    print(weekend_summary[["day_category", "shows", "total_revenue", "avg_occupancy_pct", "avg_revenue_per_show", "avg_tickets_per_show"]])
    
    # Chart 3
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.8))
    
    # Subplot 1: Occupancy comparison
    palette = ["#3B82F6", "#EC4899"]
    bars1 = ax1.bar(weekend_summary["day_category"], weekend_summary["avg_occupancy_pct"], color=palette, width=0.5, edgecolor="#1E293B")
    ax1.set_title("Average Occupancy Rate (%)", fontsize=11, fontweight="bold")
    ax1.set_ylabel("Occupancy (%)", fontsize=10, fontweight="bold")
    ax1.set_ylim(0, 80)
    ax1.grid(axis="y", linestyle="--", alpha=0.3)
    for bar in bars1:
        h = bar.get_height()
        ax1.annotate(f"{h:.1f}%", (bar.get_x() + bar.get_width()/2, h), xytext=(0, 4), textcoords="offset points", ha="center", fontweight="bold")
        
    # Subplot 2: Average Revenue per Show
    bars2 = ax2.bar(weekend_summary["day_category"], weekend_summary["avg_revenue_per_show"], color=palette, width=0.5, edgecolor="#1E293B")
    ax2.set_title("Average Revenue per Show (INR)", fontsize=11, fontweight="bold")
    ax2.set_ylabel("Revenue per Show (INR)", fontsize=10, fontweight="bold")
    ax2.set_ylim(0, max(weekend_summary["avg_revenue_per_show"]) * 1.25)
    ax2.grid(axis="y", linestyle="--", alpha=0.3)
    for bar in bars2:
        h = bar.get_height()
        ax2.annotate(f"₹{h:,.0f}", (bar.get_x() + bar.get_width()/2, h), xytext=(0, 4), textcoords="offset points", ha="center", fontweight="bold")
        
    plt.suptitle("SilverScreen Cinemas: Weekend vs. Weekday Performance Comparison", fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    chart_path = os.path.join(charts_dir, "chart3_weekend_vs_weekday.png")
    plt.savefig(chart_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f" [+] Saved Chart 3 to {chart_path}")
    
    return weekend_summary


def analyze_cinemas(df, output_dir, charts_dir):
    """Q4: Which cinemas perform best?"""
    print("\n[Q4] Analyzing Cinema Performance Across Locations...")
    
    cinema_summary = df.groupby(["cinema", "city"]).agg(
        shows=("booking_id", "count"),
        screen_capacity=("screen_capacity", "first"),
        total_tickets=("tickets", "sum"),
        total_capacity=("screen_capacity", "sum"),
        total_revenue=("revenue", "sum"),
        avg_occupancy_pct=("occupancy_pct", "mean"),
        avg_revenue_per_show=("revenue", "mean")
    ).reset_index()
    
    cinema_summary["overall_occupancy_pct"] = (
        (cinema_summary["total_tickets"] / cinema_summary["total_capacity"]) * 100
    ).round(2)
    cinema_summary["avg_revenue_per_show"] = cinema_summary["avg_revenue_per_show"].round(2)
    cinema_summary = cinema_summary.sort_values(by="total_revenue", ascending=False).reset_index(drop=True)
    
    # Save CSV
    csv_path = os.path.join(output_dir, "cinema_performance.csv")
    cinema_summary.to_csv(csv_path, index=False)
    print(f" [+] Saved cinema performance table to {csv_path}")
    print(cinema_summary[["cinema", "city", "screen_capacity", "total_tickets", "total_revenue", "avg_occupancy_pct"]])
    
    # Chart 4
    fig, ax1 = plt.subplots(figsize=(10, 5.2))
    cinemas_labels = [f"{row['cinema']}\n({row['city']})" for _, row in cinema_summary.iterrows()]
    
    bars = ax1.bar(cinemas_labels, cinema_summary["total_revenue"] / 1e6, color="#0284C7", width=0.55, edgecolor="#0F172A")
    ax1.set_title("SilverScreen Cinemas: Performance Across Locations (Revenue & Occupancy)", fontsize=13, fontweight="bold", pad=15)
    ax1.set_ylabel("Total Revenue (Million INR)", fontsize=11, fontweight="bold", color="#0F172A")
    ax1.grid(axis="y", linestyle="--", alpha=0.3)
    
    for bar in bars:
        h = bar.get_height()
        ax1.annotate(f"₹{h:.2f}M", (bar.get_x() + bar.get_width()/2, h), xytext=(0, 4), textcoords="offset points", ha="center", fontsize=9.5, fontweight="bold")
        
    ax2 = ax1.twinx()
    ax2.plot(cinemas_labels, cinema_summary["overall_occupancy_pct"], color="#E11D48", marker="s", markersize=7, linewidth=2.2, label="Occupancy %")
    ax2.set_ylabel("Overall Occupancy (%)", fontsize=11, fontweight="bold", color="#E11D48")
    ax2.set_ylim(25, 75)
    ax2.grid(False)
    
    for i, txt in enumerate(cinema_summary["overall_occupancy_pct"]):
        ax2.annotate(f"{txt:.1f}%", (i, txt), xytext=(0, 7), textcoords="offset points", ha="center", fontsize=9, fontweight="bold", color="#E11D48")
        
    plt.tight_layout()
    chart_path = os.path.join(charts_dir, "chart4_cinema_performance.png")
    plt.savefig(chart_path, dpi=300)
    plt.close()
    print(f" [+] Saved Chart 4 to {chart_path}")
    
    return cinema_summary


def analyze_offers(df, output_dir, charts_dir):
    """Q5: How do offers relate to bookings and revenue?"""
    print("\n[Q5] Analyzing Pricing Offers & Promotions...")
    
    offer_summary = df.groupby(["offer", "seat_class"]).agg(
        shows=("booking_id", "count"),
        ticket_price=("ticket_price", "first"),
        total_tickets=("tickets", "sum"),
        total_revenue=("revenue", "sum"),
        avg_occupancy_pct=("occupancy_pct", "mean"),
        avg_revenue_per_show=("revenue", "mean"),
        avg_tickets_per_show=("tickets", "mean")
    ).reset_index()
    
    offer_summary["avg_revenue_per_show"] = offer_summary["avg_revenue_per_show"].round(2)
    offer_summary["avg_tickets_per_show"] = offer_summary["avg_tickets_per_show"].round(2)
    offer_summary = offer_summary.sort_values(by="total_revenue", ascending=False).reset_index(drop=True)
    
    # Save CSV
    csv_path = os.path.join(output_dir, "offer_performance.csv")
    offer_summary.to_csv(csv_path, index=False)
    print(f" [+] Saved offer performance table to {csv_path}")
    print(offer_summary[["offer", "seat_class", "ticket_price", "shows", "total_tickets", "total_revenue", "avg_occupancy_pct"]])
    
    # Chart 5
    fig, ax = plt.subplots(figsize=(10, 5.2))
    labels = [f"{row['offer']}\n({row['seat_class']})" for _, row in offer_summary.iterrows()]
    
    x = np.arange(len(labels))
    width = 0.38
    
    ax.bar(x - width/2, offer_summary["avg_tickets_per_show"], width, label="Avg Tickets / Show", color="#059669", edgecolor="#1E293B")
    ax.set_ylabel("Average Tickets Sold per Show", fontsize=11, fontweight="bold", color="#059669")
    ax.set_title("SilverScreen Cinemas: Pricing Tier & Offer Impact on Volume & Yield", fontsize=13, fontweight="bold", pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9)
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    
    ax2 = ax.twinx()
    ax2.plot(x + width/2, offer_summary["avg_revenue_per_show"], color="#D97706", marker="D", linewidth=2.2, label="Avg Revenue / Show (INR)")
    ax2.set_ylabel("Avg Revenue per Show (INR)", fontsize=11, fontweight="bold", color="#D97706")
    ax2.grid(False)
    
    for i, row in offer_summary.iterrows():
        ax.annotate(f"{row['avg_tickets_per_show']:.0f}", (i - width/2, row['avg_tickets_per_show']), xytext=(0, 3), textcoords="offset points", ha="center", fontsize=8.5, fontweight="bold")
        ax2.annotate(f"₹{row['avg_revenue_per_show']:,.0f}", (i + width/2, row['avg_revenue_per_show']), xytext=(0, 6), textcoords="offset points", ha="center", fontsize=8.5, fontweight="bold", color="#B45309")
        
    plt.tight_layout()
    chart_path = os.path.join(charts_dir, "chart5_offer_performance.png")
    plt.savefig(chart_path, dpi=300)
    plt.close()
    print(f" [+] Saved Chart 5 to {chart_path}")
    
    return offer_summary


def analyze_release_week(df, output_dir, charts_dir):
    """Q6: How does release week influence demand?"""
    print("\n[Q6] Analyzing Demand Decay Across Release Weeks...")
    
    release_summary = df.groupby("release_week").agg(
        shows=("booking_id", "count"),
        total_tickets=("tickets", "sum"),
        total_capacity=("screen_capacity", "sum"),
        total_revenue=("revenue", "sum"),
        avg_occupancy_pct=("occupancy_pct", "mean"),
        avg_revenue_per_show=("revenue", "mean"),
        avg_tickets_per_show=("tickets", "mean")
    ).reset_index()
    
    release_summary["overall_occupancy_pct"] = (
        (release_summary["total_tickets"] / release_summary["total_capacity"]) * 100
    ).round(2)
    release_summary["avg_revenue_per_show"] = release_summary["avg_revenue_per_show"].round(2)
    release_summary["avg_tickets_per_show"] = release_summary["avg_tickets_per_show"].round(2)
    release_summary = release_summary.sort_values(by="release_week").reset_index(drop=True)
    
    # Save CSV
    csv_path = os.path.join(output_dir, "release_week_performance.csv")
    release_summary.to_csv(csv_path, index=False)
    print(f" [+] Saved release week performance table to {csv_path}")
    print(release_summary[["release_week", "shows", "total_tickets", "total_revenue", "avg_occupancy_pct", "avg_tickets_per_show"]])
    
    # Chart 6
    fig, ax1 = plt.subplots(figsize=(9, 5))
    weeks = [f"Week {w}" for w in release_summary["release_week"]]
    
    ax1.plot(weeks, release_summary["total_revenue"] / 1e6, color="#7C3AED", marker="o", markersize=8, linewidth=2.5, label="Revenue (Million INR)")
    ax1.set_title("SilverScreen Cinemas: Theatrical Run Demand Curve by Release Week", fontsize=13, fontweight="bold", pad=15)
    ax1.set_xlabel("Release Week of Theatrical Run", fontsize=11, fontweight="bold")
    ax1.set_ylabel("Total Revenue (Million INR)", fontsize=11, fontweight="bold", color="#7C3AED")
    ax1.grid(True, linestyle="--", alpha=0.3)
    
    for i, val in enumerate(release_summary["total_revenue"] / 1e6):
        ax1.annotate(f"₹{val:.2f}M", (i, val), xytext=(0, 8), textcoords="offset points", ha="center", fontweight="bold", color="#7C3AED")
        
    ax2 = ax1.twinx()
    ax2.plot(weeks, release_summary["avg_occupancy_pct"], color="#059669", marker="s", markersize=7, linewidth=2, linestyle="--", label="Avg Occupancy %")
    ax2.set_ylabel("Average Occupancy (%)", fontsize=11, fontweight="bold", color="#059669")
    ax2.set_ylim(20, 75)
    ax2.grid(False)
    
    for i, val in enumerate(release_summary["avg_occupancy_pct"]):
        ax2.annotate(f"{val:.1f}%", (i, val), xytext=(0, -15), textcoords="offset points", ha="center", fontweight="bold", color="#059669")
        
    plt.tight_layout()
    chart_path = os.path.join(charts_dir, "chart6_release_week_demand.png")
    plt.savefig(chart_path, dpi=300)
    plt.close()
    print(f" [+] Saved Chart 6 to {chart_path}")
    
    return release_summary


def print_top_findings(kpis, genre_df, time_df, weekend_df, cinema_df, offer_df, release_df):
    """Print the top findings using the actual computed results."""
    print("\n" + "=" * 70)
    print("KEY BUSINESS FINDINGS & METRICS")
    print("=" * 70)
    
    top_genre = genre_df.iloc[0]
    bottom_genre = genre_df.iloc[-1]
    print(f"1. Top Revenue Genre: {top_genre['genre']} generated INR {top_genre['total_revenue']:,.2f} "
          f"({top_genre['total_revenue']/1e6:.2f}M) across {top_genre['shows']} shows, with an average occupancy of {top_genre['avg_occupancy_pct']:.1f}%.")
    print(f"   Lowest Revenue Genre: {bottom_genre['genre']} generated INR {bottom_genre['total_revenue']:,.2f} "
          f"({bottom_genre['total_revenue']/1e6:.2f}M) with {bottom_genre['avg_occupancy_pct']:.1f}% occupancy.")
    
    top_time = time_df.sort_values(by="avg_occupancy_pct", ascending=False).iloc[0]
    morning_time = time_df.sort_values(by="avg_occupancy_pct", ascending=True).iloc[0]
    print(f"\n2. Prime Showtimes: The {top_time['show_time']} show recorded the highest average occupancy at {top_time['avg_occupancy_pct']:.1f}%, "
          f"compared to morning shows ({morning_time['show_time']}) at only {morning_time['avg_occupancy_pct']:.1f}%.")
    
    wknd = weekend_df[weekend_df["day_category"].str.contains("Weekend")].iloc[0]
    wkdy = weekend_df[weekend_df["day_category"].str.contains("Weekday")].iloc[0]
    occ_diff = wknd['avg_occupancy_pct'] - wkdy['avg_occupancy_pct']
    print(f"\n3. Weekend Premium: Weekends achieved an average occupancy of {wknd['avg_occupancy_pct']:.1f}% vs {wkdy['avg_occupancy_pct']:.1f}% on weekdays "
          f"(+{occ_diff:.1f}% uplift). Average revenue per show on weekends was INR {wknd['avg_revenue_per_show']:,.2f} vs INR {wkdy['avg_revenue_per_show']:,.2f} on weekdays.")
    
    top_cinema = cinema_df.iloc[0]
    print(f"\n4. Leading Cinema: {top_cinema['cinema']} in {top_cinema['city']} led network performance with INR {top_cinema['total_revenue']:,.2f} "
          f"({top_cinema['total_revenue']/1e6:.2f}M) and {top_cinema['overall_occupancy_pct']:.1f}% overall occupancy.")
    
    top_rev_offer = offer_df.iloc[0]
    print(f"\n5. Offer Performance: '{top_rev_offer['offer']}' ({top_rev_offer['seat_class']}) generated the highest total revenue of INR {top_rev_offer['total_revenue']:,.2f}. "
          f"Promotional packages drove strong volume while maintaining healthy margins.")
    
    week1 = release_df[release_df["release_week"] == 1].iloc[0]
    week4 = release_df[release_df["release_week"] == 4].iloc[0]
    decay_pct = ((week1['total_revenue'] - week4['total_revenue']) / week1['total_revenue']) * 100
    print(f"\n6. Theatrical Decay: Week 1 captured INR {week1['total_revenue']:,.2f} ({week1['total_revenue']/1e6:.2f}M) at {week1['avg_occupancy_pct']:.1f}% occupancy, "
          f"declining by {decay_pct:.1f}% by Week 4 (INR {week4['total_revenue']:,.2f}, {week4['avg_occupancy_pct']:.1f}% occupancy).")
    print("=" * 70)


def main():
    """Main EDA execution routine."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(base_dir, "output")
    charts_dir = os.path.join(output_dir, "charts")
    os.makedirs(charts_dir, exist_ok=True)
    
    df = load_cleaned_data(output_dir)
    kpis = calculate_overall_kpis(df)
    
    genre_df = analyze_genres(df, output_dir, charts_dir)
    time_df = analyze_showtimes(df, output_dir, charts_dir)
    weekend_df = analyze_weekend_vs_weekday(df, output_dir, charts_dir)
    cinema_df = analyze_cinemas(df, output_dir, charts_dir)
    offer_df = analyze_offers(df, output_dir, charts_dir)
    release_df = analyze_release_week(df, output_dir, charts_dir)
    
    print_top_findings(kpis, genre_df, time_df, weekend_df, cinema_df, offer_df, release_df)
    print("\n[+] Exploratory Data Analysis completed successfully. All charts and tables generated.")


if __name__ == "__main__":
    main()
