from dotenv import load_dotenv
load_dotenv()

from flask import Blueprint, render_template, request, redirect, session, url_for, jsonify
import pandas as pd
from datetime import datetime
import os
import requests

daily_report_bp = Blueprint('daily_report', __name__, template_folder='templates')

@daily_report_bp.route('/step1/', methods=['GET', 'POST'])
def step1():
    if request.method == 'POST':
        session['sales'] = {
            'client_name': request.form.getlist('client_name'),
            'package':     request.form.getlist('package'),
            'revenue':     request.form.getlist('revenue')
        }
        return redirect(url_for('daily_report.step2'))
    return render_template('daily_report/step1.html', sales=session.get('sales', {}), active_page='daily-report')

@daily_report_bp.route('/step2/', methods=['GET', 'POST'])
def step2():
    if request.method == 'POST':
        session['leads'] = {
            'name':   request.form.getlist('lead_name'),
            'date':   request.form.getlist('lead_date'),
            'source': request.form.getlist('lead_source')
        }
        return redirect(url_for('daily_report.step3'))
    return render_template('daily_report/step2.html', leads=session.get('leads', {}), active_page='daily-report')

@daily_report_bp.route('/step3/', methods=['GET', 'POST'])
def step3():
    if request.method == 'POST':
        session['consultations'] = {
            'name':    request.form.getlist('consultation_name'),
            'outcome': request.form.getlist('consultation_outcome'),
            'source':  request.form.getlist('consultation_source')
        }
        return redirect(url_for('daily_report.step4'))
    return render_template('daily_report/step3.html', consultations=session.get('consultations', {}), active_page='daily-report')

@daily_report_bp.route('/step4/', methods=['GET', 'POST'])
def step4():
    if request.method == 'POST':
        session['opportunities'] = {
            'name':        request.form.getlist('opportunity_opportunity_name'),
            'provider':    request.form.getlist('opportunity_opportunity_provider'),
            'description': request.form.getlist('opportunity_opportunity_description')
        }
        return redirect(url_for('daily_report.step5'))
    return render_template('daily_report/step4.html', opportunities=session.get('opportunities', {}), active_page='daily-report')

@daily_report_bp.route('/step5/', methods=['GET', 'POST'])
def step5():
    if request.method == 'POST':
        print("➡️ step5 called; is_json =", request.is_json, "form keys:", list(request.form.keys()))
        if request.is_json:
            data = request.get_json()
            return handle_offline_submission(data)
        elif 'full_report_json' in request.form:
            import json
            data = json.loads(request.form['full_report_json'])
            save_daily_report(data)
            session.clear()
            return render_template('daily_report/submitted.html', active_page='daily-report')
        else:
            attendance_done = request.form.get('attendance_done', '')
            no_show = request.form.get('no_show', '')
            report = build_full_report(attendance_done, no_show)
            save_daily_report(report)
            session.clear()
            return render_template('daily_report/submitted.html', active_page='daily-report')
    return render_template('daily_report/step5.html', active_page='daily-report')

@daily_report_bp.route('/submit-offline', methods=['POST'])
def submit_offline():
    data = request.get_json()
    print("📩 Offline submission received")
    print("🔎 Payload:", data)
    if not data:
        print("❌ No data received in offline submission")
        return jsonify({"error": "No data received"}), 400
    try:
        save_daily_report(data)
        print("✅ Offline report saved successfully")
        return jsonify({"message": "Offline report saved"}), 200
    except Exception as e:
        print("❌ Error saving offline report:", e)
        return jsonify({"error": str(e)}), 500

@daily_report_bp.route('/')
def home():
    return render_template('home.html', active_page='home')

def build_full_report(attendance_done, no_show):
    return {
        "sales": session.get("sales", {}),
        "leads": session.get("leads", {}),
        "consultations": session.get("consultations", {}),
        "opportunities": session.get("opportunities", {}),
        "attendance": {
            "attendance_done": attendance_done,
            "no_show": no_show
        }
    }

def save_daily_report(report):
    # Persist to Render disk
    file_path = "/mnt/data/reports.xlsx"
    date = datetime.now().strftime("%Y-%m-%d")

    # Ensure workbook exists with headers
    if not os.path.exists(file_path):
        print("🔄 Creating new reports.xlsx with headers")
        with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
            pd.DataFrame(columns=["Date","client_name","package","revenue"]).to_excel(writer, sheet_name="Sales", index=False)
            pd.DataFrame(columns=["Date","name","date","source"]).to_excel(writer, sheet_name="Leads", index=False)
            pd.DataFrame(columns=["Date","name","outcome","source"]).to_excel(writer, sheet_name="Consultations", index=False)
            pd.DataFrame(columns=["Date","name","provider","description"]).to_excel(writer, sheet_name="Opportunities", index=False)
            pd.DataFrame(columns=["Date","attendance_done","no_show"]).to_excel(writer, sheet_name="Attendance", index=False)

    print(f"🔄 Saving report to {file_path}")
    print(f"🧾 Report data: {report}")

    with pd.ExcelWriter(file_path, engine="openpyxl", mode="a", if_sheet_exists="overlay") as writer:
        sheets = writer.book.sheetnames

        def add_date_column(df):
            df.insert(0, "Date", date)
            return df

        # Sections
        for key, cols in {
            "sales": ["client_name","package","revenue"],
            "leads": ["name","date","source"],
            "consultations": ["name","outcome","source"],
            "opportunities": ["name","provider","description"]
        }.items():
            raw = report.get(key, {})
            df = pd.DataFrame(raw)
            if df.empty: continue
            df = add_date_column(df)
            # drop rows where all data cols blank
            df = df[df[cols].astype(str).apply("".join, axis=1).str.strip().astype(bool)]
            if not df.empty and key.capitalize() in sheets:
                start = writer.sheets[key.capitalize()].max_row
                df.to_excel(writer, sheet_name=key.capitalize(), index=False, header=False, startrow=start)

        # Attendance
        att = report["attendance"]
        att_df = pd.DataFrame([att])
        att_df.insert(0, "Date", date)
        if att_df.drop(columns="Date").astype(str).apply("".join, axis=1).str.strip().astype(bool).any():
            start = writer.sheets["Attendance"].max_row
            att_df.to_excel(writer, sheet_name="Attendance", index=False, header=False, startrow=start)

    # Notify Google Chat
    webhook = os.getenv("GCHAT_WEBHOOK_URL")
    if webhook:
        try:
            requests.post(webhook, json={"text": f"✅ New report: {date}"})
        except Exception as e:
            print("⚠️ Google Chat webhook failed:", e)

def handle_offline_submission(data):
    try:
        save_daily_report(data)
        return jsonify({"message": "Offline report saved"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
