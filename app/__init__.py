import os
from flask import Flask, render_template

# Import your blueprints
from app.home.routes         import home_bp
from app.clients.routes      import clients_bp
from app.daily_report.routes import daily_report_bp
from app.charts.routes       import charts_bp

def create_app():
    # instance_relative_config lets you write into instance/
    app = Flask(
        __name__,
        instance_relative_config=True,
        static_folder='static',
        static_url_path='/static'
    )

    # secret key
    app.secret_key = os.getenv('SECRET_KEY', 'Figurella2025')

    # ensure instance/ exists
    os.makedirs(app.instance_path, exist_ok=True)

    # register blueprints
    app.register_blueprint(home_bp)
    app.register_blueprint(clients_bp)
    app.register_blueprint(daily_report_bp)
    app.register_blueprint(charts_bp)

    # offline fallback
    @app.route('/offline')
    def offline():
        return render_template('offline.html'), 200

    return app
