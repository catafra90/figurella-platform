import os
from flask import Flask, render_template

# Import blueprints
from app.clients.routes     import clients_bp
from app.daily_report.routes import daily_report_bp
from app.charts.routes      import charts_bp
from app.home.routes        import home_bp

def create_app():
    # Enable instance folder (writable) and point static to app/static
    app = Flask(__name__,
                instance_relative_config=True,
                static_folder='static',
                static_url_path='/static')
    app.secret_key = 'Figurella2025'

    # Ensure the instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

    # Register blueprints
    app.register_blueprint(home_bp)
    app.register_blueprint(clients_bp)
    app.register_blueprint(daily_report_bp)
    app.register_blueprint(charts_bp)

    # Offline fallback page
    @app.route('/offline')
    def offline():
        return render_template('offline.html'), 200

    return app
