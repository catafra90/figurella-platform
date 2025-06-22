from dotenv import load_dotenv
load_dotenv()

from flask import (
    Blueprint, render_template, request,
    session, jsonify, current_app, send_file
)
import pandas as pd
from datetime import datetime
import os, requests, json

daily_report_bp = Blueprint(
    'daily_report',
    __name__,
    template_folder='templates'
)

def save_daily_report(report):
    # Log receipt
    current_app.logger.info(f"[save_daily_report] payload: {report}")

    # 1) Build path under app/static/reports
    reports_dir = os.path.join(current_app.root_path, 'static', 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    file_path = os.path.join(reports_dir, 'reports.xlsx')

    # Timestamp
    date = datetime.now().strftime("%Y-%m-%d")

    def add_date_column(df):
        if not df.empty:
            df.insert(0, 'Date', date)
        return df

    # 2) If missing, create the workbook with headers
    if not os.path.exists(file_path):
        with pd.ExcelWriter(file_path, engine='openpyxl') as w:
            pd.DataFrame(columns=["Date","client_name","package","revenue"])\
              .to_excel(w, sheet_name="Sales", index=False)
            pd.DataFrame(columns=["Date","name","date","source"])\
              .to_excel(w, sheet_name="Leads", index=False)
            pd.DataFrame(columns=["Date","name","outcome","source"])\
              .to_excel(w, sheet_name="Consultations", index=False)
            pd.DataFrame(columns=["Date","name","provider","description"])\
              .to_excel(w, sheet_name="Opportunities", index=False)
            pd.DataFrame(columns=["Date","attendance_done","no_show"])\
              .to_excel(w, sheet_name="Attendance", index=False)

    # 3) Append only non-empty rows
    with pd.ExcelWriter(file_path, engine='openpyxl',
                        mode='a', if_sheet_exists='overlay') as w:
        sheets = w.book.sheetnames
        sections = {
            "sales":        ["client_name","package","revenue"],
            "leads":        ["name","date","source"],
            "consultations":["name","outcome","source"],
            "opportunities":["name","provider","description"]
        }

        for key, cols in sections.items():
            df = pd.DataFrame(report.get(key, []))
            if df.empty: 
                continue
            df = add_date_column(df)
            mask = df[cols].astype(str)\
                     .apply(lambda r: bool(''.join(r).strip()), axis=1)
            df = df[mask]
            if df.empty or key.capitalize() not in sheets:
                continue
            start = w.sheets[key.capitalize()].max_row
            df.to_excel(
                w, sheet_name=key.capitalize(),
                index=False, header=False, startrow=start
            )

        # Attendance
        att = report.get("attendance", {})
        att_df = pd.DataFrame([att])
        att_df.insert(0, 'Date', date)
        if not att_df.drop(columns="Date")\
                      .replace('', None)\
                      .dropna(how='all').empty:
            start = w.sheets["Attendance"].max_row
            att_df.to_excel(
                w, sheet_name="Attendance",
                index=False, header=False, startrow=start
            )

    # 4) Google Chat webhook
    webhook = os.getenv("GCHAT_WEBHOOK_URL") \
           or os.getenv("GOOGLE_CHAT_WEBHOOK_URL")
    if webhook:
        try:
            resp = requests.post(webhook, json={"text": f"✅ New report: {date}"})
            current_app.logger.info(f"✅ GChat sent: {resp.status_code}")
        except Exception as ex:
            current_app.logger.error(f"⚠️ GChat failed: {ex}")

@daily_report_bp.route('/daily-report/', methods=['GET','POST'])
def combined_report_wizard():
    if request.method == 'POST':
        report = json.loads(request.form.get('full_report_json','{}'))
        save_daily_report(report)
        session.clear()
        return render_template(
            'daily_report/submitted.html',
            active_page='daily-report'
        )
    return render_template(
        'daily_report/combined.html',
        active_page='daily-report'
    )

@daily_report_bp.route('/daily-report/download')
def download_report():
    path = os.path.join(current_app.root_path,
                        'static', 'reports', 'reports.xlsx')
    if not os.path.exists(path):
        return "No report found", 404
    return send_file(path, as_attachment=True,
                     download_name='reports.xlsx')

# (You can leave history for later)
