from dotenv import load_dotenv
load_dotenv()

from flask import Blueprint, render_template, request, session, jsonify, current_app
import pandas as pd
from datetime import datetime
import os, requests, json

daily_report_bp = Blueprint(
    'daily_report',
    __name__,
    template_folder='templates'
)

def save_daily_report(report):
    current_app.logger.info(f"[save_daily_report] payload received: {report}")

    # ─── Write into app/static/reports ────────────────────────────────────────────
    # This folder lives at:
    #   C:\Users\franc\Desktop\AI_Project\app\static\reports
    reports_dir = os.path.join(current_app.root_path, 'static', 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    file_path = os.path.join(reports_dir, 'reports.xlsx')
    # ────────────────────────────────────────────────────────────────────────────────

    date = datetime.now().strftime("%Y-%m-%d")

    def add_date_column(df):
        if not df.empty:
            df.insert(0, 'Date', date)
        return df

    # Initialize the .xlsx if missing
    if not os.path.exists(file_path):
        with pd.ExcelWriter(file_path, engine="openpyxl") as w:
            pd.DataFrame(columns=["Date","client_name","package","revenue"]) \
              .to_excel(w, sheet_name="Sales", index=False)
            pd.DataFrame(columns=["Date","name","date","source"]) \
              .to_excel(w, sheet_name="Leads", index=False)
            pd.DataFrame(columns=["Date","name","outcome","source"]) \
              .to_excel(w, sheet_name="Consultations", index=False)
            pd.DataFrame(columns=["Date","name","provider","description"]) \
              .to_excel(w, sheet_name="Opportunities", index=False)
            pd.DataFrame(columns=["Date","attendance_done","no_show"]) \
              .to_excel(w, sheet_name="Attendance", index=False)

    # Append the new data
    with pd.ExcelWriter(file_path,
                        engine="openpyxl",
                        mode="a",
                        if_sheet_exists="overlay") as w:
        sheets = w.book.sheetnames
        sections = {
            "sales":        ["client_name","package","revenue"],
            "leads":        ["name","date","source"],
            "consultations":["name","outcome","source"],
            "opportunities":["name","provider","description"]
        }
        for key, cols in sections.items():
            df = pd.DataFrame(report.get(key, {}))
            if df.empty: 
                continue
            df = add_date_column(df)
            mask = df[cols].astype(str)\
                     .apply(lambda r: ''.join(r).strip(), axis=1) != ''
            df = df[mask]
            sheet = key.capitalize()
            if sheet in sheets and not df.empty:
                start = w.sheets[sheet].max_row
                df.to_excel(w,
                            sheet_name=sheet,
                            index=False,
                            header=False,
                            startrow=start)

        # Attendance
        att = report.get("attendance", {})
        att_df = pd.DataFrame([att])
        att_df.insert(0, 'Date', date)
        if not att_df.drop(columns="Date")\
                     .replace('', None)\
                     .dropna(how='all').empty:
            start = w.sheets["Attendance"].max_row
            att_df.to_excel(w,
                            sheet_name="Attendance",
                            index=False,
                            header=False,
                            startrow=start)

    # Fire off your Google Chat webhook (if set)
    webhook = os.getenv("GCHAT_WEBHOOK_URL")
    if webhook:
        try:
            resp = requests.post(webhook, json={"text": f"✅ New report: {date}"})
            current_app.logger.info("✅ GChat sent: %s", resp.status_code)
        except Exception as ex:
            current_app.logger.warning("⚠️ GChat failed: %s", ex)

@daily_report_bp.route('/daily-report/', methods=['GET','POST'])
def combined_report_wizard():
    if request.method == 'POST':
        if request.is_json:
            return jsonify({"error": "Offline not supported"}), 400

        report = json.loads(request.form.get('full_report_json','{}'))
        save_daily_report(report)
        session.clear()
        return render_template('daily_report/submitted.html',
                               active_page='daily-report')
    return render_template('daily_report/combined.html',
                           active_page='daily-report')

# (history route unchanged)
