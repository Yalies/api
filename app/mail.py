from flask import render_template
from flask_mail import Message
from app import app, mail
from app.models import User, Person

DATE_FMT = '%Y-%m-%d'
TIME_FMT = '%H:%M'
DATETIME_FMT = DATE_FMT + ' ' + TIME_FMT


def get_admin_emails():
    admins = User.query.filter_by(admin=True).all()
    admin_ids = [admin.id for admin in admins]
    admin_people = Person.query.filter(Person.netid.in_(admin_ids)).all()
    return [person.email for person in admin_people]


def send_mail(subject, html, recipients):
    with app.app_context():
        msg = Message(subject, html=html, recipients=recipients, sender=app.config['MAIL_DEFAULT_SENDER'])
        try:
            mail.send(msg)
        except Exception as e:
            # Handle any exceptions that may occur during email sending
            print(f"Error sending email: {e}")


def status_color(days_left):
    if days_left <= 1:
        return 'red'
    if days_left <= 3:
        return 'orange'
    if days_left <= 5:
        return 'yellow'
    return 'green'


def send_scraper_report(stats=None, error=None):
    subject = None
    with app.app_context():
        if error:
            subject = 'Yalies Scraper Error Report'
            html = render_template('mail/scraper_report.html', error=error, stats=None)
        else:
            subject = 'Yalies Scraper Report ' + \
                stats['end_time'].strftime(DATE_FMT)
            html = render_template('mail/scraper_report.html', error=None, stats=stats, DATE_FMT=DATE_FMT, TIME_FMT=TIME_FMT, DATETIME_FMT=DATETIME_FMT, status_color=status_color)

    recipients = get_admin_emails()
    if recipients:
        send_mail(subject=subject, html=html, recipients=recipients)
    else:
        print("No recipients available to send the email.")
