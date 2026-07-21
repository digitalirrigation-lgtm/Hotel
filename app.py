# ============================================================
# HOTEL INTERNAL MANAGEMENT SYSTEM
# Developed by Zedagim Tesfaye (Eng)
# Multi‑lingual: English, Amharic, Somali, Oromo
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
# TRANSLATIONS
# ============================================================
TRANSLATIONS = {
    'en': {
        # General
        'app_title': 'Hotel Internal Management System',
        'app_subtitle': 'Developed by Zedagim Tesfaye (Eng) • Simple • Transparent • Powerful',
        'footer': '🏨 Hotel Internal Management System • Developed by Zedagim Tesfaye (Eng) • All data stored locally • © 2025',
        # Sidebar
        'access': '🔑 Access',
        'select_role': 'Select Role',
        'role_manager': '👨‍💼 Hotel Manager',
        'role_owner': '👔 Hotel Owner',
        'owner_password': 'Enter Owner Password',
        'incorrect_password': '❌ Incorrect password.',
        'access_granted': '✅ Full access granted.',
        'manager_info': 'Manager: add daily transactions.',
        'refresh_data': '🔄 Refresh Data',
        'language': '🌐 Language',
        # Manager
        'add_entry': '📝 Add Income / Expense Entry',
        'enter_each': 'Enter each transaction separately with category and description.',
        'date': '📅 Date',
        'type': 'Type',
        'income': 'Income',
        'expense': 'Expense',
        'category': 'Category',
        'description': 'Description (optional)',
        'amount': 'Amount (ETB)',
        'add_transaction': '➕ Add Transaction',
        'enter_positive': 'Please enter a positive amount.',
        'added_success': '✅ {ttype} of {amount} added for {date}',
        'recent_transactions': '📋 Recent Transactions',
        'no_transactions': 'No transactions yet.',
        # Owner
        'dashboard': '📊 Business Performance Dashboard',
        'no_data': 'No data available. The manager needs to add transactions first.',
        'date_filter': '📅 Filter by Date Range',
        'from': 'From',
        'to': 'To',
        'key_metrics': '📊 Key Metrics',
        'total_income': '💰 Total Income',
        'total_expenses': '💸 Total Expenses',
        'total_profit': '📈 Total Profit',
        'net_profit': '🏦 Net Profit (after tax)',
        'tax_summary': '💰 Tax Summary (Ethiopia)',
        'total_tax': 'Total Tax',
        'vat': 'VAT (15%)',
        'income_tax': 'Income Tax',
        'effective_rate': 'Effective Tax Rate',
        'category_breakdown': '📊 Income & Expenses by Category',
        'income_expense_trend': '📈 Income & Expenses Trend',
        'profit_trend': '📈 Profit Trend',
        'comparisons': '📊 Comparisons',
        'this_month_vs_last': '📆 This Month vs. Last Month',
        'income_change': 'Income change',
        'profit_change': 'Profit change',
        'this_year_vs_last': '📆 This Year vs. Last Year (same period)',
        'future_predictions': '🔮 Future Predictions (Next 7 Days)',
        'projected_income_avg': 'Projected Income (avg)',
        'trend_increasing': '📈 increasing',
        'trend_decreasing': '📉 decreasing',
        'projected_profit_avg': 'Projected Profit (avg)',
        'insights': '💡 Insights & Recommendations',
        'download_reports': '📄 Download Reports',
        'daily': 'Daily',
        'weekly': 'Weekly',
        'monthly': 'Monthly',
        'yearly': 'Yearly',
        'daily_summary_data': '📋 Daily Summary Data',
        'view_transactions': '📋 View All Transactions (Raw Data)',
        'no_transactions_period': 'No transactions in this period.',
        'insufficient_data': 'Not enough data.',
        'need_3_days': 'Need at least 3 days of data for predictions.',
        'no_data_insights': 'No data available for insights.',
        # Insights messages
        'profitable': '✅ Your hotel is profitable: total profit = {profit} over {days} days.',
        'loss': '⚠️ You are running at a loss. Total loss = {loss} over {days} days.',
        'income_increasing': '📈 Income is increasing – good sign.',
        'income_declining': '📉 Income is declining – consider boosting marketing or improving services.',
        'income_stable': '➡️ Income is stable.',
        'top_expense': '🔍 Top expense category: {cat} – consider reviewing this cost.',
        'no_significant': 'No significant insights.',
        # Reports
        'report_summary': '=== {period} SUMMARY ===',
        # Buttons
        'save_settings': '💾 Save Tax Settings',
        'edit_tax_rules': '⚙️ Tax Rules (Ethiopia)',
        'vat_rate': 'VAT Rate (%)',
        'turnover_threshold': 'Turnover Tax Threshold (ETB)',
        'income_tax_brackets': 'Income Tax Brackets (threshold, rate%)',
        'threshold': 'Threshold',
        'rate': 'Rate',
        # Categories
        'room_revenue': 'Room Revenue',
        'food_beverage': 'Food & Beverage',
        'conference_hall': 'Conference/Hall',
        'other_income': 'Other Income',
        'salaries': 'Salaries',
        'utilities': 'Utilities',
        'maintenance': 'Maintenance',
        'food_supplies': 'Food Supplies',
        'marketing': 'Marketing',
        'taxes': 'Taxes',
        'other_expenses': 'Other Expenses',
    },
    'am': {  # Amharic (Google Translate approximate)
        'app_title': 'የሆቴል ውስጥ አስተዳደር ስርዓት',
        'app_subtitle': 'በዘዳግም ተስፋዬ (ኢንጂነር) የተዘጋጀ • ቀላል • ግልጽ • ኃይለኛ',
        'footer': '🏨 የሆቴል ውስጥ አስተዳደር ስርዓት • በዘዳግም ተስፋዬ (ኢንጂነር) • መረጃ በአካባቢው ተከማችቷል • © 2025',
        'access': '🔑 መዳረሻ',
        'select_role': 'ሚና ይምረጡ',
        'role_manager': '👨‍💼 የሆቴል ሥራ አስኪያጅ',
        'role_owner': '👔 የሆቴል ባለቤት',
        'owner_password': 'የባለቤት የይለፍ ቃል ያስገቡ',
        'incorrect_password': '❌ የይለፍ ቃሉ ተሳስቷል።',
        'access_granted': '✅ ሙሉ መዳረሻ ተሰጥቷል።',
        'manager_info': 'ሥራ አስኪያጅ: ዕለታዊ ግብይቶችን ያክሉ።',
        'refresh_data': '🔄 መረጃ አድስ',
        'language': '🌐 ቋንቋ',
        'add_entry': '📝 ገቢ / ወጪ ግቤት ያክሉ',
        'enter_each': 'እያንዳንዱን ግብይት በምድብ እና መግለጫ በተናጠል ያስገቡ።',
        'date': '📅 ቀን',
        'type': 'ዓይነት',
        'income': 'ገቢ',
        'expense': 'ወጪ',
        'category': 'ምድብ',
        'description': 'መግለጫ (አማራጭ)',
        'amount': 'መጠን (ETB)',
        'add_transaction': '➕ ግብይት ያክሉ',
        'enter_positive': 'እባክዎ አዎንታዊ መጠን ያስገቡ።',
        'added_success': '✅ {ttype} የ {amount} ለ {date} ተጨምሯል',
        'recent_transactions': '📋 የቅርብ ጊዜ ግብይቶች',
        'no_transactions': 'እስካሁን ግብይቶች የሉም።',
        'dashboard': '📊 የንግድ አፈጻጸም ዳሽቦርድ',
        'no_data': 'ምንም መረጃ የለም። ሥራ አስኪያጁ መጀመሪያ ግብይቶችን ማከል አለበት።',
        'date_filter': '📅 በቀን ክልል አጣሩ',
        'from': 'ከ',
        'to': 'እስከ',
        'key_metrics': '📊 ቁልፍ መለኪያዎች',
        'total_income': '💰 ጠቅላላ ገቢ',
        'total_expenses': '💸 ጠቅላላ ወጪ',
        'total_profit': '📈 ጠቅላላ ትርፍ',
        'net_profit': '🏦 የተጣራ ትርፍ (ከታክስ በኋላ)',
        'tax_summary': '💰 የታክስ ማጠቃለያ (ኢትዮጵያ)',
        'total_tax': 'ጠቅላላ ታክስ',
        'vat': 'ቫት (15%)',
        'income_tax': 'የገቢ ግብር',
        'effective_rate': 'ውጤታማ የታክስ መጠን',
        'category_breakdown': '📊 በምድብ የተከፋፈለ ገቢ እና ወጪ',
        'income_expense_trend': '📈 የገቢ እና የወጪ አዝማሚያ',
        'profit_trend': '📈 የትርፍ አዝማሚያ',
        'comparisons': '📊 ንፅፅር',
        'this_month_vs_last': '📆 የዚህ ወር እና ያለፈው ወር',
        'income_change': 'የገቢ ለውጥ',
        'profit_change': 'የትርፍ ለውጥ',
        'this_year_vs_last': '📆 የዚህ ዓመት እና ያለፈው ዓመት (ተመሳሳይ ጊዜ)',
        'future_predictions': '🔮 የወደፊት ትንበያ (ቀጣይ 7 ቀናት)',
        'projected_income_avg': 'የተተነበየ ገቢ (አማካይ)',
        'trend_increasing': '📈 እየጨመረ',
        'trend_decreasing': '📉 እየቀነሰ',
        'projected_profit_avg': 'የተተነበየ ትርፍ (አማካይ)',
        'insights': '💡 ግንዛቤዎች እና ምክሮች',
        'download_reports': '📄 ሪፖርቶችን አውርድ',
        'daily': 'ዕለታዊ',
        'weekly': 'ሳምንታዊ',
        'monthly': 'ወርሃዊ',
        'yearly': 'አመታዊ',
        'daily_summary_data': '📋 ዕለታዊ ማጠቃለያ መረጃ',
        'view_transactions': '📋 ሁሉንም ግብይቶች ይመልከቱ (ጥሬ መረጃ)',
        'no_transactions_period': 'በዚህ ጊዜ ውስጥ ምንም ግብይቶች የሉም።',
        'insufficient_data': 'በቂ መረጃ የለም።',
        'need_3_days': 'ለትንበያ ቢያንስ 3 ቀናት መረጃ ያስፈልጋል።',
        'no_data_insights': 'ለግንዛቤዎች ምንም መረጃ የለም።',
        'profitable': '✅ ሆቴልዎ ትርፋማ ነው: ጠቅላላ ትርፍ = {profit} በ {days} ቀናት።',
        'loss': '⚠️ ኪሳራ እያስከተሉ ነው። ጠቅላላ ኪሳራ = {loss} በ {days} ቀናት።',
        'income_increasing': '📈 ገቢ እየጨመረ ነው – ጥሩ ምልክት።',
        'income_declining': '📉 ገቢ እየቀነሰ ነው – ግብይት ማስተዋወቅ ወይም አገልግሎቶችን ማሻሻል ያስቡ።',
        'income_stable': '➡️ ገቢ የተረጋጋ ነው።',
        'top_expense': '🔍 ከፍተኛ የወጪ ምድብ: {cat} – ይህን ወጪ መገምገም ያስቡ።',
        'no_significant': 'ምንም ጉልህ ግንዛቤዎች የሉም።',
        'report_summary': '=== {period} ማጠቃለያ ===',
        'save_settings': '💾 የታክስ ቅንብሮችን አስቀምጥ',
        'edit_tax_rules': '⚙️ የታክስ ህጎች (ኢትዮጵያ)',
        'vat_rate': 'የቫት መጠን (%)',
        'turnover_threshold': 'የሽያጭ ግብር ገደብ (ETB)',
        'income_tax_brackets': 'የገቢ ግብር ደረጃዎች (ገደብ, መቶኛ)',
        'threshold': 'ገደብ',
        'rate': 'መጠን',
        'room_revenue': 'የክፍል ገቢ',
        'food_beverage': 'ምግብ እና መጠጥ',
        'conference_hall': 'ኮንፈረንስ/አዳራሽ',
        'other_income': 'ሌላ ገቢ',
        'salaries': 'ደሞዝ',
        'utilities': 'መገልገያዎች',
        'maintenance': 'ጥገና',
        'food_supplies': 'የምግብ አቅርቦቶች',
        'marketing': 'ግብይት',
        'taxes': 'ታክሶች',
        'other_expenses': 'ሌላ ወጪ',
    },
    'so': {  # Somali (approximate)
        'app_title': 'Nidaamka Maamulka Gudaha ee Hoteelka',
        'app_subtitle': 'Waxaa diyaariyay Zedagim Tesfaye (Eng) • Fudud • Hufan • Awood leh',
        'footer': '🏨 Nidaamka Maamulka Gudaha ee Hoteelka • Waxaa diyaariyay Zedagim Tesfaye (Eng) • Xogta gudaha lagu kaydiyaa • © 2025',
        'access': '🔑 Gelitaan',
        'select_role': 'Dooro Doorka',
        'role_manager': '👨‍💼 Maamulaha Hoteelka',
        'role_owner': '👔 Mulkiilaha Hoteelka',
        'owner_password': 'Geli Furaha Sirta ee Mulkiilaha',
        'incorrect_password': '❌ Furaha sirta waa qalad.',
        'access_granted': '✅ Gelitaan buuxa ayaa la siiyay.',
        'manager_info': 'Maamulaha: ku dar macaamillada maalinlaha ah.',
        'refresh_data': '🔄 Cusboonaysii Xogta',
        'language': '🌐 Luqadda',
        'add_entry': '📝 Ku Dar Dakhli / Kharash',
        'enter_each': 'Ku dar macaamil kasta si gooni ah oo leh qayb iyo sharaxaad.',
        'date': '📅 Taariikh',
        'type': 'Nooca',
        'income': 'Dakhli',
        'expense': 'Kharash',
        'category': 'Qayb',
        'description': 'Sharaxaad (ikhtiyaari)',
        'amount': 'Qaddar (ETB)',
        'add_transaction': '➕ Ku Dar Macaamil',
        'enter_positive': 'Fadlan geli qaddar togan.',
        'added_success': '✅ {ttype} ee {amount} waxaa lagu daray {date}',
        'recent_transactions': '📋 Macaamillada dhawaa',
        'no_transactions': 'Weli macaamil ma jiraan.',
        'dashboard': '📊 Dashboard-ka Waxqabadka Ganacsiga',
        'no_data': 'Xog ma jirto. Maamuluhu waa inuu marka hore ku daro macaamillada.',
        'date_filter': '📅 Ku Shaandhee Taariikhda',
        'from': 'Laga bilaabo',
        'to': 'Ilaa',
        'key_metrics': '📊 Cabirrada Muhiimka ah',
        'total_income': '💰 Wadarta Dakhliga',
        'total_expenses': '💸 Wadarta Kharashka',
        'total_profit': '📈 Wadarta Faaiidada',
        'net_profit': '🏦 Faaiidada Saafiga ah (kadib canshuurta)',
        'tax_summary': '💰 Soo Koobida Canshuurta (Itoobiya)',
        'total_tax': 'Wadarta Canshuurta',
        'vat': 'VAT (15%)',
        'income_tax': 'Canshuurta Dakhliga',
        'effective_rate': 'Heerka Canshuurta Wax Ku Oolka ah',
        'category_breakdown': '📊 Dakhli iyo Kharash Qayb ahaan',
        'income_expense_trend': '📈 Isbeddelka Dakhliga iyo Kharashka',
        'profit_trend': '📈 Isbeddelka Faaiidada',
        'comparisons': '📊 Isbarbardhig',
        'this_month_vs_last': '📆 Bishan vs. Bishii Hore',
        'income_change': 'Isbeddelka Dakhliga',
        'profit_change': 'Isbeddelka Faaiidada',
        'this_year_vs_last': '📆 Sanadkan vs. Sanadkii Hore (isla muddo)',
        'future_predictions': '🔮 Saadaasha Mustaqbalka (7 maalmood oo soo socda)',
        'projected_income_avg': 'Dakhliga la Saadaaliyay (celcelis)',
        'trend_increasing': '📈 kor u kacaya',
        'trend_decreasing': '📉 hoos u dhacaya',
        'projected_profit_avg': 'Faaiidada la Saadaaliyay (celcelis)',
        'insights': '💡 Faham iyo Talooyin',
        'download_reports': '📄 Soo Deji Warbixinno',
        'daily': 'Maalinle',
        'weekly': 'Toddobaadle',
        'monthly': 'Biloodle',
        'yearly': 'Sanadle',
        'daily_summary_data': '📋 Xogta Soo Koobida Maalinlaha ah',
        'view_transactions': '📋 Eeg Dhammaan Macaamillada (Xog Cayriin)',
        'no_transactions_period': 'Muddaan macaamil ma jiraan.',
        'insufficient_data': 'Xog ku filan ma jirto.',
        'need_3_days': 'U baahan tahay ugu yaraan 3 maalmood oo xog ah si saadaasha loo sameeyo.',
        'no_data_insights': 'Ma jirto xog loo helo faham.',
        'profitable': '✅ Hoteelkaagu waa faaiido leh: wadarta faaiidada = {profit} ee {days} maalmood.',
        'loss': '⚠️ Waxaad khasaare ku jirtaa. Wadarta khasaaraha = {loss} ee {days} maalmood.',
        'income_increasing': '📈 Dakhligu wuu korodhayaa – calaamad wanaagsan.',
        'income_declining': '📉 Dakhligu wuu hoos u dhacayaa – ka fikir suuqgeynta ama horumarinta adeegyada.',
        'income_stable': '➡️ Dakhligu waa deggan yahay.',
        'top_expense': '🔍 Qaybta ugu sarreysa ee kharashka: {cat} – ka fikir dib u eegista kharashkan.',
        'no_significant': 'Ma jiraan faham muhiim ah.',
        'report_summary': '=== {period} SOO KOOBID ===',
        'save_settings': '💾 Kaydi Dejinta Canshuurta',
        'edit_tax_rules': '⚙️ Xeerarka Canshuurta (Itoobiya)',
        'vat_rate': 'Heerka VAT (%)',
        'turnover_threshold': 'Xadka Canshuurta Wareegga (ETB)',
        'income_tax_brackets': 'Heerarka Canshuurta Dakhliga (xad, boqolkiiba)',
        'threshold': 'Xad',
        'rate': 'Heer',
        'room_revenue': 'Dakhliga Qolalka',
        'food_beverage': 'Cunto & Cabitaan',
        'conference_hall': 'Shir / Hool',
        'other_income': 'Dakhli Kale',
        'salaries': 'Mushaar',
        'utilities': 'Adeegyada',
        'maintenance': 'Dayactir',
        'food_supplies': 'Alaabta Cuntada',
        'marketing': 'Suuqgeyn',
        'taxes': 'Canshuuro',
        'other_expenses': 'Kharashyo Kale',
    },
    'om': {  # Oromo (approximate)
        'app_title': 'Sistimii Bulchiinsa Keessaa Hoteelaa',
        'app_subtitle': 'Zedagim Tesfaye (Eng) kan qopheesse • Salpha • Ifa • Cimaa',
        'footer': '🏨 Sistimii Bulchiinsa Keessaa Hoteelaa • Zedagim Tesfaye (Eng) • Dhaanni naannoo keessatti ku kufa • © 2025',
        'access': '🔑 Galii',
        'select_role': 'Filannoo gaalee',
        'role_manager': '👨‍💼 Bulchaa Hoteelaa',
        'role_owner': '👔 Abbaa Hoteelaa',
        'owner_password': 'Jecha iccitii abbaa hoteelaa galchi',
        'incorrect_password': '❌ Jecha iccitii dogoggoraa.',
        'access_granted': '✅ Galii guutuu kennameera.',
        'manager_info': 'Bulchaa: galmeessa guyyaa guyyaa dabali.',
        'refresh_data': '🔄 Dhaata haaromsi',
        'language': '🌐 Afaan',
        'add_entry': '📝 Galii / Baasii dabali',
        'enter_each': 'Galmeessa tokko tokkoo qabatamaan fi ibsa wajjin galchi.',
        'date': '📅 Guyyaa',
        'type': 'Gosa',
        'income': 'Galii',
        'expense': 'Baasii',
        'category': 'Qabataa',
        'description': 'Ibsa (filannoo)',
        'amount': 'Baay\'ina (ETB)',
        'add_transaction': '➕ Galmeessa dabali',
        'enter_positive': 'Maaloo baay\'ina tola galchi.',
        'added_success': '✅ {ttype} baay\'ina {amount} guyyaa {date}tti dabale',
        'recent_transactions': '📋 Galmeessa dhiyoo',
        'no_transactions': 'Hanga ammaatti galmeessii hin jiru.',
        'dashboard': '📊 Daashboordii Fooyya\'insa Daldalaa',
        'no_data': 'Dhaatni hin jiru. Bulchaan dura galmeessii dabaluu qaba.',
        'date_filter': '📅 Guyyaa filachuuf',
        'from': 'Eegaluu',
        'to': 'Hanga',
        'key_metrics': '📊 Safarriwwan ijoo',
        'total_income': '💰 Galii waliigala',
        'total_expenses': '💸 Baasii waliigala',
        'total_profit': '📈 Bu\'aa waliigala',
        'net_profit': '🏦 Bu\'aa qulqulluu (qarxii booda)',
        'tax_summary': '💰 Qabxii qarxii (Itoophiyaa)',
        'total_tax': 'Qarxii waliigala',
        'vat': 'VAT (15%)',
        'income_tax': 'Qarxii galii',
        'effective_rate': 'Haala qarxiinii',
        'category_breakdown': '📊 Galii fi baasii qabatamaan',
        'income_expense_trend': '📈 Haalli galii fi baasii',
        'profit_trend': '📈 Haalli bu\'aa',
        'comparisons': '📊 Walitti mirkaneessa',
        'this_month_vs_last': '📆 Ji\'a kana vs. Ji\'a darbe',
        'income_change': 'Jijjiirriin galii',
        'profit_change': 'Jijjiirriin bu\'aa',
        'this_year_vs_last': '📆 Waggaa kana vs. Waggaa darbe (yeroo walfakkaatu)',
        'future_predictions': '🔮 Raajii fuuturaa (Guyyaa 7 itti aanu)',
        'projected_income_avg': 'Galii raajii (giddugaleessa)',
        'trend_increasing': '📈 dabalaa jira',
        'trend_decreasing': '📉 hir\'achaa jira',
        'projected_profit_avg': 'Bu\'aa raajii (giddugaleessa)',
        'insights': '💡 Hubachiisa fi gorsa',
        'download_reports': '📄 Gabatee buusi',
        'daily': 'Guyyaa',
        'weekly': 'Torbee',
        'monthly': 'Ji\'aa',
        'yearly': 'Waggaa',
        'daily_summary_data': '📋 Dhaatni gabaabaa guyyaa',
        'view_transactions': '📋 Galmeessii hunda ilaali (dhaata raw)',
        'no_transactions_period': 'Yeroo kana keessatti galmeessii hin jiru.',
        'insufficient_data': 'Dhaatni ga\'aan hin jiru.',
        'need_3_days': 'Raajii godhuf guyyaa 3 ta\'uu qaba.',
        'no_data_insights': 'Hubachiisaaf dhaatni hin jiru.',
        'profitable': '✅ Hoteelaan keessan bu\'aa qaba: bu\'aan waliigala = {profit} guyyaa {days} keessatti.',
        'loss': '⚠️ Hooggansa irra jirtu. Hooggansi waliigala = {loss} guyyaa {days} keessatti.',
        'income_increasing': '📈 Galii dabalaa jira – mallattoo gaarii.',
        'income_declining': '📉 Galii hir\'achaa jira – yaada gurgurtaa fooyyessuu ykn tajaajila fooyyessuu.',
        'income_stable': '➡️ Galii sirriidha.',
        'top_expense': '🔍 Qabataa baasii ol’aanaa: {cat} – baasii kana miiressuu yaadi.',
        'no_significant': 'Hubachiisa guddaan hin jiru.',
        'report_summary': '=== {period} GABAAABA ===',
        'save_settings': '💾 Qarxii qindeessaa olkaa\'i',
        'edit_tax_rules': '⚙️ Seera qarxii (Itoophiyaa)',
        'vat_rate': 'Haala VAT (%)',
        'turnover_threshold': 'Daangaa qarxii gurgurtaa (ETB)',
        'income_tax_brackets': 'Sadarkaa qarxii galii (daangaa, haala)',
        'threshold': 'Daangaa',
        'rate': 'Haala',
        'room_revenue': 'Galii huccuu',
        'food_beverage': 'Nyaata fi dhugaatii',
        'conference_hall': 'Konfiraansii / Halluu',
        'other_income': 'Galii biraa',
        'salaries': 'Mindaa',
        'utilities': 'Tajaajila',
        'maintenance': 'Toojjanna',
        'food_supplies': 'Qarqara nyaataa',
        'marketing': 'Gurgurtaa',
        'taxes': 'Qarxii',
        'other_expenses': 'Baasii biraa',
    }
}

# ============================================================
# DATABASE SETUP (unchanged)
# ============================================================
def get_db():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS Transactions (
        Id INTEGER PRIMARY KEY AUTOINCREMENT,
        Date TEXT NOT NULL,
        Type TEXT CHECK(Type IN ('Income','Expense')) NOT NULL,
        Category TEXT NOT NULL,
        Description TEXT,
        Amount REAL NOT NULL,
        CreatedAt TEXT
    )''')
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
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Transactions'")
    if not c.fetchone():
        init_db()
    conn.close()

# ============================================================
# HELPERS (unchanged)
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
    conn = get_db()
    c = conn.cursor()
    c.execute("""INSERT INTO Transactions (Date, Type, Category, Description, Amount, CreatedAt)
                 VALUES (?, ?, ?, ?, ?, ?)""",
              (date, ttype, category, description, amount, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()
    recompute_daily_summary(date)

def recompute_daily_summary(date):
    conn = get_db()
    df = pd.read_sql("SELECT Type, Amount FROM Transactions WHERE Date = ?", conn, params=(date,))
    conn.close()
    if df.empty:
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
    if val is None:
        return "N/A"
    if abs(val) >= 1e6:
        return f"{val:,.0f} ({val/1e6:.2f} million)"
    elif abs(val) >= 1e3:
        return f"{val:,.0f} ({val/1e3:.2f} thousand)"
    else:
        return f"{val:,.0f}"

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

def generate_insights(df, lang='en'):
    t = TRANSLATIONS[lang]
    if df.empty:
        return t['no_data_insights']
    summary = get_period_summary(df)
    if not summary:
        return t['insufficient_data']
    total_income = summary['total_income']
    total_profit = summary['total_profit']
    days = summary['days']
    avg_income = summary['avg_income']
    avg_profit = summary['avg_profit']
    insights = []
    if total_profit > 0:
        insights.append(t['profitable'].format(profit=format_money(total_profit), days=days))
    else:
        insights.append(t['loss'].format(loss=format_money(abs(total_profit)), days=days))
    if len(df) >= 2:
        recent_income = df.tail(7)['TotalIncome'].mean() if len(df)>=7 else df['TotalIncome'].mean()
        prev_income = df.head(7)['TotalIncome'].mean() if len(df)>=7 else df['TotalIncome'].mean()
        if recent_income > prev_income * 1.05:
            insights.append(t['income_increasing'])
        elif recent_income < prev_income * 0.95:
            insights.append(t['income_declining'])
        else:
            insights.append(t['income_stable'])
    # Category expense insight
    conn = get_db()
    start = df['Date'].min() if not df.empty else None
    end = df['Date'].max() if not df.empty else None
    if start and end:
        trans = get_transactions(start, end)
        if not trans.empty:
            expense_cats = trans[trans['Type']=='Expense'].groupby('Category')['Amount'].sum()
            if not expense_cats.empty:
                top_exp = expense_cats.idxmax()
                insights.append(t['top_expense'].format(cat=top_exp))
    return "\n".join(insights) if insights else t['no_significant']

def generate_report_df(df, period_label, lang='en'):
    if df.empty:
        return None
    cols = ['Date', 'TotalIncome', 'TotalExpenses', 'Profit', 'VAT', 'IncomeTax', 'TotalTax', 'NetProfit']
    report = df[cols].copy()
    summary = get_period_summary(df)
    if summary:
        t = TRANSLATIONS[lang]
        summary_row = {
            'Date': t['report_summary'].format(period=period_label),
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

# ---- Language selection ----
if 'lang' not in st.session_state:
    st.session_state['lang'] = 'en'
lang = st.sidebar.selectbox(
    "🌐 Language",
    options=['en', 'am', 'so', 'om'],
    format_func=lambda x: {'en':'English', 'am':'አማርኛ', 'so':'Somali', 'om':'Oromo'}[x],
    index=['en','am','so','om'].index(st.session_state['lang'])
)
st.session_state['lang'] = lang
t = TRANSLATIONS[lang]

# ---- Custom CSS (unchanged) ----
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
st.markdown(f"""
<div style="text-align: center;">
  <span class="star-rating">★★★★★</span>
</div>
<h1 class="big-title">{t['app_title']}</h1>
<p class="sub-title">{t['app_subtitle']}</p>
<hr style="border: 1px solid #b8860b; width: 60%; margin: auto;"/>
<br>
""", unsafe_allow_html=True)

# ---- SIDEBAR (Access Control) ----
st.sidebar.markdown(f"### {t['access']}")
role = st.sidebar.radio(t['select_role'], [t['role_manager'], t['role_owner']])
if role == t['role_owner']:
    pwd = st.sidebar.text_input(t['owner_password'], type="password")
    if pwd != PASSWORD:
        st.sidebar.error(t['incorrect_password'])
        st.stop()
    else:
        st.sidebar.success(t['access_granted'])
else:
    st.sidebar.info(t['manager_info'])

st.sidebar.markdown("---")
if st.sidebar.button(t['refresh_data']):
    st.rerun()

# ---- MANAGER VIEW ----
if role == t['role_manager']:
    st.subheader(t['add_entry'])
    st.markdown(t['enter_each'])
    
    col1, col2 = st.columns(2)
    with col1:
        date_input = st.date_input(t['date'], value=datetime.today())
        date_str = date_input.strftime("%Y-%m-%d")
    with col2:
        ttype = st.selectbox(t['type'], [t['income'], t['expense']])
        # we need to map selected ttype to DB value
        ttype_db = 'Income' if ttype == t['income'] else 'Expense'
    
    # Categories
    if ttype == t['income']:
        categories = [t['room_revenue'], t['food_beverage'], t['conference_hall'], t['other_income']]
    else:
        categories = [t['salaries'], t['utilities'], t['maintenance'], t['food_supplies'], t['marketing'], t['taxes'], t['other_expenses']]
    # Store category in original English for DB
    cat_mapping = {
        t['room_revenue']: 'Room Revenue',
        t['food_beverage']: 'Food & Beverage',
        t['conference_hall']: 'Conference/Hall',
        t['other_income']: 'Other Income',
        t['salaries']: 'Salaries',
        t['utilities']: 'Utilities',
        t['maintenance']: 'Maintenance',
        t['food_supplies']: 'Food Supplies',
        t['marketing']: 'Marketing',
        t['taxes']: 'Taxes',
        t['other_expenses']: 'Other Expenses',
    }
    category_display = st.selectbox(t['category'], categories)
    category_db = cat_mapping.get(category_display, category_display)
    description = st.text_input(t['description'])
    amount = st.number_input(t['amount'], min_value=0.0, step=100.0, value=0.0)
    
    if st.button(t['add_transaction'], use_container_width=True):
        if amount <= 0:
            st.warning(t['enter_positive'])
        else:
            add_transaction(date_str, ttype_db, category_db, description, amount)
            st.success(t['added_success'].format(ttype=ttype, amount=format_money(amount), date=date_str))
            st.rerun()
    
    st.markdown("---")
    st.subheader(t['recent_transactions'])
    trans_df = get_transactions()
    if not trans_df.empty:
        st.dataframe(trans_df.head(20)[['Date', 'Type', 'Category', 'Description', 'Amount']], use_container_width=True)
    else:
        st.info(t['no_transactions'])

# ---- OWNER VIEW ----
else:
    st.subheader(t['dashboard'])
    df = get_daily_summaries()
    if df.empty:
        st.warning(t['no_data'])
        st.stop()
    
    st.markdown(f"### {t['date_filter']}")
    col1, col2 = st.columns(2)
    default_start = (datetime.today() - timedelta(days=30)).strftime("%Y-%m-%d")
    default_end = datetime.today().strftime("%Y-%m-%d")
    with col1:
        start_date = st.date_input(t['from'], value=datetime.strptime(default_start, "%Y-%m-%d"))
    with col2:
        end_date = st.date_input(t['to'], value=datetime.strptime(default_end, "%Y-%m-%d"))
    
    filtered = df[(df['Date'] >= start_date.strftime("%Y-%m-%d")) & (df['Date'] <= end_date.strftime("%Y-%m-%d"))]
    if filtered.empty:
        st.warning("No data in this date range.")
        st.stop()
    
    summary = get_period_summary(filtered)
    st.markdown(f"### {t['key_metrics']}")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(t['total_income'], format_money(summary['total_income']))
    col2.metric(t['total_expenses'], format_money(summary['total_expenses']))
    col3.metric(t['total_profit'], format_money(summary['total_profit']), delta=f"{format_money(summary['avg_profit'])} avg/day")
    col4.metric(t['net_profit'], format_money(summary['net_profit']))
    
    st.markdown(f"### {t['tax_summary']}")
    total_tax = filtered['TotalTax'].sum()
    total_vat = filtered['VAT'].sum()
    total_income_tax = filtered['IncomeTax'].sum()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(t['total_tax'], format_money(total_tax))
    col2.metric(t['vat'], format_money(total_vat))
    col3.metric(t['income_tax'], format_money(total_income_tax))
    col4.metric(t['effective_rate'], f"{(total_tax / summary['total_income'] * 100):.1f}%" if summary['total_income']>0 else "0%")
    
    # Category breakdown
    st.markdown(f"### {t['category_breakdown']}")
    trans = get_transactions(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
    if not trans.empty:
        cat_data = trans.groupby(['Type', 'Category'])['Amount'].sum().reset_index()
        if not cat_data.empty:
            chart = alt.Chart(cat_data).mark_bar().encode(
                x=alt.X('Category:N', title='Category'),
                y=alt.Y('Amount:Q', title='Amount (ETB)'),
                color='Type:N',
                tooltip=['Category', 'Type', 'Amount']
            ).properties(height=300, width=600)
            st.altair_chart(chart, use_container_width=True)
    
    # Trends
    st.markdown(f"### {t['income_expense_trend']}")
    chart_data = filtered[['Date', 'TotalIncome', 'TotalExpenses']].melt(id_vars=['Date'], var_name='Metric', value_name='Amount')
    trend_chart = alt.Chart(chart_data).mark_line(point=True, strokeWidth=3).encode(
        x='Date:T',
        y='Amount:Q',
        color='Metric:N',
        tooltip=['Date', 'Metric', 'Amount']
    ).properties(height=300)
    st.altair_chart(trend_chart, use_container_width=True)
    
    st.markdown(f"### {t['profit_trend']}")
    profit_chart = alt.Chart(filtered).mark_line(point=True, color='#28a745', strokeWidth=3).encode(
        x='Date:T',
        y='Profit:Q',
        tooltip=['Date', 'Profit']
    ).properties(height=300)
    st.altair_chart(profit_chart, use_container_width=True)
    
    # Comparisons
    st.markdown(f"### {t['comparisons']}")
    today_dt = datetime.today()
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
        st.markdown(f"#### {t['this_month_vs_last']}")
        if this_month_sum and last_month_sum:
            income_change = this_month_sum['total_income'] - last_month_sum['total_income']
            profit_change = this_month_sum['total_profit'] - last_month_sum['total_profit']
            st.metric(t['income_change'], format_money(income_change), 
                     delta=f"{income_change/last_month_sum['total_income']*100:.1f}%" if last_month_sum['total_income']>0 else "N/A")
            st.metric(t['profit_change'], format_money(profit_change),
                     delta=f"{profit_change/last_month_sum['total_profit']*100:.1f}%" if last_month_sum['total_profit']>0 else "N/A")
        else:
            st.info(t['insufficient_data'])
    
    last_year_start = (today_dt - timedelta(days=365)).strftime("%Y-%m-%d")
    last_year_end = (today_dt - timedelta(days=365) + timedelta(days=30)).strftime("%Y-%m-%d")
    last_year_df = df[(df['Date'] >= last_year_start) & (df['Date'] <= last_year_end)]
    last_year_sum = get_period_summary(last_year_df) if not last_year_df.empty else None
    with col2:
        st.markdown(f"#### {t['this_year_vs_last']}")
        if this_month_sum and last_year_sum:
            income_change = this_month_sum['total_income'] - last_year_sum['total_income']
            profit_change = this_month_sum['total_profit'] - last_year_sum['total_profit']
            st.metric(t['income_change'], format_money(income_change),
                     delta=f"{income_change/last_year_sum['total_income']*100:.1f}%" if last_year_sum['total_income']>0 else "N/A")
            st.metric(t['profit_change'], format_money(profit_change),
                     delta=f"{profit_change/last_year_sum['total_profit']*100:.1f}%" if last_year_sum['total_profit']>0 else "N/A")
        else:
            st.info(t['insufficient_data'])
    
    # Predictions
    st.markdown(f"### {t['future_predictions']}")
    if len(df) >= 3:
        pred_income, slope_i = predict_future(df, 7, 'TotalIncome')
        pred_profit, slope_p = predict_future(df, 7, 'Profit')
        if pred_income is not None:
            col1, col2 = st.columns(2)
            with col1:
                st.metric(t['projected_income_avg'], format_money(pred_income.mean()))
                st.write(f"{t['trend_increasing'] if slope_i > 0 else t['trend_decreasing']}")
            with col2:
                st.metric(t['projected_profit_avg'], format_money(pred_profit.mean()))
                st.write(f"{t['trend_increasing'] if slope_p > 0 else t['trend_decreasing']}")
            future_dates = [(datetime.today() + timedelta(days=i+1)).strftime("%Y-%m-%d") for i in range(7)]
            pred_df = pd.DataFrame({
                'Date': future_dates,
                'Predicted Income': [format_money(x) for x in pred_income],
                'Predicted Profit': [format_money(x) for x in pred_profit]
            })
            st.dataframe(pred_df, use_container_width=True)
        else:
            st.warning(t['need_3_days'])
    else:
        st.warning(t['need_3_days'])
    
    # Insights
    st.markdown(f"### {t['insights']}")
    insights = generate_insights(filtered, lang)
    st.info(insights)
    
    # Reports
    st.markdown(f"### {t['download_reports']}")
    col1, col2, col3, col4 = st.columns(4)
    def download_report(df, label):
        report = generate_report_df(df, label, lang)
        if report is not None:
            csv = report.to_csv(index=False)
            b64 = base64.b64encode(csv.encode()).decode()
            href = f'<a href="data:text/csv;base64,{b64}" download="{label}_Report.csv" style="background:#b8860b;color:white;padding:8px 16px;border-radius:20px;text-decoration:none;font-weight:bold;">📥 {label}</a>'
            return href
        return "No data"
    today_str = datetime.today().strftime("%Y-%m-%d")
    today_df = df[df['Date'] == today_str]
    with col1:
        st.markdown(download_report(today_df, t['daily']), unsafe_allow_html=True)
    week_start = (datetime.today() - timedelta(days=7)).strftime("%Y-%m-%d")
    week_df = df[(df['Date'] >= week_start) & (df['Date'] <= today_str)]
    with col2:
        st.markdown(download_report(week_df, t['weekly']), unsafe_allow_html=True)
    month_start = (datetime.today() - timedelta(days=30)).strftime("%Y-%m-%d")
    month_df = df[(df['Date'] >= month_start) & (df['Date'] <= today_str)]
    with col3:
        st.markdown(download_report(month_df, t['monthly']), unsafe_allow_html=True)
    year_start = (datetime.today() - timedelta(days=365)).strftime("%Y-%m-%d")
    year_df = df[(df['Date'] >= year_start) & (df['Date'] <= today_str)]
    with col4:
        st.markdown(download_report(year_df, t['yearly']), unsafe_allow_html=True)
    
    # Full data table
    st.markdown(f"### {t['daily_summary_data']}")
    display_cols = ['Date', 'TotalIncome', 'TotalExpenses', 'Profit', 'VAT', 'IncomeTax', 'TotalTax', 'NetProfit']
    styled = filtered[display_cols].copy()
    for col in ['TotalIncome', 'TotalExpenses', 'Profit', 'VAT', 'IncomeTax', 'TotalTax', 'NetProfit']:
        styled[col] = styled[col].apply(lambda x: format_money(x))
    st.dataframe(styled, use_container_width=True)
    
    with st.expander(t['view_transactions']):
        all_trans = get_transactions(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
        if not all_trans.empty:
            st.dataframe(all_trans[['Date', 'Type', 'Category', 'Description', 'Amount']], use_container_width=True)
        else:
            st.info(t['no_transactions_period'])

# ---- FOOTER ----
st.markdown("---")
st.caption(t['footer'])
