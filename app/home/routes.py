from flask import Blueprint, render_template

home_bp = Blueprint('home', __name__, template_folder='templates')

# Homepage route
@home_bp.route('/')
def index():
    return render_template('index.html', active_page='home')

# Offline fallback route for service worker
@home_bp.route('/offline')
def offline():
    return render_template('offline.html', active_page='offline'), 200
