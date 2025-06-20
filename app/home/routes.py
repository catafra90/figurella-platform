from flask import Blueprint, render_template

home_bp = Blueprint('home', __name__, template_folder='templates')

@home_bp.route('/')
def index():
    # you already pass active_page for highlighting in the nav
    return render_template('index.html', active_page='home')

@home_bp.route('/offline')
def offline():
    # this will serve your offline.html whenever the SW falls back
    return render_template('offline.html', active_page='offline'), 200
