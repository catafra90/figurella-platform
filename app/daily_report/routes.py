from flask import Blueprint, render_template, request, session, jsonify, current_app, send_file
import pandas as pd
from datetime import datetime
import os, requests, json

# ← THIS MUST BE HERE:
daily_report_bp = Blueprint(
    'daily_report',
    __name__,
    template_folder='templates'
)

def save_daily_report(report):
    current_app.logger.info(f"[save_daily_report] payload: {report}")

    # 1) Build reports folder under static
    reports_dir = os.path.join(current_app.root_path, 'static', 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    file_path = os.path.join(reports_dir, 'reports.xlsx')

    date = datetime.now().strftime("%Y-%m-%d")
    def add_date_column(df):
        if not df.empty:
            df.insert(0, 'Date', date)
        return df

    # 2) Initialize workbook if missing
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

    # 3) Append data with proper column mapping
    with pd.ExcelWriter(file_path, engine='openpyxl',
                        mode='a', if_sheet_exists='overlay') as w:
        sheets = w.book.sheetnames

        # mapping: section -> (json_fields, sheet_columns)
        sections = {
            "sales":        (["client_name","package","revenue"],
                             ["client_name","package","revenue"]),
            "leads":        (["lead_name","lead_date","lead_source"],
                             ["name","date","source"]),
            "consultations":(["consultation_name","consultation_outcome","consultation_source"],
                             ["name","outcome","source"]),
            "opportunities":(["opportunity_name","opportunity_provider","opportunity_description"],
                             ["name","provider","description"])
        }

        for key, (json_cols, sheet_cols) in sections.items():
            data = report.get(key, [])
            if not data:
                continue

            df = pd.DataFrame(data)
            # rename JSON fields to match sheet columns
            df = df.rename(columns=dict(zip(json_cols, sheet_cols)))
            df = add_date_column(df)

            # drop rows where all sheet_cols are empty
            mask = df[sheet_cols].astype(str)\
                     .apply(lambda row: bool("".join(row).strip()), axis=1)
            df = df[mask]
            if df.empty or key.capitalize() not in sheets:
                continue

            start = w.sheets[key.capitalize()].max_row
            df.to_excel(
                w,
                sheet_name=key.capitalize(),
                index=False,
                header=False,
                startrow=start
            )

        # Attendance (fields already match sheet)
        att = report.get("attendance", {})
        att_df = pd.DataFrame([att])
        att_df.insert(0, 'Date', date)
        # only append if any attendance field is non-empty
        if not att_df.drop(columns="Date")\
                     .replace('', None)\
                     .dropna(how='all').empty:
            start = w.sheets["Attendance"].max_row
            att_df.to_excel(
                w,
                sheet_name="Attendance",
                index=False,
                header=False,
                startrow=start
            )

    # 4) Notify Google Chat
    webhook = os.getenv("GCHAT_WEBHOOK_URL") or os.getenv("GOOGLE_CHAT_WEBHOOK_URL")
    if webhook:
        try:
            resp = requests.post(webhook, json={"text": f"✅ New report: {date}"})
            current_app.logger.info(f"✅ GChat sent: {resp.status_code}")
        except Exception as ex:
            current_app.logger.error(f"⚠️ GChat failed: {ex}")
