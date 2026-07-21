# ============================================================
# ULTIMATE AI DASHBOARD – HOTEL MANAGEMENT + SCHOLARSHIP/JOB
# SKY/SILVER THEME • COLORFUL • ATTRACTIVE
# ============================================================
import streamlit as st
import pandas as pd
import sqlite3
import re
from datetime import datetime, timedelta
import os
import altair as alt
import requests
import json
import base64

# ---------- Local AI (optional) ----------
try:
    from transformers import AutoModelForCausalLM, AutoTokenizer
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

# ---------- CONFIGURATION ----------
USE_LOCAL_AI = True
DB_PATH = "pipeline_vault.db"

# ============================================================
# DATABASE SETUP
# ============================================================
def get_db():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def reset_db():
    conn = get_db()
    c = conn.cursor()
    # Opportunities
    c.execute('''CREATE TABLE IF NOT EXISTS Opportunities (
        Id INTEGER PRIMARY KEY AUTOINCREMENT,
        Title TEXT, Organization TEXT, Category TEXT,
        Deadline TEXT, Status TEXT, CreatedAt TEXT,
        Saved INTEGER DEFAULT 0, UserDescription TEXT, Link TEXT,
        GeneratedCV TEXT, GeneratedCL TEXT, GeneratedML TEXT,
        AppliedTimestamp TEXT, LastNotificationCheck TEXT
    )''')
    # MasterProfile
    c.execute('''CREATE TABLE IF NOT EXISTS MasterProfile (
        Id INTEGER PRIMARY KEY AUTOINCREMENT,
        Name TEXT, Email TEXT, Phone TEXT, Location TEXT,
        Education TEXT, Experience TEXT, Achievements TEXT,
        Skills TEXT, Certifications TEXT,
        NarrativeContext TEXT, NarrativeSolution TEXT, NarrativeCTA TEXT
    )''')
    c.execute("SELECT COUNT(*) FROM MasterProfile")
    if c.fetchone()[0] == 0:
        c.execute("""INSERT INTO MasterProfile
            (Name, Email, Phone, Location, Education, Experience, Achievements, Skills, Certifications,
             NarrativeContext, NarrativeSolution, NarrativeCTA)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""", (
            "ZEDAGIM TESFAYE TANTU", "zedagim100@gmail.com",
            "+251-924-700-390", "Jigjiga, Ethiopia",
            "B.Eng Water Resource & Irrigation Eng. (GPA: 3.87/4.00)",
            "Water resource engineering, irrigation systems, satellite data analysis, climate prediction.",
            "Developed Hydro-Agritech prototypes; Digitized FAO-56; Prevented 456+ trafficking cases.",
            "Python, GIS, Remote Sensing, ML, Data Analysis, Project Management",
            "Certified in GeoAI, Digital Irrigation Systems",
            "Developing regions rely on traditional agriculture without data arrays.",
            "Deploy spaceborne remote sensing and validated Earth Observation data.",
            "I am ready to discuss my potential alignment with your goals."
        ))
    # Hotel tables
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

def ensure_table_schema():
    # Only needed for upgrades; reset_db creates all tables fresh
    pass

# Initialize DB
if not os.path.exists(DB_PATH):
    reset_db()
else:
    # Ensure all tables exist
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='HotelDaily'")
    if not c.fetchone():
        reset_db()
    conn.close()

# ============================================================
# HOTEL BUSINESS LOGIC
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
    """Calculate taxes using Ethiopian rules."""
    profit = income - expenses
    vat_rate = settings.get('VATRate', 15.0) / 100
    vat = income * vat_rate
    
    brackets = settings.get('IncomeTaxBrackets', [])
    income_tax = 0
    remaining_profit = profit
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

def save_daily_hotel_data(date, income, expenses):
    settings = get_hotel_settings()
    if not settings:
        return False
    tax_results = calculate_ethiopian_taxes(income, expenses, settings)
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT Id FROM HotelDaily WHERE Date = ?", (date,))
    existing = c.fetchone()
    if existing:
        c.execute("""UPDATE HotelDaily SET
            Income=?, Expenses=?, Profit=?, VAT=?, IncomeTax=?, TotalTax=?, NetProfit=?, CreatedAt=?
            WHERE Date=?""",
            (income, expenses, tax_results['profit'], tax_results['vat'],
             tax_results['income_tax'], tax_results['total_tax'],
             tax_results['net_profit'], datetime.now().strftime("%Y-%m-%d %H:%M:%S"), date))
    else:
        c.execute("""INSERT INTO HotelDaily
            (Date, Income, Expenses, Profit, VAT, IncomeTax, TotalTax, NetProfit, CreatedAt)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (date, income, expenses, tax_results['profit'], tax_results['vat'],
             tax_results['income_tax'], tax_results['total_tax'],
             tax_results['net_profit'], datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()
    return True

def get_hotel_data(start_date=None, end_date=None):
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
        'avg_profit': df['Profit'].mean() if len(df)>0 else 0
    }

def generate_downloadable_report(df, period_type='Daily'):
    if df.empty:
        return None
    report_cols = ['Date', 'Income', 'Expenses', 'Profit', 'VAT', 'IncomeTax', 'TotalTax', 'NetProfit']
    report_df = df[report_cols].copy()
    summary = get_period_summary(df)
    if summary:
        summary_row = {
            'Date': f'== {period_type} SUMMARY ==',
            'Income': summary['total_income'],
            'Expenses': summary['total_expenses'],
            'Profit': summary['total_profit'],
            'VAT': summary['total_tax'] * 0.6,  # approx
            'IncomeTax': summary['total_tax'] * 0.4,
            'TotalTax': summary['total_tax'],
            'NetProfit': summary['net_profit']
        }
        report_df = pd.concat([report_df, pd.DataFrame([summary_row])], ignore_index=True)
    return report_df

# ============================================================
# SCHOLARSHIP/JOB DB HELPERS (without bs4)
# ============================================================
def fetch_all():
    conn = get_db()
    df = pd.read_sql("SELECT * FROM Opportunities ORDER BY Id DESC", conn)
    conn.close()
    return df

def fetch_profile():
    conn = get_db()
    df = pd.read_sql("SELECT * FROM MasterProfile LIMIT 1", conn)
    conn.close()
    return df

def add_opportunity(data):
    conn = get_db()
    c = conn.cursor()
    c.execute("""INSERT INTO Opportunities
        (Title, Organization, Category, Deadline, Status, CreatedAt, Saved, UserDescription, Link,
         GeneratedCV, GeneratedCL, GeneratedML, AppliedTimestamp, LastNotificationCheck)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
        data["title"], data["organization"], data["category"],
        data["deadline"].strftime("%Y-%m-%d"), data["status"],
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 0,
        data["description"], data["link"],
        "", "", "", "", ""
    ))
    conn.commit()
    conn.close()

def update_generated_docs(opp_id, cv, cl, ml):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE Opportunities SET GeneratedCV=?, GeneratedCL=?, GeneratedML=? WHERE Id=?",
              (cv, cl, ml, opp_id))
    conn.commit()
    conn.close()

def update_status(opp_id, new_status):
    conn = get_db()
    c = conn.cursor()
    applied_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S") if new_status == "Applied" else ""
    c.execute("UPDATE Opportunities SET Status=?, AppliedTimestamp=? WHERE Id=?",
              (new_status, applied_ts, opp_id))
    conn.commit()
    conn.close()

def delete_opportunity(opp_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM Opportunities WHERE Id = ?", (opp_id,))
    conn.commit()
    conn.close()

def extract_keywords(text):
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    stopwords = {"the","and","for","with","from","into","about","without","etc","this","that","have","are"}
    return set(w for w in words if w not in stopwords)

# ---------- URL FETCH WITHOUT BS4 ----------
def extract_description_from_url(url):
    # Fallback: just return a message; no bs4 to avoid errors
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            # Return first 500 chars of raw text (no parsing)
            text = response.text[:500]
            return f"Fetched raw text (first 500 chars):\n{text} ..."
        else:
            return f"Could not fetch: HTTP {response.status_code}"
    except Exception as e:
        return f"Error fetching: {e}"

# ---------- AI Document Generation (simplified) ----------
def generate_cv(profile, description):
    # Simple template (no AI to keep it lightweight)
    matched_ach = [a.strip() for a in profile['Achievements'].split(';') if a.strip()]
    matched_skills = [s.strip() for s in profile['Skills'].split(',') if s.strip()]
    return f"""Name: {profile['Name']}
Email: {profile['Email']}
Phone: {profile['Phone']}
Location: {profile['Location']}

Education:
{profile['Education']}

Experience:
{profile['Experience']}

Achievements (aligned):
{'; '.join(matched_ach[:3])}

Skills (aligned):
{', '.join(matched_skills[:5])}

Certifications:
{profile['Certifications']}"""

def generate_cover_letter(profile, description):
    return f"""Dear Hiring Committee,

I am writing to apply for the position described. My name is {profile['Name']}, and I hold a {profile['Education']}. With a background in {profile['Experience']}, I am confident I can contribute effectively.

My achievements include {profile['Achievements']}, and my skills in {profile['Skills']} are directly relevant.

Thank you for your consideration.

Sincerely,
{profile['Name']}"""

def generate_motivation_letter(profile, description):
    return f"""Dear Selection Committee,

My name is {profile['Name']} from Ethiopia. My journey in water resource engineering and GeoAI has been driven by a desire to solve real-world problems. {profile['NarrativeContext']}

I have developed {profile['Achievements']} and possess skills in {profile['Skills']}. This opportunity would allow me to further my mission of {profile['NarrativeSolution']}.

I look forward to contributing to your program.

Sincerely,
{profile['Name']}"""

# ---------- NOTIFICATIONS ----------
def check_notifications(df):
    today = datetime.today().date()
    urgent = df[pd.to_datetime(df['Deadline']).dt.date <= today + timedelta(days=10)]
    within_24h = df[pd.to_datetime(df['Deadline']).dt.date <= today + timedelta(days=1)]
    msgs = []
    if not urgent.empty:
        msgs.append(f"🔴 {len(urgent)} urgent deadline(s) within 10 days!")
    if not within_24h.empty:
        msgs.append(f"⚠️ {len(within_24h)} deadline(s) within 24 hours!")
    return msgs

# ============================================================
# STREAMLIT UI
# ============================================================
st.set_page_config(layout="wide", page_title="🏨 AI Hotel & Scholarship Dashboard", page_icon="🏨")

# ---- CUSTOM CSS (Sky/Silver + Golden + Colorful) ----
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(145deg, #d4e6f1 0%, #f0f0f0 50%, #e8e8e8 100%);
        color: #1a1a2e;
    }
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp p, .stApp label, .stApp .stMarkdown {
        color: #1a1a2e !important;
    }
    .golden-text {
        color: #b8860b;
        text-shadow: 0 0 8px rgba(184, 134, 11, 0.3);
    }
    .big-number {
        font-size: 2.5rem;
        font-weight: 800;
        color: #1a1a2e;
    }
    .profit-positive { color: #28a745 !important; font-weight: bold; }
    .profit-negative { color: #dc3545 !important; font-weight: bold; }
    .metric-card {
        background: rgba(255,255,255,0.6) !important;
        backdrop-filter: blur(4px);
        border-radius: 15px !important;
        padding: 15px !important;
        border: 1px solid #b8860b !important;
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
    .css-1y4p8pa { background: rgba(255,255,255,0.6) !important; backdrop-filter: blur(4px); border-radius: 15px; }
    .dataframe { border: 1px solid #b8860b !important; border-radius: 10px; background: rgba(255,255,255,0.7); }
    .dataframe th { background: #b8860b !important; color: white !important; }
    .dataframe td { color: #1a1a2e !important; }
    .stAlert { background-color: rgba(184, 134, 11, 0.1) !important; color: #1a1a2e !important; border: 1px solid #b8860b; }
    .sidebar .sidebar-content { background: rgba(255,255,255,0.3) !important; backdrop-filter: blur(4px); }
    .report-link { background: #b8860b; color: white !important; padding: 8px 16px; border-radius: 20px; text-decoration: none; font-weight: bold; }
    .report-link:hover { background: #d4a017; }
</style>
""", unsafe_allow_html=True)

st.title("🏨 Hotel & Scholarship AI Dashboard")
st.markdown("<p class='golden-text' style='font-size:1.2rem;'>Sky/Silver Theme • Colorful • Powered by Local AI</p>", unsafe_allow_html=True)

# ---- TABS ----
tab1, tab2 = st.tabs(["🏨 Hotel Management System", "🎓 Scholarship/Job Dashboard"])

# ============================================================
# TAB 1: HOTEL MANAGEMENT
# ============================================================
with tab1:
    # Fetch data
    hotel_df = get_hotel_data()
    
    # Sidebar for hotel
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🏨 Hotel Dashboard")
    role = st.sidebar.radio(
        "Select Role",
        ["👨‍💼 Hotel Manager", "👔 Hotel Owner"],
        index=0
    )
    if st.sidebar.button("🔄 Refresh Data"):
        st.rerun()
    
    # Tax settings (Owner only)
    settings = get_hotel_settings()
    if role == "👔 Hotel Owner":
        with st.sidebar.expander("⚙️ Tax Rules (Ethiopia)", expanded=False):
            vat_rate = st.number_input("VAT Rate (%)", min_value=0.0, max_value=100.0, value=settings['VATRate'] if settings else 15.0)
            turnover_threshold = st.number_input("Turnover Tax Threshold (ETB)", min_value=0, value=int(settings['TurnoverTaxThreshold']) if settings else 1000000)
            st.markdown("**Income Tax Brackets** (threshold, rate%)")
            brackets = settings['IncomeTaxBrackets'] if settings else []
            new_brackets = []
            for i, bracket in enumerate(brackets):
                col1, col2 = st.columns(2)
                with col1:
                    thresh = st.number_input(f"Threshold {i+1}", min_value=0, value=bracket['threshold'], key=f"thresh_{i}")
                with col2:
                    rate = st.number_input(f"Rate {i+1} (%)", min_value=0.0, max_value=100.0, value=bracket['rate']*100, key=f"rate_{i}") / 100
                new_brackets.append({"threshold": thresh, "rate": rate})
            if st.button("💾 Save Tax Settings"):
                update_hotel_settings(vat_rate, turnover_threshold, json.dumps(new_brackets))
                st.success("✅ Tax settings updated!")
                st.rerun()
    
    # ------------- MANAGER VIEW -------------
    if role == "👨‍💼 Hotel Manager":
        st.subheader("📝 Daily Hotel Data Entry")
        st.info("Enter today's income and expenses. All calculations are automatic.")
        
        today = datetime.today().strftime("%Y-%m-%d")
        today_data = hotel_df[hotel_df['Date'] == today] if not hotel_df.empty else pd.DataFrame()
        
        col1, col2 = st.columns(2)
        with col1:
            date_input = st.date_input("📅 Date", value=datetime.today())
            date_str = date_input.strftime("%Y-%m-%d")
        with col2:
            if not today_data.empty:
                st.success(f"✅ Data exists for {today}")
                st.write(f"Income: **{today_data.iloc[0]['Income']:,.0f} ETB**")
                st.write(f"Expenses: **{today_data.iloc[0]['Expenses']:,.0f} ETB**")
        
        col1, col2 = st.columns(2)
        with col1:
            income = st.number_input("💰 Today's Income (ETB)", min_value=0.0, step=1000.0, value=0.0)
        with col2:
            expenses = st.number_input("💸 Today's Expenses (ETB)", min_value=0.0, step=1000.0, value=0.0)
        
        # Preview
        if income > 0 or expenses > 0:
            settings = get_hotel_settings()
            if settings:
                tax_preview = calculate_ethiopian_taxes(income, expenses, settings)
                st.markdown("---")
                st.markdown("### 📊 Preview")
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Profit", f"{tax_preview['profit']:,.0f} ETB", delta="before tax")
                col2.metric("VAT (15%)", f"{tax_preview['vat']:,.0f} ETB")
                col3.metric("Income Tax", f"{tax_preview['income_tax']:,.0f} ETB")
                col4.metric("Net Profit", f"{tax_preview['net_profit']:,.0f} ETB")
                if tax_preview['net_profit'] > 0:
                    st.balloons()
        
        if st.button("💾 Save Today's Data", use_container_width=True, type="primary"):
            if income == 0 and expenses == 0:
                st.warning("⚠️ Please enter income or expenses before saving.")
            else:
                success = save_daily_hotel_data(date_str, income, expenses)
                if success:
                    st.success(f"✅ Data for {date_str} saved successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to save data. Check settings.")
        
        # Recent entries
        st.markdown("---")
        st.subheader("📋 Recent Entries (Last 7 Days)")
        if not hotel_df.empty:
            recent = hotel_df.sort_values('Date', ascending=False).head(7)
            display_cols = ['Date', 'Income', 'Expenses', 'Profit', 'NetProfit']
            st.dataframe(recent[display_cols].style.format({
                'Income': '{:,.0f}',
                'Expenses': '{:,.0f}',
                'Profit': '{:,.0f}',
                'NetProfit': '{:,.0f}'
            }), use_container_width=True)
        else:
            st.info("No data entries yet. Start by saving today's data.")
    
    # ------------- OWNER VIEW -------------
    else:
        st.subheader("📊 Business Performance Dashboard")
        hotel_df = get_hotel_data()
        if hotel_df.empty:
            st.warning("No hotel data available. The manager needs to enter daily data first.")
        else:
            # Date filter
            st.markdown("### 📅 Filter by Date Range")
            col1, col2 = st.columns(2)
            default_start = (datetime.today() - timedelta(days=30)).strftime("%Y-%m-%d")
            default_end = datetime.today().strftime("%Y-%m-%d")
            with col1:
                start_date = st.date_input("From", value=datetime.strptime(default_start, "%Y-%m-%d"))
            with col2:
                end_date = st.date_input("To", value=datetime.strptime(default_end, "%Y-%m-%d"))
            
            filtered_df = hotel_df[
                (hotel_df['Date'] >= start_date.strftime("%Y-%m-%d")) &
                (hotel_df['Date'] <= end_date.strftime("%Y-%m-%d"))
            ]
            if filtered_df.empty:
                st.warning("No data in this date range.")
            else:
                summary = get_period_summary(filtered_df)
                # KPI cards with color
                st.markdown("### 📊 Key Metrics")
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("💰 Total Income", f"{summary['total_income']:,.0f} ETB")
                col2.metric("💸 Total Expenses", f"{summary['total_expenses']:,.0f} ETB")
                profit_delta = f"{summary['avg_profit']:,.0f} avg/day"
                col3.metric("📈 Total Profit", f"{summary['total_profit']:,.0f} ETB", delta=profit_delta)
                col4.metric("🏦 Net Profit (after tax)", f"{summary['net_profit']:,.0f} ETB")
                
                # Tax summary
                st.markdown("### 💰 Tax Summary (Ethiopia)")
                total_tax = filtered_df['TotalTax'].sum()
                total_vat = filtered_df['VAT'].sum()
                total_income_tax = filtered_df['IncomeTax'].sum()
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Total Tax", f"{total_tax:,.0f} ETB")
                col2.metric("VAT (15%)", f"{total_vat:,.0f} ETB")
                col3.metric("Income Tax", f"{total_income_tax:,.0f} ETB")
                col4.metric("Effective Tax Rate", f"{(total_tax / summary['total_income'] * 100):.1f}%")
                
                # Charts
                st.markdown("### 📈 Trends")
                chart_col1, chart_col2 = st.columns(2)
                with chart_col1:
                    chart_data = filtered_df[['Date', 'Income', 'Expenses']].melt(id_vars=['Date'], var_name='Type', value_name='Amount')
                    chart = alt.Chart(chart_data).mark_bar(opacity=0.7).encode(
                        x='Date:T',
                        y='Amount:Q',
                        color='Type:N',
                        tooltip=['Date', 'Amount']
                    ).properties(height=300)
                    st.altair_chart(chart, use_container_width=True)
                with chart_col2:
                    profit_chart = alt.Chart(filtered_df).mark_line(point=True, color='#28a745').encode(
                        x='Date:T',
                        y='Profit:Q',
                        tooltip=['Date', 'Profit']
                    ).properties(height=300)
                    st.altair_chart(profit_chart, use_container_width=True)
                
                # Reports
                st.markdown("### 📄 Download Reports")
                col1, col2, col3, col4 = st.columns(4)
                
                def create_report_download(df, period, label):
                    report_df = generate_downloadable_report(df, period)
                    if report_df is not None:
                        csv = report_df.to_csv(index=False)
                        b64 = base64.b64encode(csv.encode()).decode()
                        href = f'<a href="data:text/csv;base64,{b64}" download="{period}_Report.csv" class="report-link">📥 {label}</a>'
                        return href
                    return "No data"
                
                today_str = datetime.today().strftime("%Y-%m-%d")
                today_data = hotel_df[hotel_df['Date'] == today_str]
                with col1:
                    st.markdown(create_report_download(today_data, "Daily", "Daily Report"), unsafe_allow_html=True)
                week_start = (datetime.today() - timedelta(days=7)).strftime("%Y-%m-%d")
                week_data = hotel_df[(hotel_df['Date'] >= week_start) & (hotel_df['Date'] <= today_str)]
                with col2:
                    st.markdown(create_report_download(week_data, "Weekly", "Weekly Report"), unsafe_allow_html=True)
                month_start = (datetime.today() - timedelta(days=30)).strftime("%Y-%m-%d")
                month_data = hotel_df[(hotel_df['Date'] >= month_start) & (hotel_df['Date'] <= today_str)]
                with col3:
                    st.markdown(create_report_download(month_data, "Monthly", "Monthly Report"), unsafe_allow_html=True)
                year_start = (datetime.today() - timedelta(days=365)).strftime("%Y-%m-%d")
                year_data = hotel_df[(hotel_df['Date'] >= year_start) & (hotel_df['Date'] <= today_str)]
                with col4:
                    st.markdown(create_report_download(year_data, "Yearly", "Yearly Report"), unsafe_allow_html=True)
                
                # All data table
                st.markdown("### 📋 All Hotel Data")
                display_cols = ['Date', 'Income', 'Expenses', 'Profit', 'VAT', 'IncomeTax', 'TotalTax', 'NetProfit']
                st.dataframe(filtered_df[display_cols].style.format({
                    'Income': '{:,.0f}',
                    'Expenses': '{:,.0f}',
                    'Profit': '{:,.0f}',
                    'VAT': '{:,.0f}',
                    'IncomeTax': '{:,.0f}',
                    'TotalTax': '{:,.0f}',
                    'NetProfit': '{:,.0f}'
                }), use_container_width=True)

# ============================================================
# TAB 2: SCHOLARSHIP/JOB DASHBOARD (simplified, no bs4)
# ============================================================
with tab2:
    st.subheader("🎓 Scholarship & Job Application Tracker")
    df_all = fetch_all()
    
    # Sidebar notification button
    if st.sidebar.button("🔔 Check Notifications"):
        if not df_all.empty:
            msgs = check_notifications(df_all)
            if msgs:
                for msg in msgs:
                    st.sidebar.warning(msg)
            else:
                st.sidebar.success("✅ All deadlines under control!")
        else:
            st.sidebar.info("No opportunities.")
    
    # Metrics
    if not df_all.empty:
        total = len(df_all)
        applied = len(df_all[df_all['Status'] == 'Applied'])
        pending = len(df_all[df_all['Status'] == 'Not Applied'])
        urgent_count = len(df_all[pd.to_datetime(df_all['Deadline']) <= datetime.today() + timedelta(days=10)])
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📌 Total", total)
        col2.metric("✅ Applied", applied)
        col3.metric("⏳ Pending", pending)
        col4.metric("🔴 Urgent", urgent_count)
    
    # Table
    if df_all.empty:
        st.info("No opportunities yet. Add one below.")
    else:
        st.dataframe(df_all[["Id", "Title", "Organization", "Deadline", "Status"]], use_container_width=True)
        selected_id = st.selectbox("Select Opportunity ID", df_all["Id"].tolist())
        if selected_id:
            row = df_all[df_all["Id"] == selected_id].iloc[0]
            profile_df = fetch_profile()
            if not profile_df.empty:
                profile = profile_df.iloc[0].to_dict()
                with st.expander(f"📄 {row['Title']} – {row['Organization']}", expanded=True):
                    st.write(f"**Deadline:** {row['Deadline']}")
                    st.write(f"**Status:** {row['Status']}")
                    st.write(f"**Link:** {row['Link']}")
                    description = st.text_area("Job Description (paste or edit)", value=row["UserDescription"] or "", height=150)
                    
                    col_gen, col_status, col_del = st.columns(3)
                    with col_gen:
                        if st.button("⚡ Generate Documents (AI)"):
                            cv = generate_cv(profile, description)
                            cl = generate_cover_letter(profile, description)
                            ml = generate_motivation_letter(profile, description)
                            update_generated_docs(selected_id, cv, cl, ml)
                            st.success("✅ Generated and saved!")
                            st.rerun()
                    with col_status:
                        if st.button("✅ Mark as Applied"):
                            update_status(selected_id, "Applied")
                            st.rerun()
                    with col_del:
                        if st.button("🗑️ Delete"):
                            delete_opportunity(selected_id)
                            st.rerun()
                    
                    if row['GeneratedCV']:
                        st.subheader("📄 CV")
                        st.text_area("CV", row['GeneratedCV'], height=200)
                        st.download_button("⬇️ Download CV", data=row['GeneratedCV'], file_name=f"CV_{row['Title']}.txt")
                    if row['GeneratedCL']:
                        st.subheader("✉️ Cover Letter")
                        st.text_area("Cover Letter", row['GeneratedCL'], height=200)
                        st.download_button("⬇️ Download Cover Letter", data=row['GeneratedCL'], file_name=f"CL_{row['Title']}.txt")
                    if row['GeneratedML']:
                        st.subheader("📨 Motivation Letter")
                        st.text_area("Motivation Letter", row['GeneratedML'], height=200)
                        st.download_button("⬇️ Download Motivation Letter", data=row['GeneratedML'], file_name=f"ML_{row['Title']}.txt")
    
    # Add new
    with st.expander("➕ Add New Opportunity", expanded=False):
        with st.form("add_form"):
            title = st.text_input("Title *")
            org = st.text_input("Organization *")
            cat = st.selectbox("Category", ["Scholarship", "Job", "Fellowship"])
            deadline = st.date_input("Deadline", value=datetime.today().date() + timedelta(days=30))
            link = st.text_input("Link (optional)")
            desc = st.text_area("Description", height=100)
            if st.form_submit_button("Add Opportunity"):
                if title and org:
                    add_opportunity({
                        "title": title, "organization": org, "category": cat,
                        "deadline": deadline, "status": "Not Applied",
                        "description": desc, "link": link
                    })
                    st.success("✅ Added!")
                    st.rerun()
                else:
                    st.warning("Title and Organization required.")

# ---- FOOTER ----
st.markdown("---")
st.caption("⚡ Data stored in SQLite (pipeline_vault.db) | Beautiful Sky/Silver Theme | 🏨 Hotel Management System v3.0")
