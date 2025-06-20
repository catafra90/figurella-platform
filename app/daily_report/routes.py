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

# Step 1: Sales
@daily_report_bp.route('/step1/', methods=['GET', 'POST'])
def step1():
    if request.method == 'POST':
        session['sales'] = {
            'client_name': request.form.getlist('client_name'),
            'package':     request.form.getlist('package'),
            'revenue':     request.form.getlist('revenue')
        }
        return redirect(url_for('daily_report.step2'))
    return render_template('daily_report/step1.html',
                           sales=session.get('sales', {}),
                           active_page='daily-report')

# Step 2: Leads
@daily_report_bp.route('/step2/', methods=['GET', 'POST'])
def step2():
    if request.method == 'POST':
        session['leads'] = {
            'name':   request.form.getlist('lead_name'),
            'date':   request.form.getlist('lead_date'),
            'source': request.form.getlist('lead_source')
        }
        return redirect(url_for('daily_report.step3'))
    return render_template('daily_report/step2.html',
                           leads=session.get('leads', {}),
                           active_page='daily-report')

# Step 3: Consultations
@daily_report_bp.route('/step3/', methods=['GET', 'POST'])
def step3():
    if request.method == 'POST':
        session['consultations'] = {
            'name':    request.form.getlist('consultation_name'),
            'outcome': request.form.getlist('consultation_outcome'),
            'source':  request.form.getlist('consultation_source')
        }
        return redirect(url_for('daily_report.step4'))
    return render_template('daily_report/step3.html',
                           consultations=session.get('consultations', {}),
                           active_page='daily-report')

# Step 4: Opportunities
@daily_report_bp.route('/step4/', methods=['GET', 'POST'])
def step4():
    if request.method == 'POST':
        session['opportunities'] = {
            'name':        request.form.getlist('opportunity_opportunity_name'),
            'provider':    request.form.getlist('opportunity_opportunity_provider'),
            'description': request.form.getlist('opportunity_opportunity_description')
        }
        return redirect(url_for('daily_report.step5'))
    return render_template('daily_report/step4.html',
                           opportunities=session.get('opportunities', {}),
                           active_page='daily-report')

# Step 5: Submit & Review
@daily_report_bp.route('/step5/', methods=['GET', 'POST'])
def step5():
    if request.method == 'POST':
        # Offline JSON submission
        if request.is_json:
            return handle_offline_submission(request.get_json())
        # Final wizard submission
        if 'full_report_json' in request.form:
            report = json.loads(request.form['full_report_json'])
        else:
            attendance_done = request.form.get('attendance_done', '')
            no_show         = request.form.get('no_show', '')
            report = build_full_report(attendance_done, no_show)

        save_daily_report(report)
        session.clear()
        return render_template('daily_report/submitted.html',
                               active_page='daily-report')

    return render_template('daily_report/step5.html', active_page='daily-report')

# Offline queue handler
@daily_report_bp.route('/submit-offline', methods=['POST'])
def submit_offline():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data received"}), 400
    return handle_offline_submission(data)

# Helpers omitted for brevity...

# ── Combined Wizard Route ───────────────────────────────────────────────────────
@daily_report_bp.route('/daily-report/', endpoint='combined_report_wizard', methods=['GET', 'POST'])
def daily_report_wizard():
    if request.method == 'POST':
        if request.is_json:
            return handle_offline_submission(request.get_json())
        if 'full_report_json' in request.form:
            data = json.loads(request.form['full_report_json'])
            save_daily_report(data)
            session.clear()
            return render_template('daily_report/submitted.html', active_page='daily-report')
        return redirect(url_for('daily_report.combined_report_wizard'))

    return render_template('daily_report/combined.html', active_page='daily-report')
