from dotenv import load_dotenv
load_dotenv()

from flask import Blueprint, render_template, request, redirect, session, url_for, jsonify, current_app
import pandas as pd
from datetime import datetime
import os
import requests
import json

# Blueprint setup
daily_report_bp = Blueprint('daily_report', __name__, template_folder='templates')

# ── Helpers ─────────────────────────────────────────────────────────────────────
def build_full_report(attendance_done, no_show):
    return {
        "sales":         session.get("sales", {}),
        "leads":         session.get("leads", {}),
        "consultations": session.get("consultations", {}),
        "opportunities": session.get("opportunities", {}),
        "attendance": {
            "attendance_done": attendance_done,
            "no_show":         no_show
        }
    }


def save_daily_report(report):
    # Log incoming payload for debugging
    current_app.logger.info(f"[save_daily_report] payload received: {report}")

    data_dir = os.path.join(current_app.root_path, '..', 'data')
    os.makedirs(data_dir, exist_ok=True)
    file_path = os.path.join(data_dir, 'reports.xlsx')
    date = datetime.now().strftime("%Y-%m-%d")

    def add_date_column(df):
        if not df.empty:
            df.insert(0, 'Date', date)
        return df

    # Initialize file with proper sheets
    if not os.path.exists(file_path):
        with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
            pd.DataFrame(columns=["Date","client_name","package","revenue"]).to_excel(writer, sheet_name="Sales", index=False)
            pd.DataFrame(columns=["Date","name","date","source"]).to_excel(writer, sheet_name="Leads", index=False)
            pd.DataFrame(columns=["Date","name","outcome","source"]).to_excel(writer, sheet_name="Consultations", index=False)
            pd.DataFrame(columns=["Date","name","provider","description"]).to_excel(writer, sheet_name="Opportunities", index=False)
            pd.DataFrame(columns=["Date","attendance_done","no_show"]).to_excel(writer, sheet_name="Attendance", index=False)

    # Append data to each sheet
    with pd.ExcelWriter(file_path, engine="openpyxl", mode="a", if_sheet_exists="overlay") as writer:
        sheets = writer.book.sheetnames
        sections = {
            "sales":        ["client_name","package","revenue"],
            "leads":        ["name","date","source"],
            "consultations": ["name","outcome","source"],
            "opportunities": ["name","provider","description"]
        }
        for key, cols in sections.items():
            df = pd.DataFrame(report.get(key, {}))
            if df.empty:
                continue
            df = add_date_column(df)
            mask = df[cols].astype(str).apply(lambda row: ''.join(row).strip(), axis=1) != ''
            df = df[mask]
            sheet = key.capitalize()
            if sheet in sheets and not df.empty:
                start = writer.sheets[sheet].max_row
                df.to_excel(writer, sheet_name=sheet, index=False, header=False, startrow=start)
        # Attendance sheet
        att = report.get("attendance", {})
        att_df = pd.DataFrame([att])
        att_df.insert(0, 'Date', date)
        if not att_df.drop(columns="Date").replace('', None).dropna(how='all').empty:
            start = writer.sheets["Attendance"].max_row
            att_df.to_excel(writer, sheet_name="Attendance", index=False, header=False, startrow=start)

    # Optional: Google Chat webhook
    webhook = os.getenv("GCHAT_WEBHOOK_URL")
    if webhook:
        try:
            requests.post(webhook, json={"text": f"✅ New report submitted: {date}"})
        except Exception as e:
            current_app.logger.warning("GChat webhook failed: %s", e)


def handle_offline_submission(data):
    try:
        save_daily_report(data)
        return jsonify({"message": "Offline report saved"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── Routes ───────────────────────────────────────────────────────────────────────
@daily_report_bp.route('/daily-report/', endpoint='combined_report_wizard', methods=['GET', 'POST'])
def combined_report_wizard():
    if request.method == 'POST':
        try:
            if request.is_json:
                return handle_offline_submission(request.get_json())

            # Parse full JSON from form
            report = json.loads(request.form.get('full_report_json', '{}'))
            save_daily_report(report)
            session.clear()
            return render_template('daily_report/submitted.html', active_page='daily-report')

        except Exception as e:
            current_app.logger.exception("Error saving daily report")
            return render_template(
                'daily_report/combined.html',
                active_page='daily-report',
                error_message=str(e)
            ), 500

    # GET: serve the combined single-page form
    return render_template('daily_report/combined.html', active_page='daily-report')
