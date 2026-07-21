# ============================================================
# HOTEL INTERNAL MANAGEMENT SYSTEM 
# Sky/Silver Theme • Powerful • AI‑Augmented
# ============================================================
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import os
import altair as alt
import json
import base64
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# ---------- CONFIG ----------
DB_PATH = "hotel_data.db"

# ============================================================
# DATABASE SETUP
# ============================================================
def get_db():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_db()
    c = conn.cursor()
    # Daily records
    c.execute('''CREATE TABLE IF NOT EXISTS HotelDaily (
        Id INTEGER PRIMARY KEY AUTOINCREMENT,
        Date TEXT UNIQUE,
        Income REAL DEFAULT 0,
        Expenses REAL DEFAULT 0,
        Profit REAL DEFAULT 0,
        VAT REAL DEFAULT 0,
        IncomeTax REAL DEFAULT 0,
        TotalTax REAL DEFAULT 0,
        NetProfit REAL DEFAULT 0,
        CreatedAt TEXT
    )''')
    # Settings
    c.execute('''CREATE TABLE IF NOT EXISTS HotelSettings (
        Id INTEGER PRIMARY KEY AUTOINCREMENT,
        VATRate REAL DEFAULT 15.0,
        TurnoverTaxThreshold REAL DEFAULT 1000000.0,
        IncomeTaxBrackets TEXT,
        UpdatedAt TEXT
    )''')
    c.execute("SELECT COUNT(*) FROM HotelSettings")
    if c.fetchone()[0] == 0:
        default_brackets = json.dumps([
            {"threshold": 1501, "rate": 0.10},
            {"threshold": 6501, "rate": 0.15},
            {"threshold": 9501, "rate": 0.20},
            {"threshold": 14501, "rate": 0.25},
            {"threshold": 20001, "rate": 0.30},
            {"threshold": 30001, "rate": 0.35},
            {"threshold": 50001, "rate": 0.40},
            {"threshold": 100001, "rate": 0.50}
        ])
        c.execute("""INSERT INTO HotelSettings 
            (VATRate, TurnoverTaxThreshold, IncomeTaxBrackets, UpdatedAt)
            VALUES (?, ?, ?, ?)""",
            (15.0, 1000000.0, default_brackets, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

if not os.path.exists(DB_PATH):
    init_db()
else:
    # ensure tables exist
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='HotelDaily'")
    if not c.fetchone():
        init_db()
    conn.close()

# ============================================================
# HOTEL LOGIC
# ============================================================
def get_hotel_settings():
    conn = get_db()
    df = pd.read_sql("SELECT * FROM HotelSettings LIMIT 1", conn)
    conn.close()
    if df.empty:
        return None
    row = df.iloc[0].to_dict()
    row['IncomeTaxBrackets'] = json.loads(row['IncomeTaxBrackets'])
    return row

def update_hotel_settings(vat_rate, turnover_threshold, brackets_json):
    conn = get_db()
    c = conn.cursor()
    c.execute("""UPDATE HotelSettings SET 
        VATRate=?, TurnoverTaxThreshold=?, IncomeTaxBrackets=?, UpdatedAt=?
        WHERE Id=1""",
        (vat_rate, turnover_threshold, brackets_json, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def calculate_ethiopian_taxes(income, expenses, settings):
    profit = income - expenses
    vat_rate = settings.get('VATRate', 15.0) / 100
    vat = income * vat_rate
    brackets = settings.get('IncomeTaxBrackets', [])
    income_tax = 0
    sorted_brackets = sorted(brackets, key=lambda x: x['threshold'])
    prev_threshold = 0
    for bracket in sorted_brackets:
        threshold = bracket['threshold']
        rate = bracket['rate']
        if profit > prev_threshold:
            taxable = min(profit, threshold) - prev_threshold
            if taxable > 0:
                income_tax += taxable * rate
        prev_threshold = threshold
    if profit > sorted_brackets[-1]['threshold']:
        excess = profit - sorted_brackets[-1]['threshold']
        income_tax += excess * sorted_brackets[-1]['rate']
    total_tax = vat + income_tax
    net_profit = profit - total_tax
    return {
        'profit': profit,
        'vat': vat,
        'income_tax': income_tax,
        'total_tax': total_tax,
        'net_profit': net_profit
    }

def save_daily_data(date, income, expenses):
    settings = get_hotel_settings()
    if not settings:
        return False
    tax = calculate_ethiopian_taxes(income, expenses, settings)
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT Id FROM HotelDaily WHERE Date = ?", (date,))
    existing = c.fetchone()
    if existing:
        c.execute("""UPDATE HotelDaily SET
            Income=?, Expenses=?, Profit=?, VAT=?, IncomeTax=?, TotalTax=?, NetProfit=?, CreatedAt=?
            WHERE Date=?""",
            (income, expenses, tax['profit'], tax['vat'],
             tax['income_tax'], tax['total_tax'],
             tax['net_profit'], datetime.now().strftime("%Y-%m-%d %H:%M:%S"), date))
    else:
        c.execute("""INSERT INTO HotelDaily
            (Date, Income, Expenses, Profit, VAT, IncomeTax, TotalTax, NetProfit, CreatedAt)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (date, income, expenses, tax['profit'], tax['vat'],
             tax['income_tax'], tax['total_tax'],
             tax['net_profit'], datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()
    return True

def get_data(start_date=None, end_date=None):
    conn = get_db()
    query = "SELECT * FROM HotelDaily ORDER BY Date"
    if start_date and end_date:
        query = f"SELECT * FROM HotelDaily WHERE Date >= '{start_date}' AND Date <= '{end_date}' ORDER BY Date"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def get_period_summary(df):
    if df.empty:
        return None
    return {
        'total_income': df['Income'].sum(),
        'total_expenses': df['Expenses'].sum(),
        'total_profit': df['Profit'].sum(),
        'total_tax': df['TotalTax'].sum(),
        'net_profit': df['NetProfit'].sum(),
        'days': len(df),
        'avg_income': df['Income'].mean(),
        'avg_profit': df['Profit'].mean()
    }

def generate_report_df(df, period_label):
    if df.empty:
        return None
    cols = ['Date', 'Income', 'Expenses', 'Profit', 'VAT', 'IncomeTax', 'TotalTax', 'NetProfit']
    report = df[cols].copy()
    summary = get_period_summary(df)
    if summary:
        summary_row = {
            'Date': f'=== {period_label} SUMMARY ===',
            'Income': summary['total_income'],
            'Expenses': summary['total_expenses'],
            'Profit': summary['total_profit'],
            'VAT': summary['total_tax'] * 0.6,
            'IncomeTax': summary['total_tax'] * 0.4,
            'TotalTax': summary['total_tax'],
            'NetProfit': summary['net_profit']
        }
        report = pd.concat([report, pd.DataFrame([summary_row])], ignore_index=True)
    return report

# ============================================================
# PREDICTION & INSIGHTS (AI‑like)
# ============================================================
def predict_future(df, days=7, target='Income'):
    """Simple linear regression for future prediction."""
    if df.empty or len(df) < 3:
        return None, None
    df_sorted = df.sort_values('Date').reset_index(drop=True)
    # Use days since start as X
    X = np.arange(len(df_sorted)).reshape(-1, 1)
    y = df_sorted[target].values
    # Linear regression
    coeffs = np.polyfit(X.flatten(), y, 1)
    slope, intercept = coeffs[0], coeffs[1]
    # Predict next 'days'
    last_x = len(df_sorted) - 1
    future_x = np.arange(last_x + 1, last_x + days + 1)
    predictions = slope * future_x + intercept
    # Ensure non-negative
    predictions = np.maximum(predictions, 0)
    return predictions, (slope, intercept)

def generate_insights(df):
    """Generate recommendations and insights based on data."""
    if df.empty:
        return "No data available for insights."
    summary = get_period_summary(df)
    if not summary:
        return "Insufficient data."
    income = summary['total_income']
    profit = summary['total_profit']
    days = summary['days']
    avg_income = summary['avg_income']
    avg_profit = summary['avg_profit']
    
    insights = []
    # Profitability check
    if profit > 0:
        insights.append(f"✅ Your hotel is profitable: total profit = {format_number(profit)} over {days} days.")
    else:
        insights.append(f"⚠️ You are running at a loss. Total loss = {format_number(abs(profit))} over {days} days.")
    
    # Income trend
    if len(df) >= 2:
        recent_avg = df.tail(7)['Income'].mean() if len(df) >= 7 else df['Income'].mean()
        prev_avg = df.head(7)['Income'].mean() if len(df) >= 7 else df['Income'].mean()
        if recent_avg > prev_avg * 1.05:
            insights.append("📈 Income is increasing recently – good sign!")
        elif recent_avg < prev_avg * 0.95:
            insights.append("📉 Income is declining – consider boosting marketing or improving services.")
        else:
            insights.append("➡️ Income is stable.")
    
    # Recommendations
    if avg_income < 10000:
        insights.append("💡 Suggestion: Increase room rates or offer packages to boost average income.")
    if avg_profit < 1000:
        insights.append("💡 Suggestion: Review expenses – might be overspending on utilities or staff.")
    insights.append("📊 For better performance, track daily occupancy and compare with income.")
    
    return "\n".join(insights)

def format_number(num):
    """Format number with both digits and words to avoid deception."""
    if num is None:
        return "N/A"
    if num >= 1e9:
        return f"{num:,.0f} ({num/1e9:.2f} billion)"
    elif num >= 1e6:
        return f"{num:,.0f} ({num/1e6:.2f} million)"
    elif num >= 1e3:
        return f"{num:,.0f} ({num/1e3:.2f} thousand)"
    else:
        return f"{num:,.0f} ({num:.0f})"

def format_money(val):
    return f"{val:,.0f} ETB"

# ============================================================
# STREAMLIT UI
# ============================================================
st.set_page_config(layout="wide", page_title="🏨 Hotel Internal Management System", page_icon="🏨")

# ---- CUSTOM CSS with animation for 5-star rating ----
st.markdown("""
<style>
@keyframes starGlow {
  0% { text-shadow: 0 0 5px gold; }
  50% { text-shadow: 0 0 20px #FFD700, 0 0 30px #FFA500; }
  100% { text-shadow: 0 0 5px gold; }
}
.star-rating {
  font-size: 3rem;
  color: #FFD700;
  animation: starGlow 2s infinite alternate;
  display: inline-block;
}
.big-title {
  font-size: 4rem;
  font-weight: 900;
  background: linear-gradient(45deg, #b8860b, #FFD700, #b8860b);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  text-shadow: 0 0 30px rgba(184,134,11,0.3);
  text-align: center;
}
.sub-title {
  font-size: 1.5rem;
  color: #1a1a2e;
  text-align: center;
  margin-top: -10px;
}
.big-number {
  font-size: 2.2rem;
  font-weight: 800;
}
.metric-card {
  background: rgba(255,255,255,0.7);
  backdrop-filter: blur(4px);
  border-radius: 15px;
  padding: 15px;
  border: 1px solid #b8860b;
  box-shadow: 0 2px 10px rgba(0,0,0,0.05);
}
.stButton button {
  background: linear-gradient(145deg, #FFD700, #B8860B) !important;
  color: #1a1a2e !important;
  border-radius: 30px !important;
  border: none !important;
  font-weight: bold !important;
  box-shadow: 0 4px 15px rgba(184, 134, 11, 0.3) !important;
  transition: transform 0.2s;
}
.stButton button:hover {
  transform: scale(1.05);
  box-shadow: 0 6px 25px rgba(184, 134, 11, 0.5) !important;
}
</style>
""", unsafe_allow_html=True)

# ---- HEADER with star rating ----
st.markdown("""
<div style="text-align: center;">
  <span class="star-rating">★★★★★</span>
</div>
<h1 class="big-title">Hotel Internal Management System</h1>
<p class="sub-title">Powered by AI • Real‑time Analytics • Ethiopian Tax Engine</p>
<hr style="border: 1px solid #b8860b; width: 50%; margin: auto;"/>
""", unsafe_allow_html=True)

# ---- SIDEBAR (Role & Password) ----
st.sidebar.markdown("### 🏨 Access Control")
role = st.sidebar.radio("Select Role", ["👨‍💼 Hotel Manager", "👔 Hotel Owner"])
if role == "👔 Hotel Owner":
    pwd = st.sidebar.text_input("Enter Owner Password", type="password")
    if pwd != "00000000":
        st.sidebar.error("❌ Incorrect password. Access denied.")
        st.stop()
    else:
        st.sidebar.success("✅ Owner access granted.")
else:
    st.sidebar.info("Manager: only data entry allowed.")

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Refresh Data"):
    st.rerun()

# ---- MAIN CONTENT ----
# Manager or Owner view
if role == "👨‍💼 Hotel Manager":
    st.subheader("📝 Daily Data Entry")
    st.info("Enter today's income and expenses. All taxes are calculated automatically using Ethiopian rules.")

    today = datetime.today().strftime("%Y-%m-%d")
    df_all = get_data()
    today_data = df_all[df_all['Date'] == today] if not df_all.empty else pd.DataFrame()

    col1, col2 = st.columns(2)
    with col1:
        date_input = st.date_input("📅 Date", value=datetime.today())
        date_str = date_input.strftime("%Y-%m-%d")
    with col2:
        if not today_data.empty:
            st.success(f"✅ Data exists for {today}")
            st.write(f"Income: **{format_money(today_data.iloc[0]['Income'])}**")
            st.write(f"Expenses: **{format_money(today_data.iloc[0]['Expenses'])}**")

    col1, col2 = st.columns(2)
    with col1:
        income = st.number_input("💰 Today's Income (ETB)", min_value=0.0, step=1000.0, value=0.0)
    with col2:
        expenses = st.number_input("💸 Today's Expenses (ETB)", min_value=0.0, step=1000.0, value=0.0)

    if income > 0 or expenses > 0:
        settings = get_hotel_settings()
        if settings:
            tax_preview = calculate_ethiopian_taxes(income, expenses, settings)
            st.markdown("---")
            st.markdown("### 📊 Preview")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Profit", f"{format_money(tax_preview['profit'])}", delta="before tax")
            col2.metric("VAT (15%)", f"{format_money(tax_preview['vat'])}")
            col3.metric("Income Tax", f"{format_money(tax_preview['income_tax'])}")
            col4.metric("Net Profit", f"{format_money(tax_preview['net_profit'])}")
            if tax_preview['net_profit'] > 0:
                st.balloons()

    if st.button("💾 Save Today's Data", use_container_width=True, type="primary"):
        if income == 0 and expenses == 0:
            st.warning("⚠️ Please enter income or expenses before saving.")
        else:
            ok = save_daily_data(date_str, income, expenses)
            if ok:
                st.success(f"✅ Data for {date_str} saved successfully!")
                st.rerun()
            else:
                st.error("❌ Failed to save. Check settings.")

    st.markdown("---")
    st.subheader("📋 Recent Entries (Last 7 Days)")
    if not df_all.empty:
        recent = df_all.sort_values('Date', ascending=False).head(7)
        display = recent[['Date', 'Income', 'Expenses', 'Profit', 'NetProfit']].copy()
        display['Income'] = display['Income'].apply(lambda x: format_money(x))
        display['Expenses'] = display['Expenses'].apply(lambda x: format_money(x))
        display['Profit'] = display['Profit'].apply(lambda x: format_money(x))
        display['NetProfit'] = display['NetProfit'].apply(lambda x: format_money(x))
        st.dataframe(display, use_container_width=True)
    else:
        st.info("No data entries yet.")

else:  # OWNER VIEW
    st.subheader("📊 Business Performance Dashboard")
    df = get_data()
    if df.empty:
        st.warning("No hotel data available. The manager needs to enter daily data first.")
        st.stop()

    # ---- Date filter ----
    st.markdown("### 📅 Filter by Date Range")
    col1, col2 = st.columns(2)
    default_start = (datetime.today() - timedelta(days=30)).strftime("%Y-%m-%d")
    default_end = datetime.today().strftime("%Y-%m-%d")
    with col1:
        start_date = st.date_input("From", value=datetime.strptime(default_start, "%Y-%m-%d"))
    with col2:
        end_date = st.date_input("To", value=datetime.strptime(default_end, "%Y-%m-%d"))

    filtered = df[(df['Date'] >= start_date.strftime("%Y-%m-%d")) & (df['Date'] <= end_date.strftime("%Y-%m-%d"))]
    if filtered.empty:
        st.warning("No data in this date range.")
        st.stop()

    # ---- Summary KPIs ----
    summary = get_period_summary(filtered)
    st.markdown("### 📊 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💰 Total Income", format_money(summary['total_income']))
    col2.metric("💸 Total Expenses", format_money(summary['total_expenses']))
    col3.metric("📈 Total Profit", format_money(summary['total_profit']), 
                delta=f"{format_money(summary['avg_profit'])} avg/day")
    col4.metric("🏦 Net Profit (after tax)", format_money(summary['net_profit']))

    # ---- Tax breakdown ----
    st.markdown("### 💰 Tax Summary (Ethiopia)")
    total_tax = filtered['TotalTax'].sum()
    total_vat = filtered['VAT'].sum()
    total_income_tax = filtered['IncomeTax'].sum()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Tax", format_money(total_tax))
    col2.metric("VAT (15%)", format_money(total_vat))
    col3.metric("Income Tax", format_money(total_income_tax))
    col4.metric("Effective Tax Rate", f"{(total_tax / summary['total_income'] * 100):.1f}%")

    # ---- Charts ----
    st.markdown("### 📈 Trends")
    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        chart_data = filtered[['Date', 'Income', 'Expenses']].melt(id_vars=['Date'], var_name='Type', value_name='Amount')
        chart = alt.Chart(chart_data).mark_bar(opacity=0.7).encode(
            x='Date:T', y='Amount:Q', color='Type:N', tooltip=['Date', 'Amount']
        ).properties(height=300)
        st.altair_chart(chart, use_container_width=True)
    with chart_col2:
        profit_chart = alt.Chart(filtered).mark_line(point=True, color='#28a745').encode(
            x='Date:T', y='Profit:Q', tooltip=['Date', 'Profit']
        ).properties(height=300)
        st.altair_chart(profit_chart, use_container_width=True)

    # ---- COMPARISONS ----
    st.markdown("### 📊 Comparisons")
    # Last month (same number of days)
    today_dt = datetime.today()
    last_month_start = (today_dt - timedelta(days=30)).strftime("%Y-%m-%d")
    last_month_end = (today_dt - timedelta(days=1)).strftime("%Y-%m-%d")
    this_month_start = today_dt.replace(day=1).strftime("%Y-%m-%d")
    this_month_end = today_dt.strftime("%Y-%m-%d")
    last_month_data = df[(df['Date'] >= last_month_start) & (df['Date'] <= last_month_end)]
    this_month_data = df[(df['Date'] >= this_month_start) & (df['Date'] <= this_month_end)]
    last_month_sum = get_period_summary(last_month_data) if not last_month_data.empty else None
    this_month_sum = get_period_summary(this_month_data) if not this_month_data.empty else None

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 📆 This Month vs. Last Month")
        if this_month_sum and last_month_sum:
            income_change = this_month_sum['total_income'] - last_month_sum['total_income']
            profit_change = this_month_sum['total_profit'] - last_month_sum['total_profit']
            st.metric("Income change", format_money(income_change), 
                     delta=f"{income_change/last_month_sum['total_income']*100:.1f}%" if last_month_sum['total_income']>0 else "N/A")
            st.metric("Profit change", format_money(profit_change),
                     delta=f"{profit_change/last_month_sum['total_profit']*100:.1f}%" if last_month_sum['total_profit']>0 else "N/A")
        else:
            st.info("Not enough data for month comparison.")

    # Last year (same day range)
    last_year_start = (today_dt - timedelta(days=365)).strftime("%Y-%m-%d")
    last_year_end = (today_dt - timedelta(days=365) + timedelta(days=30)).strftime("%Y-%m-%d")
    last_year_data = df[(df['Date'] >= last_year_start) & (df['Date'] <= last_year_end)]
    last_year_sum = get_period_summary(last_year_data) if not last_year_data.empty else None
    with col2:
        st.markdown("#### 📆 This Year vs. Last Year (same period)")
        if this_month_sum and last_year_sum:
            income_change = this_month_sum['total_income'] - last_year_sum['total_income']
            profit_change = this_month_sum['total_profit'] - last_year_sum['total_profit']
            st.metric("Income change", format_money(income_change),
                     delta=f"{income_change/last_year_sum['total_income']*100:.1f}%" if last_year_sum['total_income']>0 else "N/A")
            st.metric("Profit change", format_money(profit_change),
                     delta=f"{profit_change/last_year_sum['total_profit']*100:.1f}%" if last_year_sum['total_profit']>0 else "N/A")
        else:
            st.info("Not enough data for year comparison.")

    # ---- PREDICTIONS ----
    st.markdown("### 🔮 Future Predictions (Next 7 Days)")
    if len(df) >= 3:
        pred_income, slope_i = predict_future(df, 7, 'Income')
        pred_profit, slope_p = predict_future(df, 7, 'Profit')
        if pred_income is not None:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Projected Income (avg)", format_money(pred_income.mean()))
                st.write(f"Trend: {'📈 increasing' if slope_i > 0 else '📉 decreasing'}")
            with col2:
                st.metric("Projected Profit (avg)", format_money(pred_profit.mean()))
                st.write(f"Trend: {'📈 increasing' if slope_p > 0 else '📉 decreasing'}")
            # Show table of predictions
            future_dates = [(datetime.today() + timedelta(days=i+1)).strftime("%Y-%m-%d") for i in range(7)]
            pred_df = pd.DataFrame({
                'Date': future_dates,
                'Predicted Income': [format_money(x) for x in pred_income],
                'Predicted Profit': [format_money(x) for x in pred_profit]
            })
            st.dataframe(pred_df, use_container_width=True)
        else:
            st.warning("Insufficient data for prediction (need at least 3 days).")
    else:
        st.warning("Need at least 3 days of data for predictions.")

    # ---- AI INSIGHTS & RECOMMENDATIONS ----
    st.markdown("### 💡 AI‑powered Insights & Recommendations")
    insights = generate_insights(filtered)
    st.info(insights)

    # ---- REPORTS DOWNLOAD ----
    st.markdown("### 📄 Download Reports")
    col1, col2, col3, col4 = st.columns(4)
    def download_report(df, period_label):
        report = generate_report_df(df, period_label)
        if report is not None:
            csv = report.to_csv(index=False)
            b64 = base64.b64encode(csv.encode()).decode()
            href = f'<a href="data:text/csv;base64,{b64}" download="{period_label}_Report.csv" style="background:#b8860b;color:white;padding:8px 16px;border-radius:20px;text-decoration:none;">📥 {period_label}</a>'
            return href
        return "No data"
    today_str = datetime.today().strftime("%Y-%m-%d")
    today_data = df[df['Date'] == today_str]
    with col1:
        st.markdown(download_report(today_data, "Daily"), unsafe_allow_html=True)
    week_start = (datetime.today() - timedelta(days=7)).strftime("%Y-%m-%d")
    week_data = df[(df['Date'] >= week_start) & (df['Date'] <= today_str)]
    with col2:
        st.markdown(download_report(week_data, "Weekly"), unsafe_allow_html=True)
    month_start = (datetime.today() - timedelta(days=30)).strftime("%Y-%m-%d")
    month_data = df[(df['Date'] >= month_start) & (df['Date'] <= today_str)]
    with col3:
        st.markdown(download_report(month_data, "Monthly"), unsafe_allow_html=True)
    year_start = (datetime.today() - timedelta(days=365)).strftime("%Y-%m-%d")
    year_data = df[(df['Date'] >= year_start) & (df['Date'] <= today_str)]
    with col4:
        st.markdown(download_report(year_data, "Yearly"), unsafe_allow_html=True)

    # ---- Full data table ----
    st.markdown("### 📋 All Hotel Data")
    display_cols = ['Date', 'Income', 'Expenses', 'Profit', 'VAT', 'IncomeTax', 'TotalTax', 'NetProfit']
    styled = filtered[display_cols].copy()
    for col in ['Income', 'Expenses', 'Profit', 'VAT', 'IncomeTax', 'TotalTax', 'NetProfit']:
        styled[col] = styled[col].apply(lambda x: format_money(x))
    st.dataframe(styled, use_container_width=True)

# ---- FOOTER ----
st.markdown("---")
st.caption("🏨 Hotel Internal Management System v4.0 • All data stored locally • Ethiopian Tax Engine • © 2025")
