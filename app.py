# ============================================================
# HOTEL INTERNAL MANAGEMENT SYSTEM
# Developed by Zedagim Tesfaye (Eng)
# Sky/Silver Theme • Simple • Powerful • Transparent
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
PASSWORD = "00000000"  # Owner password

# ============================================================
# DATABASE SETUP
# ============================================================
def get_db():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_db()
    c = conn.cursor()
    # Transactions table – each line item
    c.execute('''CREATE TABLE IF NOT EXISTS Transactions (
        Id INTEGER PRIMARY KEY AUTOINCREMENT,
        Date TEXT NOT NULL,
        Type TEXT CHECK(Type IN ('Income','Expense')) NOT NULL,
        Category TEXT NOT NULL,
        Description TEXT,
        Amount REAL NOT NULL,
        CreatedAt TEXT
    )''')
    # Daily summaries – computed from transactions
    c.execute('''CREATE TABLE IF NOT EXISTS DailySummaries (
        Date TEXT PRIMARY KEY,
        TotalIncome REAL DEFAULT 0,
        TotalExpenses REAL DEFAULT 0,
        Profit REAL DEFAULT 0,
        VAT REAL DEFAULT 0,
        IncomeTax REAL DEFAULT 0,
        TotalTax REAL DEFAULT 0,
        NetProfit REAL DEFAULT 0,
        UpdatedAt TEXT
    )''')
    # Settings (tax rules)
    c.execute('''CREATE TABLE IF NOT EXISTS HotelSettings (
        Id INTEGER PRIMARY KEY AUTOINCREMENT,
        VATRate REAL DEFAULT 15.0,
        TurnoverTaxThreshold REAL DEFAULT 1000000.0,
        IncomeTaxBrackets TEXT,
        UpdatedAt TEXT
    )''')
    # Insert default settings if empty
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
    # Ensure tables exist
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Transactions'")
    if not c.fetchone():
        init_db()
    conn.close()

# ============================================================
# HELPER FUNCTIONS
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

def add_transaction(date, ttype, category, description, amount):
    """Insert a single transaction."""
    conn = get_db()
    c = conn.cursor()
    c.execute("""INSERT INTO Transactions (Date, Type, Category, Description, Amount, CreatedAt)
                 VALUES (?, ?, ?, ?, ?, ?)""",
              (date, ttype, category, description, amount, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()
    # After adding, we need to recompute daily summary for that date
    recompute_daily_summary(date)

def recompute_daily_summary(date):
    """Aggregate all transactions for a given date, compute taxes, update DailySummaries."""
    conn = get_db()
    df = pd.read_sql("SELECT Type, Amount FROM Transactions WHERE Date = ?", conn, params=(date,))
    conn.close()
    if df.empty:
        # No transactions – set zeros
        total_income = 0.0
        total_expenses = 0.0
    else:
        total_income = df[df['Type']=='Income']['Amount'].sum()
        total_expenses = df[df['Type']=='Expense']['Amount'].sum()
    profit = total_income - total_expenses
    settings = get_hotel_settings()
    if settings:
        tax = calculate_ethiopian_taxes(total_income, total_expenses, settings)
        vat = tax['vat']
        income_tax = tax['income_tax']
        total_tax = tax['total_tax']
        net_profit = tax['net_profit']
    else:
        vat = income_tax = total_tax = net_profit = 0.0

    conn = get_db()
    c = conn.cursor()
    c.execute("""INSERT OR REPLACE INTO DailySummaries 
        (Date, TotalIncome, TotalExpenses, Profit, VAT, IncomeTax, TotalTax, NetProfit, UpdatedAt)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (date, total_income, total_expenses, profit, vat, income_tax, total_tax, net_profit,
         datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def get_transactions(start_date=None, end_date=None):
    conn = get_db()
    query = "SELECT * FROM Transactions ORDER BY Date DESC, Id DESC"
    if start_date and end_date:
        query = f"SELECT * FROM Transactions WHERE Date >= '{start_date}' AND Date <= '{end_date}' ORDER BY Date DESC, Id DESC"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def get_daily_summaries(start_date=None, end_date=None):
    conn = get_db()
    query = "SELECT * FROM DailySummaries ORDER BY Date"
    if start_date and end_date:
        query = f"SELECT * FROM DailySummaries WHERE Date >= '{start_date}' AND Date <= '{end_date}' ORDER BY Date"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def get_period_summary(df):
    if df.empty:
        return None
    return {
        'total_income': df['TotalIncome'].sum(),
        'total_expenses': df['TotalExpenses'].sum(),
        'total_profit': df['Profit'].sum(),
        'total_tax': df['TotalTax'].sum(),
        'net_profit': df['NetProfit'].sum(),
        'days': len(df),
        'avg_income': df['TotalIncome'].mean(),
        'avg_profit': df['Profit'].mean()
    }

def format_money(val):
    if val is None:
        return "0 ETB"
    return f"{val:,.0f} ETB"

def format_number(val):
    """Human-friendly number with words."""
    if val is None:
        return "N/A"
    if abs(val) >= 1e6:
        return f"{val:,.0f} ({val/1e6:.2f} million)"
    elif abs(val) >= 1e3:
        return f"{val:,.0f} ({val/1e3:.2f} thousand)"
    else:
        return f"{val:,.0f}"

# ---- Prediction (linear regression) ----
def predict_future(df, days=7, target='TotalIncome'):
    if df.empty or len(df) < 3:
        return None, None
    df_sorted = df.sort_values('Date').reset_index(drop=True)
    X = np.arange(len(df_sorted)).reshape(-1, 1)
    y = df_sorted[target].values
    coeffs = np.polyfit(X.flatten(), y, 1)
    slope, intercept = coeffs[0], coeffs[1]
    last_x = len(df_sorted) - 1
    future_x = np.arange(last_x + 1, last_x + days + 1)
    predictions = slope * future_x + intercept
    predictions = np.maximum(predictions, 0)
    return predictions, slope

# ---- Insights (rule-based) ----
def generate_insights(df):
    if df.empty:
        return "No data available for insights."
    summary = get_period_summary(df)
    if not summary:
        return "Insufficient data."
    total_income = summary['total_income']
    total_profit = summary['total_profit']
    days = summary['days']
    avg_income = summary['avg_income']
    avg_profit = summary['avg_profit']
    insights = []
    if total_profit > 0:
        insights.append(f"✅ Your hotel is profitable: total profit = {format_money(total_profit)} over {days} days.")
    else:
        insights.append(f"⚠️ You are running at a loss. Total loss = {format_money(abs(total_profit))} over {days} days.")
    if len(df) >= 2:
        recent_income = df.tail(7)['TotalIncome'].mean() if len(df)>=7 else df['TotalIncome'].mean()
        prev_income = df.head(7)['TotalIncome'].mean() if len(df)>=7 else df['TotalIncome'].mean()
        if recent_income > prev_income * 1.05:
            insights.append("📈 Income is increasing – good sign.")
        elif recent_income < prev_income * 0.95:
            insights.append("📉 Income is declining – consider boosting marketing or improving services.")
        else:
            insights.append("➡️ Income is stable.")
    # Category-specific insights (from transactions)
    conn = get_db()
    # Get transactions for the period to analyze categories
    start = df['Date'].min() if not df.empty else None
    end = df['Date'].max() if not df.empty else None
    if start and end:
        trans = get_transactions(start, end)
        if not trans.empty:
            expense_cats = trans[trans['Type']=='Expense'].groupby('Category')['Amount'].sum()
            if not expense_cats.empty:
                top_exp = expense_cats.idxmax()
                insights.append(f"🔍 Top expense category: {top_exp} – consider reviewing this cost.")
    return "\n".join(insights) if insights else "No significant insights."

# ---- Generate report CSV ----
def generate_report_df(df, period_label):
    if df.empty:
        return None
    cols = ['Date', 'TotalIncome', 'TotalExpenses', 'Profit', 'VAT', 'IncomeTax', 'TotalTax', 'NetProfit']
    report = df[cols].copy()
    summary = get_period_summary(df)
    if summary:
        summary_row = {
            'Date': f'=== {period_label} SUMMARY ===',
            'TotalIncome': summary['total_income'],
            'TotalExpenses': summary['total_expenses'],
            'Profit': summary['total_profit'],
            'VAT': summary['total_tax'] * 0.6,
            'IncomeTax': summary['total_tax'] * 0.4,
            'TotalTax': summary['total_tax'],
            'NetProfit': summary['net_profit']
        }
        report = pd.concat([report, pd.DataFrame([summary_row])], ignore_index=True)
    return report

# ============================================================
# STREAMLIT UI
# ============================================================
st.set_page_config(layout="wide", page_title="🏨 Hotel Internal Management System", page_icon="🏨")

# Custom CSS (star rating, big title)
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
  font-size: 1.3rem;
  color: #1a1a2e;
  text-align: center;
  margin-top: -5px;
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

# ---- HEADER ----
st.markdown("""
<div style="text-align: center;">
  <span class="star-rating">★★★★★</span>
</div>
<h1 class="big-title">Hotel Internal Management System</h1>
<p class="sub-title">Developed by Zedagim Tesfaye (Eng) • Simple • Transparent • Powerful</p>
<hr style="border: 1px solid #b8860b; width: 60%; margin: auto;"/>
<br>
""", unsafe_allow_html=True)

# ---- SIDEBAR (Access Control) ----
st.sidebar.markdown("### 🔑 Access")
role = st.sidebar.radio("Select Role", ["👨‍💼 Hotel Manager", "👔 Hotel Owner"])
if role == "👔 Hotel Owner":
    pwd = st.sidebar.text_input("Enter Owner Password", type="password")
    if pwd != PASSWORD:
        st.sidebar.error("❌ Incorrect password.")
        st.stop()
    else:
        st.sidebar.success("✅ Full access granted.")
else:
    st.sidebar.info("Manager: add daily transactions.")

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Refresh Data"):
    st.rerun()

# ============================================================
# MANAGER VIEW
# ============================================================
if role == "👨‍💼 Hotel Manager":
    st.subheader("📝 Add Income / Expense Entry")
    st.markdown("Enter each transaction separately with category and description.")
    
    col1, col2 = st.columns(2)
    with col1:
        date_input = st.date_input("📅 Date", value=datetime.today())
        date_str = date_input.strftime("%Y-%m-%d")
    with col2:
        ttype = st.selectbox("Type", ["Income", "Expense"])
    
    # Predefined categories
    income_cats = ["Room Revenue", "Food & Beverage", "Conference/Hall", "Other Income"]
    expense_cats = ["Salaries", "Utilities", "Maintenance", "Food Supplies", "Marketing", "Taxes", "Other Expenses"]
    if ttype == "Income":
        categories = income_cats
    else:
        categories = expense_cats
    
    category = st.selectbox("Category", categories)
    description = st.text_input("Description (optional)")
    amount = st.number_input("Amount (ETB)", min_value=0.0, step=100.0, value=0.0)
    
    if st.button("➕ Add Transaction", use_container_width=True):
        if amount <= 0:
            st.warning("Please enter a positive amount.")
        else:
            add_transaction(date_str, ttype, category, description, amount)
            st.success(f"✅ {ttype} of {format_money(amount)} added for {date_str}")
            st.rerun()
    
    st.markdown("---")
    st.subheader("📋 Recent Transactions")
    trans_df = get_transactions()
    if not trans_df.empty:
        # Show last 20
        st.dataframe(trans_df.head(20)[['Date', 'Type', 'Category', 'Description', 'Amount']], use_container_width=True)
    else:
        st.info("No transactions yet.")

# ============================================================
# OWNER VIEW
# ============================================================
else:
    st.subheader("📊 Business Performance Dashboard")
    # Get daily summaries
    df = get_daily_summaries()
    if df.empty:
        st.warning("No data available. The manager needs to add transactions first.")
        st.stop()
    
    # Date filter
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
    
    # Summary KPIs
    summary = get_period_summary(filtered)
    st.markdown("### 📊 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💰 Total Income", format_money(summary['total_income']))
    col2.metric("💸 Total Expenses", format_money(summary['total_expenses']))
    col3.metric("📈 Total Profit", format_money(summary['total_profit']), delta=f"{format_money(summary['avg_profit'])} avg/day")
    col4.metric("🏦 Net Profit (after tax)", format_money(summary['net_profit']))
    
    # Tax breakdown
    st.markdown("### 💰 Tax Summary (Ethiopia)")
    total_tax = filtered['TotalTax'].sum()
    total_vat = filtered['VAT'].sum()
    total_income_tax = filtered['IncomeTax'].sum()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Tax", format_money(total_tax))
    col2.metric("VAT (15%)", format_money(total_vat))
    col3.metric("Income Tax", format_money(total_income_tax))
    col4.metric("Effective Tax Rate", f"{(total_tax / summary['total_income'] * 100):.1f}%" if summary['total_income']>0 else "0%")
    
    # Category breakdown chart (using transactions data)
    st.markdown("### 📊 Income & Expenses by Category")
    # Get transactions for the period
    trans = get_transactions(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
    if not trans.empty:
        # Prepare data for stacked bar chart: group by Type and Category
        cat_data = trans.groupby(['Type', 'Category'])['Amount'].sum().reset_index()
        if not cat_data.empty:
            # Create a bar chart
            chart = alt.Chart(cat_data).mark_bar().encode(
                x=alt.X('Category:N', title='Category'),
                y=alt.Y('Amount:Q', title='Amount (ETB)'),
                color='Type:N',
                tooltip=['Category', 'Type', 'Amount']
            ).properties(height=300, width=600)
            st.altair_chart(chart, use_container_width=True)
    
    # Trends (Income vs Expenses over time)
    st.markdown("### 📈 Income & Expenses Trend")
    chart_data = filtered[['Date', 'TotalIncome', 'TotalExpenses']].melt(id_vars=['Date'], var_name='Metric', value_name='Amount')
    trend_chart = alt.Chart(chart_data).mark_line(point=True, strokeWidth=3).encode(
        x='Date:T',
        y='Amount:Q',
        color='Metric:N',
        tooltip=['Date', 'Metric', 'Amount']
    ).properties(height=300)
    st.altair_chart(trend_chart, use_container_width=True)
    
    # Profit trend
    st.markdown("### 📈 Profit Trend")
    profit_chart = alt.Chart(filtered).mark_line(point=True, color='#28a745', strokeWidth=3).encode(
        x='Date:T',
        y='Profit:Q',
        tooltip=['Date', 'Profit']
    ).properties(height=300)
    st.altair_chart(profit_chart, use_container_width=True)
    
    # Comparisons
    st.markdown("### 📊 Comparisons")
    today_dt = datetime.today()
    # Last month vs this month
    last_month_start = (today_dt - timedelta(days=30)).strftime("%Y-%m-%d")
    last_month_end = (today_dt - timedelta(days=1)).strftime("%Y-%m-%d")
    this_month_start = today_dt.replace(day=1).strftime("%Y-%m-%d")
    this_month_end = today_dt.strftime("%Y-%m-%d")
    last_month_df = df[(df['Date'] >= last_month_start) & (df['Date'] <= last_month_end)]
    this_month_df = df[(df['Date'] >= this_month_start) & (df['Date'] <= this_month_end)]
    last_month_sum = get_period_summary(last_month_df) if not last_month_df.empty else None
    this_month_sum = get_period_summary(this_month_df) if not this_month_df.empty else None
    
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
            st.info("Not enough data.")
    
    # Last year same period
    last_year_start = (today_dt - timedelta(days=365)).strftime("%Y-%m-%d")
    last_year_end = (today_dt - timedelta(days=365) + timedelta(days=30)).strftime("%Y-%m-%d")
    last_year_df = df[(df['Date'] >= last_year_start) & (df['Date'] <= last_year_end)]
    last_year_sum = get_period_summary(last_year_df) if not last_year_df.empty else None
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
            st.info("Not enough data.")
    
    # Predictions
    st.markdown("### 🔮 Future Predictions (Next 7 Days)")
    if len(df) >= 3:
        pred_income, slope_i = predict_future(df, 7, 'TotalIncome')
        pred_profit, slope_p = predict_future(df, 7, 'Profit')
        if pred_income is not None:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Projected Income (avg)", format_money(pred_income.mean()))
                st.write(f"Trend: {'📈 increasing' if slope_i > 0 else '📉 decreasing'}")
            with col2:
                st.metric("Projected Profit (avg)", format_money(pred_profit.mean()))
                st.write(f"Trend: {'📈 increasing' if slope_p > 0 else '📉 decreasing'}")
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
    
    # Insights
    st.markdown("### 💡 Insights & Recommendations")
    insights = generate_insights(filtered)
    st.info(insights)
    
    # Reports
    st.markdown("### 📄 Download Reports")
    col1, col2, col3, col4 = st.columns(4)
    def download_report(df, label):
        report = generate_report_df(df, label)
        if report is not None:
            csv = report.to_csv(index=False)
            b64 = base64.b64encode(csv.encode()).decode()
            href = f'<a href="data:text/csv;base64,{b64}" download="{label}_Report.csv" style="background:#b8860b;color:white;padding:8px 16px;border-radius:20px;text-decoration:none;font-weight:bold;">📥 {label}</a>'
            return href
        return "No data"
    today_str = datetime.today().strftime("%Y-%m-%d")
    today_df = df[df['Date'] == today_str]
    with col1:
        st.markdown(download_report(today_df, "Daily"), unsafe_allow_html=True)
    week_start = (datetime.today() - timedelta(days=7)).strftime("%Y-%m-%d")
    week_df = df[(df['Date'] >= week_start) & (df['Date'] <= today_str)]
    with col2:
        st.markdown(download_report(week_df, "Weekly"), unsafe_allow_html=True)
    month_start = (datetime.today() - timedelta(days=30)).strftime("%Y-%m-%d")
    month_df = df[(df['Date'] >= month_start) & (df['Date'] <= today_str)]
    with col3:
        st.markdown(download_report(month_df, "Monthly"), unsafe_allow_html=True)
    year_start = (datetime.today() - timedelta(days=365)).strftime("%Y-%m-%d")
    year_df = df[(df['Date'] >= year_start) & (df['Date'] <= today_str)]
    with col4:
        st.markdown(download_report(year_df, "Yearly"), unsafe_allow_html=True)
    
    # Full data table
    st.markdown("### 📋 Daily Summary Data")
    display_cols = ['Date', 'TotalIncome', 'TotalExpenses', 'Profit', 'VAT', 'IncomeTax', 'TotalTax', 'NetProfit']
    styled = filtered[display_cols].copy()
    for col in ['TotalIncome', 'TotalExpenses', 'Profit', 'VAT', 'IncomeTax', 'TotalTax', 'NetProfit']:
        styled[col] = styled[col].apply(lambda x: format_money(x))
    st.dataframe(styled, use_container_width=True)
    
    # Option to view all transactions
    with st.expander("📋 View All Transactions (Raw Data)"):
        all_trans = get_transactions(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
        if not all_trans.empty:
            st.dataframe(all_trans[['Date', 'Type', 'Category', 'Description', 'Amount']], use_container_width=True)
        else:
            st.info("No transactions in this period.")

# ---- FOOTER ----
st.markdown("---")
st.caption("🏨 Hotel Internal Management System • Developed by Zedagim Tesfaye (Eng) • All data stored locally • © 2025")
