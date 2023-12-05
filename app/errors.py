from flask import render_template
from app import app, db


@app.errorhandler(401)
def error_401(error):
    return render_template('401.html'), 401


@app.errorhandler(403)
def error_403(error):
    return render_template('403.html'), 403


@app.errorhandler(404)
def error_404(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def error_500(error):
    db.session.rollback()
    return render_template('500.html'), 500
