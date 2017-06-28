from flask import Flask, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from models import Base, Category, Item, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
import oath_logins.google as google
from helper import render

app = Flask(__name__)

# Connect to Database and create database session
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Show all restaurants
@app.route('/')
def showHome():
        return render('home.html')


@app.route('/login')
def showLogin():
    #  Create anti-forgery state token
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render('login.html', state=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    returned_state = request.args.get('state')
    code = request.data

    (failure_reponse, access_token, gplus_id) = google.validate_user(returned_state, code)
    if failure_reponse:
        return failure_reponse

    # Store the access token in the session for later use.
    login_session['access_token'] = access_token
    login_session['gplus_id'] = gplus_id

    (username, picture, email) = google.get_user_info(access_token)
    login_session['username'] = username
    login_session['picture'] = picture
    login_session['email'] = email
    login_session['provider'] = 'google'

    flash("you are now logged in as %s" % login_session['username'])

    output = "<h1>Welcome, %s!</h1>" % login_session['username']
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            response = google.logout(login_session['access_token'])
            if response:
                return response
            del login_session['gplus_id']
            del login_session['access_token']
            # if login_session['provider'] == 'facebook':
            #     fbdisconnect()
            #     del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
#        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('showHome'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showHome'))


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
