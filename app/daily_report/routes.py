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
    return render_template('daily_report/step1.html',
                           sales=session.get('sales', {}),
                           active_page='daily-report')

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

@daily_report_bp.route('/step5/', methods=['GET', 'POST'])
def step5():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            attendance_done = data.get('attendance_done', '')
            no_show = data.get('no_show', '')
        else:
            attendance_done = request.form['attendance_done']
            no_show = request.form['no_show']

        save_daily_report(attendance_done, no_show)
        session.clear()

        if request.is_json:
            return jsonify({"message": "Report saved offline"}), 200
        else:
            return render_template('daily_report/submitted.html', active_page='daily-report')

    return render_template('daily_report/step5.html', active_page='daily-report')

@daily_report_bp.route('/')
def home():
    return render_template('home.html', active_page='home')
