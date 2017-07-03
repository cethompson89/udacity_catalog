from flask import render_template, redirect
from flask import session as login_session
from flask import make_response
import json
from functools import wraps


#  improve render to automatically pass certain terms to templates
def render(template, **kwargs):
    username = login_session.get('username', None)
    picture = login_session.get('picture', None)
    return render_template(template, username=username, picture=picture, **kwargs)


# test Oath states before proceeding
def test_state(returned_state):
    if returned_state != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response


def login_required(func):
    """
    A decorator to confirm a user is logged in or redirect as needed.
    """
    @wraps(func)
    def decorated_function(*args, **kwargs):
        # Redirect to login if user not logged in, else execute func.
        if 'username' not in login_session:
            return redirect('/login')
        return func(*args, **kwargs)
    return decorated_function
