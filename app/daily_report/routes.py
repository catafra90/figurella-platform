from dotenv import load_dotenv
load_dotenv()

from flask import Blueprint, render_template, request, session, jsonify, current_app
import pandas as pd
from datetime import datetime
import os, requests, json

daily_report_bp = Blueprint('daily_report', __name__, template_folder='templates')

# — Helpers —

def save_daily_report(report):
    current_app.logger.info(f"[save_daily_report] payload received: {report}")
    data_dir = os.path.join(current_app.root_path, '..', 'data')
    os.makedirs(data_dir, exist_ok=True)
    file_path = os.path.join(data_dir, 'reports.xlsx')
    date = datetime.now().strftime("%Y-%m-%d")

    def add_date_column(df):
        if not df.empty:
            df.insert(0, 'Date', date)
        return df

    # Initialize workbook if missing
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

    # Append data
    with pd.ExcelWriter(file_path, engine="openpyxl",
                        mode="a", if_sheet_exists="overlay") as w:
        sheets = w.book.sheetnames
        sections = {
            "sales":        ["client_name","package","revenue"],
            "leads":        ["name","date","source"],
            "consultations":["name","outcome","source"],
            "opportunities":["name","provider","description"]
        }
        for key, cols in sections.items():
            df = pd.DataFrame(report.get(key, {}))
            if df.empty: continue
            df = add_date_column(df)
            mask = df[cols].astype(str) \
                     .apply(lambda r: ''.join(r).strip(), axis=1) != ''
            df = df[mask]
            sheet = key.capitalize()
            if sheet in sheets and not df.empty:
                start = w.sheets[sheet].max_row
                df.to_excel(w, sheet_name=sheet,
                            index=False, header=False, startrow=start)

        # Attendance
        att = report.get("attendance", {})
        att_df = pd.DataFrame([att])
        att_df.insert(0, 'Date', date)
        if not att_df.drop(columns="Date") \
                     .replace('', None) \
                     .dropna(how='all').empty:
            start = w.sheets["Attendance"].max_row
            att_df.to_excel(w, sheet_name="Attendance",
                            index=False, header=False, startrow=start)

    # Optional webhook
    webhook = os.getenv("GCHAT_WEBHOOK_URL")
    if webhook:
        try:
            requests.post(webhook, json={"text": f"✅ New report: {date}"})
        except Exception as ex:
            current_app.logger.warning("GChat failed: %s", ex)

def handle_offline_submission(data):
    try:
        save_daily_report(data)
        return jsonify({"message": "Offline report saved"}), 200
    except Exception as err:
        return jsonify({"error": str(err)}), 500

# — Combined Wizard Route —

@daily_report_bp.route('/daily-report/', endpoint='combined_report_wizard',
                       methods=['GET','POST'])
def combined_report_wizard():
    if request.method == 'POST':
        if request.is_json:
            return handle_offline_submission(request.get_json())

        report = json.loads(request.form.get('full_report_json','{}'))
        save_daily_report(report)
        session.clear()
        return render_template('daily_report/submitted.html',
                               active_page='daily-report')

    return render_template('daily_report/combined.html',
                           active_page='daily-report')

# — New History Route —

@daily_report_bp.route('/daily-report/history/', endpoint='history')
def history():
    data_dir = os.path.join(current_app.root_path, '..', 'data')
    file_path = os.path.join(data_dir, 'reports.xlsx')
    entries = []

    if os.path.exists(file_path):
        # Read and combine every sheet
        all_sheets = pd.read_excel(file_path, sheet_name=None)
        for section, df in all_sheets.items():
            for row in df.to_dict('records'):
                entries.append({"section": section, **row})
        # Sort newest first
        entries.sort(key=lambda x: x.get("Date"), reverse=True)

    return render_template('daily_report/history.html',
                           active_page='daily-report-history',
                           entries=entries)
