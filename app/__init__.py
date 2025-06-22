# app/__init__.py
import os
import logging
from flask import Flask, render_template

# Import your blueprints
from app.home.routes    import home_bp
from app.clients.routes import clients_bp
from app.daily_report   import daily_report_bp
from app.charts.routes  import charts_bp

def create_app():
    # create the Flask app
    app = Flask(
        __name__,
        instance_relative_config=True,
        static_folder='static',
        static_url_path='/static'
    )

    # ── enable INFO logging so logger.info() shows in Render logs ──
    app.logger.setLevel(logging.INFO)

    # secret key & instance folder
    app.secret_key = os.getenv('SECRET_KEY', 'Figurella2025')
    os.makedirs(app.instance_path, exist_ok=True)

    # register blueprints
    app.register_blueprint(home_bp)
    app.register_blueprint(clients_bp)
    app.register_blueprint(daily_report_bp)
    app.register_blueprint(charts_bp)

    # offline fallback page
    @app.route('/offline')
    def offline():
        return render_template('offline.html'), 200

    return app
