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
    'daily_report', __name__, template_folder='templates'
)

def save_daily_report(report):
    current_app.logger.info(f"[save_daily_report] payload received: {report}")

    # 1) Compute path to AI_Project root and reports.xlsx
    project_root = os.path.abspath(os.path.join(current_app.root_path, os.pardir))
    file_path = os.path.join(project_root, 'reports.xlsx')
    date = datetime.now().strftime("%Y-%m-%d")

    def add_date_column(df):
        if not df.empty:
            df.insert(0, 'Date', date)
        return df

    # 2) Initialize workbook if missing
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

    # 3) Append data, but only if at least one field in each row is non-empty
    with pd.ExcelWriter(file_path, engine="openpyxl",
                        mode="a", if_sheet_exists="overlay") as w:
        sheets  = w.book.sheetnames
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
            # keep only rows where any of the key columns is non-empty
            mask = df[cols].astype(str).apply(lambda r: bool(''.join(r).strip()), axis=1)
            df = df[mask]
            if not df.empty and key.capitalize() in sheets:
                start = w.sheets[key.capitalize()].max_row
                df.to_excel(
                    w,
                    sheet_name=key.capitalize(),
                    index=False,
                    header=False,
                    startrow=start
                )

        # Attendance block
        att = report.get("attendance", {})
        att_df = pd.DataFrame([att])
        att_df.insert(0, 'Date', date)
        # only append if at least one attendance field is non-empty
        if not att_df.drop(columns="Date").replace('', None).dropna(how='all').empty:
            start = w.sheets["Attendance"].max_row
            att_df.to_excel(
                w,
                sheet_name="Attendance",
                index=False,
                header=False,
                startrow=start
            )

    # 4) Fire Google Chat webhook
    webhook = os.getenv("GCHAT_WEBHOOK_URL") or os.getenv("GOOGLE_CHAT_WEBHOOK_URL")
    if webhook:
        try:
            resp = requests.post(webhook, json={"text": f"✅ New report submitted: {date}"})
            current_app.logger.info(f"✅ GChat sent: {resp.status_code} {resp.text}")
        except Exception as ex:
            current_app.logger.error(f"⚠️ GChat failed: {ex}")

@daily_report_bp.route('/daily-report/', methods=['GET','POST'])
def combined_report_wizard():
    if request.method == 'POST':
        if request.is_json:
            return jsonify({"error": "Offline not supported"}), 400

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

# — Download endpoint for direct access if desired —  

@daily_report_bp.route('/daily-report/download')
def download_report():
    project_root = os.path.abspath(os.path.join(current_app.root_path, os.pardir))
    file_path = os.path.join(project_root, 'reports.xlsx')
    if not os.path.exists(file_path):
        return "Report not found", 404
    return send_file(
        file_path,
        as_attachment=True,
        download_name='reports.xlsx'
    )

# — History Route —  

@daily_report_bp.route('/daily-report/history/', endpoint='history')
def history():
    project_root = os.path.abspath(os.path.join(current_app.root_path, os.pardir))
    file_path = os.path.join(project_root, 'reports.xlsx')
    entries = []
    if os.path.exists(file_path):
        all_sheets = pd.read_excel(file_path, sheet_name=None)
        for section, df in all_sheets.items():
            for row in df.to_dict('records'):
                entries.append({"section": section, **row})
        entries.sort(key=lambda x: x.get("Date"), reverse=True)

    return render_template(
        'daily_report/history.html',
        active_page='daily-report-history',
        entries=entries
    )
