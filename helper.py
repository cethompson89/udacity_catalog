from flask import render_template
from flask import session as login_session


#  improve render to automatically pass certain terms to templates
def render(template, **kwargs):
    username = login_session.get('username', None)
    return render_template(template, username=username, **kwargs)
