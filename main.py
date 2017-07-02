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
import oath_logins.facebook as facebook
from helper import render, test_state

app = Flask(__name__)

# Connect to Database and create database session
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Show homepage
@app.route('/')
@app.route('/category-<int:category_id>', methods=['GET'])
def showHome(category_id=None):
        categories = Category.getAllCategories()
        if category_id:
            selected_category = Category.getCategory(category_id)
            items = Item.getByCategory(category_id)
        else:
            selected_category = None
            items = Item.getAllItems()
        return render('home.html', categories=categories, items=items, selected_category=selected_category)


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

    failure_reponse = test_state(returned_state)
    if failure_reponse:
        return failure_reponse

    (failure_reponse, access_token, gplus_id) = google.validate_user(code)
    if failure_reponse:
        return failure_reponse

    (username, picture, email) = google.get_user_info(access_token)

    login_session['access_token'] = access_token
    login_session['gplus_id'] = gplus_id
    login_session['username'] = username
    login_session['picture'] = picture
    login_session['email'] = email
    login_session['provider'] = 'google'

    # see if user exists
    user_id = User.getUserID(login_session['email'])
    if not user_id:
        user_id = User.createUser(login_session)
    login_session['user_id'] = user_id

    output = "<h1>Welcome, %s!</h1>" % login_session['username']
    flash("you are now logged in as %s" % login_session['username'])
    return output


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    returned_state = request.args.get('state')
    access_token = request.data

    failure_reponse = test_state(returned_state)
    if failure_reponse:
        return failure_reponse

    token = facebook.validate_user(access_token)

    (username, picture, email, facebook_id) = facebook.get_user_info(token)

    login_session['access_token'] = token
    login_session['facebook_id'] = facebook_id
    login_session['username'] = username
    login_session['picture'] = picture
    login_session['email'] = email
    login_session['provider'] = 'facebook'

    # see if user exists
    user_id = User.getUserID(login_session['email'])
    if not user_id:
        user_id = User.createUser(login_session)
    login_session['user_id'] = user_id

    output = "<h1>Welcome, %s!</h1>" % login_session['username']
    flash("you are now logged in as %s" % login_session['username'])
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
        if login_session['provider'] == 'facebook':
            facebook.logout(login_session['facebook_id'], login_session['access_token'])
            del login_session['facebook_id']
        del login_session['access_token']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('showHome'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showHome'))


@app.route('/category', methods=['GET', 'POST'])
def newCategory():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        category = request.form['category']
        Category.createCategory(category)
        flash('New Category %s Successfully Created' % category)
        return redirect(url_for('showHome'))
    else:
        return render('newCategory.html')


@app.route('/item-<int:item_id>', methods=['GET'])
def displayItem(item_id):
    item = Item.getItemInfo(item_id)
    return render('item.html', item=item)



@app.route('/edit-<int:item_id>', methods=['GET', 'POST'])
@app.route('/newitem', methods=['GET', 'POST'])
def newItem(item_id=None):
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        item_category = request.form['category']
        if name and description:  # required information
            category_id = Category.getCategoryID(item_category)
            user_id = login_session['user_id']
            if item_id:  # editting item
                Item.updateItem(item_id, name, description, category_id, user_id)
                flash('Item %s Successfully Updated' % name)
            else:  # create new item
                item_id = Item.createItem(name, description, category_id, user_id)
                flash('New Item %s Successfully Created' % name)
            return redirect("/item-%s" % str(item_id))
        else:  # take user back to form to fix missing data
            categories = Category.getAllCategories()
            name_error = ""
            description_error = ""
            if not name:
                name_error = "Name required"
            if not description:
                description_error = "Description required"
            return render('newItem.html', categories=categories, name=name, description=description, item_category=item_category, name_error=name_error, description_error=description_error)

    else:  # render form
        categories = Category.getAllCategories()
        name, description, item_category = "", "", ""
        if item_id:
            item = Item.getItemInfo(item_id)
            name = item.name
            description = item.description
            item_category = item.category.name
        return render('newItem.html', categories=categories, name=name, description=description, item_category=item_category)


@app.route('/delete-<int:item_id>', methods=['GET', 'POST'])
def deleteItem(item_id):
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        item_id = request.form['item_id']
        Item.deleteItem(item_id)
        return redirect(url_for('showHome'))
    else:
        item = Item.getItemInfo(item_id)
        return render('delete.html', item=item)


#  Not linked to in site
@app.route('/category-<int:category_id>/JSON')
def categoryJSON(category_id):
    items = Item.getByCategory(category_id)
    return jsonify(Item=[i.serialize for i in items])


@app.route('/JSON')
def allJSON():
    categories = Category.getAllCategories()
    return jsonify(Category=[c.serialize_with_items for c in categories])


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
