from __future__ import print_function
from six.moves import xrange
from ortools.constraint_solver import pywrapcp
from ortools.constraint_solver import routing_enums_pb2
from math import sin, cos, sqrt, atan2, radians

from flask import Flask, render_template, url_for, request, session, redirect, flash, jsonify
from flask_pymongo import PyMongo

import math
import requests
import json
import bson
import statistics
from key import key
import datetime
#    Global Value   #
average_speed = 40
maximum_worktime = 8
visit_duration = 1
#    Global Value   #

app = Flask(__name__)
# connection for database
app.config['MONGO_DBNAME'] = 'canvassing_db'
app.config['MONGO_URI'] = 'mongodb://songyy:cse308@ds125953.mlab.com:25953/canvassing_db'

mongo = PyMongo(app)  # instantiate the db connection
search_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"   # either json or xml
details_url = "https://maps.googleapis.com/maps/api/place/details/json"


@app.route('/canvass/<loc>', methods=['GET'])
def canvass(loc):
    today = datetime.datetime.now()
    tasks = mongo.db.tasks.find()
    next_location = None
    task_id = None
    lat_lng_1, lat_lng_2 = None, None
    for task in tasks:          # should be modified later
        if "canvasser" in task and "date" in task:
            if task["canvasser"] == session['username'] and task["date"] > today.strftime('%Y-%m-%d'):
                j = 0
                for location in task["route"]:
                    if location == loc and not task["route"][location][0]:
                        next_location = location
                        task_id = bson.objectid.ObjectId(task['_id'])
                        lat_lng_2 = task["route"][location][1]
                        break
                    previous = location
                    j += 1
                if j == 0:
                    current_location = next_location
                    lat_lng_1 = task["route"][current_location][1]
                else:
                    current_location = previous
                    lat_lng_1 = task["route"][current_location][1]
    location = [lat_lng_1, lat_lng_2]
    return render_template('next_stop.html', next_address=next_location, location=json.dumps(location), task_id=task_id)


@app.route('/enter_results/<campaign_name>/<address>/<task_id>/<flag_>', methods=['GET', 'POST'])
def enter_results(campaign_name, address, task_id, flag_):
    task = mongo.db.tasks.find_one({"_id": bson.objectid.ObjectId(task_id)})
    today = datetime.datetime.now()
    if request.method == "POST":
        campaign = mongo.db.campaigns.find_one({"campaign_name": campaign_name})
        results = mongo.db.results
        question_dict = {}
        i = 0
        for loc in task["route"]:
            if address == loc:
                lat_lng = task["route"][loc][1]
        for question in campaign["questionnaire"]:
            if not request.form.getlist(question):
                question_dict[question] = "NA"
            else:
                question_dict[question] = request.form[question]
            i += 1
        # print(question_dict)
        found = mongo.db.results.find_one({'address': address, 'campaign_name': campaign_name})
        if not request.form.getlist('rating'):
            rating = "0"
        else:
            rating = request.form['rating']
        if not request.form.getlist('question'):
            spoke = "no"
        else:
            spoke = request.form.getlist('question')[0]
        if not found:
            results.insert_one({
                'campaign_name': campaign_name,
                'spoke': spoke,
                'questionnaire': question_dict,
                'rating': rating,
                'address': address,
                'notes': request.form['notes'],
                'task_id': task_id,
                'lat_lng': lat_lng
            })
            task['route'][address][0] = True
            mongo.db.tasks.update_one(
                {'_id': bson.objectid.ObjectId(task_id)},
                {'$set': {
                    'route': task['route']
                }
                })
        else:
            results.replace_one(
                {'address': address},
                {
                    'campaign_name': campaign_name,
                    'spoke': spoke,
                    'questionnaire': question_dict,
                    'rating': rating,
                    'address': address,
                    'notes': request.form['notes'],
                    'task_id': task_id,
                    'lat_lng': lat_lng
                }
            )
        session_user = mongo.db.user_database.find_one({'name': session['username']})
        current_ava_date = session_user["ava_data"]
        tasks = mongo.db.tasks.find()
        tasks_list = []
        lat_lng = []
        current_task = None
        for task in tasks:  # should be modified later
            if "canvasser" in task and "date" in task:
                if task["canvasser"] == session['username'] and task["date"] > today.strftime('%Y-%m-%d'):
                    tasks_list.append(task)
                elif task["canvasser"] == session['username'] and task["date"] == today.strftime('%Y-%m-%d'):
                    current_task = task
                for location in task["route"]:
                    lat_lng.append(task["route"][location][1])
        if current_task:
            tasks_list = [current_task] + tasks_list
        if len(tasks_list) > 0:
            session_user = mongo.db.user_database.find_one({'name': session['username']})
            return render_template("canvasser.html", sessionUser=session_user, ava_date=current_ava_date,
                                   length=len(current_ava_date), repeatdata=0, tasks_info=tasks_list,
                                   campaign_name=tasks_list[0]["campaign_name"], lat_lng=json.dumps(lat_lng))
        else:
            session_user = mongo.db.user_database.find_one({'name': session['username']})
            return render_template("canvasser.html", sessionUser=session_user, ava_date=current_ava_date, length=len(current_ava_date),
                                   repeatdata=0, tasks_info=tasks_list)
    else:
        if not flag_ or flag_ == "False":
            campaign = mongo.db.campaigns.find_one({"campaign_name": campaign_name})
            return render_template("enter_results.html", campaign=campaign, address=address, task_id=task_id)
        else:
            results = mongo.db.results.find_one({'address': address, 'campaign_name': campaign_name})
            campaign = mongo.db.campaigns.find_one({"campaign_name": campaign_name})
            return render_template('update_results.html', route=task['route'], task=task, address=address,
                               campaign=campaign, results=results)


@app.route('/view_upcoming_list/<task_id>', methods=['GET', 'POST'])
def view_upcoming_list(task_id):
    task = mongo.db.tasks.find_one({"_id": bson.objectid.ObjectId(task_id)})
    return render_template('view_upcoming_list.html', route=task['route'], task=task)



@app.route('/to_home')
def to_home():
    login_user = mongo.db.user_database.find_one({'name': session['username']})
    return render_template('role_selection.html', sessionUser=login_user)

@app.route('/editGlobal',  methods=['POST'])
def editGlobal():
    if 'username' not in session:
        return render_template('login.html')
    global visit_duration            # Access the global var
    global average_speed
    global maximum_worktime
    visit_duration = int(request.form['visit_duration'])
    average_speed = int(request.form['average_speed'])
    maximum_worktime = int(request.form['maximum_worktime'])
    print(visit_duration)
    print(average_speed)
    print(maximum_worktime)
    if 'username' in session:
        user = mongo.db.user_database
        users = user.find({})
        count = user.count({})
        account_request = mongo.db.account_request
        account_list = account_request.find()
        session_user=mongo.db.user_database.find_one({'name': session['username']})
        return render_template('home.html', users=account_list, sessionUser=session_user, namevalues=users,
                               number=count,
                               visitD=visit_duration, averageS=average_speed, maxW=maximum_worktime)
        return render_template('redirect.html')


@app.route('/')
def index():
    # if 'username' in session:
    #     users = mongo.db.user_database
    #     login_user = users.find_one({'name': session['username']})
    #     if 'administrator' in login_user['role'] :
    #         user = mongo.db.user_database
    #         users = user.find({})
    #         count = user.count({})
    #         session_user = mongo.db.user_database.find_one({'name': session['username']})
    #         account_request = mongo.db.account_request
    #         account_list = account_request.find()
    #         return render_template('home.html', users=account_list, sessionUser=session_user, namevalues=users,
    #                                number=count,
    #                                visitD=visit_duration, averageS=average_speed, maxW=maximum_worktime)        # elif login_user['role'] == 'canvasser':
    #     #     return render_template("canvasser.html")
    #     session_user = mongo.db.user_database.find_one({'name': session['username']})
    #     return render_template("manager_cam.html", sessionUser=session_user)
    return render_template('login.html')


@app.route('/login', methods=['POST', 'GET'])
def login():
    if 'username' in session:
        login_user = mongo.db.user_database.find_one({'name': session['username']})
        return render_template('role_selection.html', sessionUser=login_user)
    else:
        users = mongo.db.user_database
        login_user = users.find_one({'name': request.form['username']})

    if login_user:
        if request.form['pass'] == login_user['password']:
            session['username'] = request.form['username']
            login_user = mongo.db.user_database.find_one({'name': session['username']})
            return render_template('role_selection.html', sessionUser=login_user)
        flash('The user name/ password is wrong!\nPlease Try it again')
        return render_template('login.html')

    flash('The user name/ password is wrong!')
    # logger.info("# user: "+ request.form['username']+"not found")
    return render_template('login.html')  # redirect back to login page

@app.route('/roleSelection', methods=['POST', 'GET'])
def roleSelection():
    users = mongo.db.user_database
    login_user = users.find_one({'name': session['username']})
    if login_user:
            if request.form['role'] == 'administrator':
                if 'username' in session:
                    user = mongo.db.user_database
                    users = user.find({})
                    count = user.count({})

                    # logger.info("login as administer: " + request.form['username'])

                    account_request = mongo.db.account_request
                    account_list = account_request.find()
                    return render_template('home.html', users=account_list, sessionUser=login_user, namevalues=users,
                                           number=count,
                                           visitD=visit_duration, averageS=average_speed, maxW=maximum_worktime)

            # logger.info("# login as manager:" + request.form['username'])
            elif request.form['role'] == 'manager':

                login_user = mongo.db.user_database.find_one({'name': session['username']})
                return render_template('manager_cam.html', sessionUser=login_user)
            else:
                login_user = mongo.db.user_database.find_one({'name': session['username']})
                return render_template('canvasser.html',sessionUser=login_user)


    # logger.info("# user: "+ request.form['username']+"not found")
    return render_template('redirect.html')  # redirect back to login page



@app.route('/logout')
def logout():
    # logout the username
    session.pop('username', None)
    return redirect(url_for('index'))


@app.route('/admin')
def admin():
    session_user = mongo.db.user_database.find_one({'name': session['username']})
    if 'username' in session:
        user = mongo.db.user_database
        users = user.find({})
        count = user.count({})

        # logger.info("login as administer: " + request.form['username'])
        account_request = mongo.db.account_request
        account_list = account_request.find()
        return render_template('home.html', users=account_list, sessionUser=session_user, namevalues=users, number=count,
                               visitD=visit_duration, averageS=average_speed, maxW=maximum_worktime)


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        users = mongo.db.user_database
        existing_user = users.find_one({'name': request.form['username']})

        if existing_user is None:
            account_request = mongo.db.account_request
            account_request.insert({'name': request.form['username'],
                          'password': request.form['pass'], 'role': [request.form['role']],'ava_data':{}})
            flash('Your application has been sent!')
            return redirect(url_for('index'))
        flash('Please choose another user name!')
    return render_template('register.html')

@app.route('/account', methods=['POST','GET'])
def account():
    if request.method == 'GET':
        account_request = mongo.db.account_request
        account_list = account_request.find()
    else:
        account_request = mongo.db.account_request
        account_list = account_request.find()
        account_modlist = request.form.getlist('account')
        for account_user in account_modlist:
            print('name is ', account_user)
            insert_user=mongo.db.account_request.find_one({'name':account_user})
            mongo.db.user_database.insert_one({'name': insert_user['name'],
                          'password': insert_user['password'], 'role': insert_user['role'],'ava_data':insert_user['ava_data']})
            mongo.db.account_request.delete_one({'name': account_user})

    if 'username' in session:
        user = mongo.db.user_database
        users = user.find({})
        count = user.count({})

        # logger.info("login as administer: " + request.form['username'])
        session_user = mongo.db.user_database.find_one({'name': session['username']})
        return render_template('home.html', users=account_list, sessionUser=session_user, namevalues=users, number=count,
                               visitD=visit_duration, averageS=average_speed, maxW=maximum_worktime)



@app.route('/add', methods=['POST'])
def add():
    if 'username' not in session:
        return render_template('login.html')
    if request.method == 'POST':
        useradd = mongo.db.user_database
        existing_user = useradd.find_one({'name': request.form['username']})

        if existing_user is None and request.form['username'] != None:
            useradd.insert_one({'name': request.form['username'], 'password': request.form['pass'],
                                'role': request.form.getlist('role'), 'ava_data':{}})
            print('test in add:')
            print(visit_duration)
            print(average_speed)
            if 'username' in session:
                user = mongo.db.user_database
                users = user.find({})
                count = user.count({})
                session_user = users.find_one({'name': session['username']})
                account_request = mongo.db.account_request
                account_list = account_request.find()
                return render_template('home.html', users=account_list, sessionUser=session_user, namevalues=users,
                                       number=count,
                                       visitD=visit_duration, averageS=average_speed, maxW=maximum_worktime)
                return redirect(url_for('index'))
        return render_template('redirect.html')


@app.route('/delete', methods=['POST', 'GET'])
def delete():
    if 'username' not in session:
        return render_template('login.html')
    if request.method == 'POST':
        userdelete = mongo.db.user_database
        existing_user = userdelete.find_one({'name': request.form['username']})
        if existing_user:
            existing_id = bson.objectid.ObjectId(existing_user['_id'])
            # print(existing_id)
            campaignExist = mongo.db.campaigns.find()
            for campaign in campaignExist:
                # print(campaign['campaign_name'])
                if 'managers' in campaign:
                    # print('managers exist for ', campaign['campaign_name'] )
                    existing_id = bson.objectid.ObjectId(existing_user['_id'])
                    # print('check each managers id: ', campaignM)
                    # print('check each existing_id: ', str(existing_id))
                    if str(existing_id) in campaign['managers']:
                        print('get through?')
                        return render_template('redirect.html')
                if 'canvassers' in campaign:
                    # print('canvassers exist for ', campaign['campaign_name'])
                    existing_id = bson.objectid.ObjectId(existing_user['_id'])
                    if str(existing_id) in campaign['canvassers']:
                        return render_template('redirect.html')

            userdelete.delete_one({'name': request.form['username']})
            if 'username' in session:
                user = mongo.db.user_database
                users = user.find({})
                count = user.count({})
                session_user = users.find_one({'name': session['username']})

                account_request = mongo.db.account_request
                account_list = account_request.find()
                return render_template('home.html', users=account_list, sessionUser=session_user, namevalues=users,
                                       number=count,
                                       visitD=visit_duration, averageS=average_speed, maxW=maximum_worktime)

            return redirect(url_for('index'))
        return render_template('redirect.html')


@app.route('/editUser', methods=['POST', 'GET'])
def editUser():
    if 'username' not in session:
        return render_template('login.html')
    if request.method == 'POST':
        useredit = mongo.db.user_database
        existing_user = useredit.find_one({'name': request.form['username']})

        if existing_user:
            user_ori = useredit.find_one({'name': request.form['username']})

            correct_name = request.form['username']

            # check if new username is different from original username
            if request.form['newusername'] != "":
                correct_name = request.form['newusername']
                # print(userOri['password'])
                # print('testsssss')
                if request.form['username'] != request.form['newusername']:
                    useredit.find_one_and_update({'name': request.form['username']},
                                                 {"$set": {'name': correct_name}})
                    user_ori = useredit.find_one({'name': request.form['newusername']})
                    correct_name = request.form['newusername']
            # check if new password is different from original password
            if request.form['newpass'] != "":
                if request.form['newpass'] != user_ori['password']:
                    useredit.find_one_and_update({'name': correct_name},
                                                 {"$set": {'password': request.form['newpass']}})
            # check the difference between new user type(role) and original user type.
            if request.form.getlist('newrole') != []:
                useredit.find_one_and_update({'name': correct_name},
                                                 {"$set": {'role': request.form.getlist('newrole')}})
                if 'canvasser' in request.form.getlist('newrole'):
                    useredit.find_one_and_update({'name': correct_name}, {"$set": {'ava_data': {}}})
            # check the difference between new average speed and original average peed for canvasser.
            # if request.form['newavespeed'] != "":
            #     if request.form['newavespeed'] != user_ori['avespeed']:
            #         useredit.find_one_and_update({'name': correct_name},
            #                                      {"$set": {'avespeed': request.form['newavespeed']}})

            if 'username' in session:
                user = mongo.db.user_database
                users = user.find({})
                count = user.count({})
                session_user = mongo.db.user_database.find_one({'name': session['username']})

                account_request = mongo.db.account_request
                account_list = account_request.find()
                return render_template('home.html', users=account_list, sessionUser=session_user, namevalues=users,
                                       number=count,
                                       visitD=visit_duration, averageS=average_speed, maxW=maximum_worktime)

            return redirect(url_for('index'))
        return render_template('redirect.html')



################
# Jin Chen
################

# canvasser
@app.route('/canvasser', methods=['GET', 'POST'])
def canvasser():
    session_user = mongo.db.user_database.find_one({'name': session['username']})
    task = mongo.db.tasks.find_one({"canvasser": session['username']})
    # print(campaign)
    if 'username' not in session:
        return render_template('login.html')
    if request.method == 'POST':
        users = mongo.db.user_database
        existing_user = users.find_one({'name': session['username']})
        current_ava_date = existing_user["ava_data"]
        if str(request.form['aday']) in current_ava_date or request.form['aday'] == "":
            return render_template("canvasser.html", sessionUser=existing_user, ava_date=current_ava_date, length=len(current_ava_date),
                                   repeatdata=1, campaign_info=task, request=request)
        current_ava_date[str(request.form['aday'])] = True
        users.find_one_and_update({'name': session['username']}, {"$set": {'ava_data': current_ava_date}})
        return render_template("canvasser.html", sessionUser=existing_user, ava_date=current_ava_date, length=len(current_ava_date), repeatdata=0,
                               campaign_info=task, request=request)
    else:
        users = mongo.db.user_database
        existing_user = users.find_one({'name': session['username']})
        # date_list = existing_user["ava_data"]
        current_ava_date = []
        today = datetime.datetime.now()
        for key in existing_user["ava_data"]:
            if existing_user["ava_data"][key] and key >= today.strftime('%Y-%m-%d'):
                current_ava_date.append(key)
        tasks = mongo.db.tasks.find()
        tasks_list = []
        current_task = None
        for task in tasks:  # should be modified later
            if "canvasser" in task and "date" in task:
                if task["canvasser"] == session['username'] and task["date"] > today.strftime('%Y-%m-%d'):
                    tasks_list.append(task)
                elif task["canvasser"] == session['username'] and task["date"] == today.strftime('%Y-%m-%d'):
                    current_task = task
        if current_task:
            tasks_list = [current_task] + tasks_list
        if len(tasks_list) > 0:
            return render_template("canvasser.html", sessionUser=existing_user, ava_date=current_ava_date,
                                   length=len(current_ava_date), repeatdata=0, tasks_info=tasks_list,
                                   campaign_name=tasks_list[0]["campaign_name"], session_user=session_user)
        else:
            return render_template("canvasser.html", sessionUser=existing_user, ava_date=current_ava_date, length=len(current_ava_date),
                                   repeatdata=0, tasks_info=tasks_list, session_user=session_user)


@app.route('/view_result/<address>', methods=['GET'])
def view_result(address):
    session_user = mongo.db.user_database.find_one({'name': session['username']})
    results = mongo.db.results.find_one({"address": address})
    return render_template("view_result.html", results=results, request=request,session_user=session_user)


@app.route('/add_date', methods=['GET', 'POST'])
def add_date():
    session_user = mongo.db.user_database.find_one({'name': session['username']})
    campaign = mongo.db.tasks.find_one({"canvasser": session['username']})
    if 'username' not in session:
        return render_template('login.html')
    if request.method == 'POST':
        users = mongo.db.user_database
        existing_user = users.find_one({'name': session['username']})
        current_avadate = existing_user["ava_data"]
        current_avadate[str(request.form['aday'])] = True
        users.find_one_and_update({'name': session['username']},
                                  {"$set": {'ava_data': current_avadate}})
        return render_template("add_date.html", ava_date=current_avadate, length=len(current_avadate), repeatdata=0,
                               campaign_info=campaign)
    else:
        users = mongo.db.user_database
        existing_user = users.find_one({'name': session['username']})
        # date_list = existing_user["ava_data"]
        current_avadata = []
        today = datetime.datetime.now()
        for key in existing_user["ava_data"]:
            if existing_user["ava_data"][key] and key >= today.strftime('%Y-%m-%d'):
                current_avadata.append(key)
        tasks = mongo.db.tasks.find()
        tasks_list = []
        current_task = None
        for task in tasks:
            if "canvasser" in task and "date" in task:
                if task["canvasser"] == session['username'] and task["date"] > today.strftime('%Y-%m-%d'):
                    tasks_list.append(task)
                elif task["canvasser"] == session['username'] and task["date"] == today.strftime('%Y-%m-%d'):
                    current_task = task
        if current_task:
            tasks_list = [current_task] + tasks_list
        if len(tasks_list) > 0:
            return render_template("add_date.html", ava_date=current_avadata, length=len(current_avadata),
                                   repeatdata=0, tasks_info=tasks_list,
                                   request=request, session_user=session_user)
        else:
            return render_template("add_date.html", ava_date=current_avadata, length=len(current_avadata),
                                   repeatdata=0, tasks_info=tasks_list, session_user=session_user)


@app.route('/delete_date', methods=['GET', 'POST'])
def delete_date():
    session_user = mongo.db.user_database.find_one({'name': session['username']})
    campaign = mongo.db.tasks.find_one({"canvasser": session['username']})
    today = datetime.datetime.now()
    if 'username' not in session:
        return render_template('login.html')
    if request.method == 'POST':
        users = mongo.db.user_database
        existing_user = users.find_one({'name': session['username']})
        current_avadata = existing_user["ava_data"]
        deleted_date = request.form.getlist('delete_date')
        # logger.info(session['username'] + " delete avaliable date")
        for i in list(current_avadata):
            for j in deleted_date:
                if i == j and current_avadata[i]:
                    del current_avadata[i]
        current_av_date = {}
        for key in current_avadata:
            if current_avadata[key] and key >= today.strftime('%Y-%m-%d'):
                current_av_date[key] = True
        users.find_one_and_update({'name': session['username']}, {"$set": {'ava_data': current_av_date}})
        return render_template("delete_date.html", ava_date=current_av_date, length=len(current_av_date), repeatdata=0, campaign_info=campaign,session_user=session_user)
    else:
        users = mongo.db.user_database
        existing_user = users.find_one({'name': session['username']})
        # date_list = existing_user["ava_data"]
        current_avadata = []
        for key in existing_user["ava_data"]:
            if existing_user["ava_data"][key] and key >= today.strftime('%Y-%m-%d'):
                current_avadata.append(key)
        return render_template("delete_date.html", ava_date=current_avadata, session_user=session_user)


'''
Below is campaign.py
'''


@app.route('/Camp')
def Camp():
    session_user = mongo.db.user_database.find_one({'name': session['username']})
    return render_template("manager_cam.html", sessionUser=session_user)


@app.route('/create', methods=['GET', 'POST'])      # whatever web-page you wanna connect
def create():
    session_user = mongo.db.user_database.find_one({'name': session['username']})
    if request.method == 'GET':
        user = mongo.db.user_database
        users = list(user.find())
        return render_template("create_campaign.html", users=users, session_user=session_user)
    else:
        campaigns = mongo.db.campaigns
        user = mongo.db.user_database
        users = list(user.find())
        location_list = []
        for location in request.form.getlist('address'):
            search_payload = {"key": key, "query": location}
            search_req = requests.get(search_url, params=search_payload)
            search_json = search_req.json()  # json representation of the data
            loc = location.replace(".", "")
            sub_loc = (loc, search_json["results"][0]["geometry"]["location"])
            location_list.append(sub_loc)

        if request.form['campaign_name'] and request.form['dates']\
                and request.form['talk_p'] and request.form.getlist('address')\
                and [request.form['v_b'], request.form['v_e']]\
                and request.form.getlist('Que') and request.form.getlist('canvasser')\
                and request.form.getlist('manager'):

            campaigns.insert({
                'campaign_name': request.form['campaign_name'],
                'visit_duration': float(request.form['dates']),
                'talking_points': request.form['talk_p'],
                'location': location_list,
                'duration': [request.form['v_b'], request.form['v_e']],
                'questionnaire': request.form.getlist('Que'),
                'managers': request.form.getlist('manager'),
                'canvassers': request.form.getlist('canvasser'),
                          })

            flash(request.form['campaign_name']+' was created successfully!')
            return render_template("create_campaign.html", users=users, session_user=session_user)
        else:
            # flash('You must fill in all the blocks!')
            return render_template("create_campaign.html", users=users, session_user=session_user)


@app.route('/view')
def view():
    session_user = mongo.db.user_database.find_one({'name': session['username']})
    if session_user:
        users = mongo.db.user_database
        users = list(users.find())
        campaigns = mongo.db.campaigns.find()
        return render_template("view_campaign.html", campaigns=campaigns, users=users, session_user=session_user)
    return redirect(url_for('index'))


@app.route('/edit')
def edit():
    session_user = mongo.db.user_database.find_one({'name': session['username']})
    if session_user:
        campaigns = mongo.db.campaigns.find()
        return render_template("show_camp_list.html", campaigns=campaigns, session_user=session_user)
    return redirect(url_for('index'))


@app.route('/result')
def result():
    session_user = mongo.db.user_database.find_one({'name': session['username']})
    if session_user:
        results = mongo.db.results.find()
        return render_template("view_camp_result.html", results=results, session_user=session_user)
    return redirect(url_for('index'))

@app.route('/table_result')
def table_result():
    session_user = mongo.db.user_database.find_one({'name': session['username']})
    campaign_list = []
    user = session['username']
    manager = list(mongo.db.user_database.find({"name" : user}))[0]['_id']

    campaigns = list(mongo.db.campaigns.find())

    for i in campaigns:
        if str(manager) not in i['managers']:
            campaigns.remove(i)
    for i in campaigns:
        if str(manager) not in i['managers']:
            campaigns.remove(i)
    for i in campaigns:
        if str(manager) not in i['managers']:
            campaigns.remove(i)

    for i in campaigns:
        campaign_list.append(i['campaign_name'])


    results = list(mongo.db.results.find())
    for i in results:
        if i['campaign_name'] not in campaign_list:
            results.remove(i)

    return render_template("view_camp_table_result.html", results=results, session_user=session_user)


@app.route('/statistical_result')
def statistical_result():
    session_user = mongo.db.user_database.find_one({'name': session['username']})
    rate_dic={}
    answer_dic = {}
    answer_sub_dic = {}
    results = list(mongo.db.results.find())
    for i in results:

        if i['campaign_name'] in rate_dic.keys():

            rate_dic[i['campaign_name']].append(float(i['rating']))
        else:
            rate_dic[i['campaign_name']] = [float(i['rating'])]
    for i in rate_dic:
        rate_dic[i] = [(float(sum(rate_dic[i])) / max(len(rate_dic[i]), 1))]
        if len(rate_dic[i]) == 1:
            rate_dic[i].append(0)
        else:
            rate_dic[i].append(statistics.stdev(rate_dic[i]))

    for i in results:

        answer_dic[i['campaign_name']] = {}
        for j in i['questionnaire']:
            if j in answer_sub_dic.keys():
                answer_sub_dic[j].append(i['questionnaire'][j].lower())
            else:
                answer_sub_dic[j] = [i['questionnaire'][j].lower()]
        answer_dic[i['campaign_name']] = answer_sub_dic

    dict = {}

    for i in answer_dic:
        dict[i]={}
        for j in answer_dic[i]:
            dict[i][j] = answer_dic[i][j].count('yes')/len(answer_dic[i][j])

    # logger.info("view campaign statistical_result")
    return render_template("view_camp_statistical_result.html", rate_dic=rate_dic, answer_dic=dict,
                           session_user=session_user)



@app.route('/visual_result')
def visual_result():
    session_user = mongo.db.user_database.find_one({'name': session['username']})
    if session_user:
        result = list(mongo.db.results.find())
        campaign_list=[]
        for i in result:
            if i['campaign_name'] in campaign_list:
                continue
            else:
                campaign_list.append(i['campaign_name'])
        return render_template('view_camp_list_result.html',campaign_list = campaign_list,session_user=session_user)
    return redirect(url_for('index'))


@app.route('/visual_result_map/<campaign_name>')
def visual_result_map(campaign_name):
    result = mongo.db.results.find({"campaign_name": campaign_name})
    sequence_list = []
    for i in result:
        sequence_list.append((i['lat_lng'], i['rating']))

    n = len(sequence_list)
    for i in range(n):
        for j in range(0, n - i - 1):
            if sequence_list[j][1] > sequence_list[j + 1][1]:
                sequence_list[j], sequence_list[j + 1] = sequence_list[j + 1], sequence_list[j]

    for i in range(len(sequence_list)):
        sequence_list[i] = sequence_list[i][0]
    print(sequence_list)
    return render_template('view_camp_visual_result.html', location=json.dumps(sequence_list))


@app.route('/edit_campaigns/<campaign_name>')
def edit_campaigns(campaign_name):
    session_user = mongo.db.user_database.find_one({'name': session['username']})
    campaign = mongo.db.campaigns.find_one({"campaign_name": campaign_name})
    users = mongo.db.user_database
    users = list(users.find())
    location_list = []
    for loc in campaign["location"]:
        location_list.append(loc[0])
    return render_template("edit_camp.html", campaign=campaign, users=users, session_user=session_user, location_list=location_list)


@app.route('/update_camp_info/<campaign_name>', methods=['GET', 'POST'])
def update_camp_info(campaign_name):
    # if request.method == 'POST':
        session_user = mongo.db.user_database.find_one({'name': session['username']})
        campaign = mongo.db.campaigns

        location_list = []
        for location in request.form.getlist('address'):
            search_payload = {"key": key, "query": location}
            search_req = requests.get(search_url, params=search_payload)
            search_json = search_req.json()  # json representation of the data
            loc = location.replace(".", "")
            sub_loc = (loc, search_json["results"][0]["geometry"]["location"])
            location_list.append(sub_loc)
        campaign.replace_one(
            {'campaign_name': campaign_name},
            {
                'campaign_name': request.form['campaign_name'],
                'visit_duration': float(request.form['dates']),
                'talking_points': request.form['talk_p'],
                'location': location_list,
                'duration': [request.form['v_b'], request.form['v_e']],
                'questionnaire': request.form.getlist('Que'),
                'managers': request.form.getlist('manager'),
                'canvassers': request.form.getlist('canvasser')
            }
        )
        flash(campaign_name + ' has been changed!')
        campaigns = mongo.db.campaigns.find()
        return render_template("show_camp_list.html", campaigns=campaigns, session_user=session_user)
    # else:
    #     return render_template("edit_campaign.html", campaign=campaign, users=users, session_user=session_user)


@app.route('/viewLocationsOnMap/<campaign_name>')
def view_locations_on_map(campaign_name):
    campaign = mongo.db.campaigns.find_one({"campaign_name": campaign_name})
    location = []
    for loc in campaign['location']:
        location.append(loc[1])
    return render_template('location_map.html', location=json.dumps(location))


@app.route('/view_locations_on_map_canvasser/<task_id>')
def view_locations_on_map_canvasser(task_id):
    task = mongo.db.tasks.find_one({"_id": bson.objectid.ObjectId(task_id)})
    lat_lng = []
    for location in task["route"]:
        lat_lng.append(task["route"][location][1])
    return render_template('location_map.html', location=json.dumps(lat_lng))


@app.route('/tasks_detail/<_id>')
def tasks_detail(_id):
    session_user = mongo.db.user_database.find_one({'name': session['username']})
    task = mongo.db.tasks.find_one({"_id": bson.objectid.ObjectId(_id)})
    return render_template("tasks_detail.html", task=task, session_user=session_user)


@app.route('/view_task/<campaign_name>')
def view_task(campaign_name):
    session_user = mongo.db.user_database.find_one({'name': session['username']})
    if session_user:
        campaign = mongo.db.campaigns.find_one({"campaign_name": campaign_name})
        tasks = mongo.db.tasks
        tasks = list(tasks.find())
        return render_template("task_list.html", campaign=campaign, tasks=tasks,session_user=session_user)
    return redirect(url_for('index'))


@app.route('/assign_task/<_id>/<campaign>')
def assign_task(_id, campaign):
    session_user = mongo.db.user_database.find_one({'name': session['username']})
    if session_user:
        task = mongo.db.tasks.find_one({"_id": bson.objectid.ObjectId(_id)})
        campaign = mongo.db.campaigns.find_one({"campaign_name": campaign})
        users = mongo.db.user_database
        users = list(users.find())
        return render_template("assign_task.html", task=task, users=users, campaign=campaign, session_user=session_user)
    return redirect(url_for('index'))


@app.route('/assign_task_to_user/<user>/<date>/<task>/<campaign_name>')
def assign_task_to_user(user, date, task, campaign_name):
    session_user = mongo.db.user_database.find_one({'name': session['username']})
    if session_user:
        mongo.db.tasks.update_one({
            '_id': bson.objectid.ObjectId(task)}, {
            '$set': {
                'canvasser': user,
                'date': date
            }
        })
        user = mongo.db.user_database.find_one({"name": user})
        user['ava_data'][date] = False
        mongo.db.user_database.update_one({
            '_id': user['_id']}, {
            '$set': {
                'ava_data': user['ava_data']
            }
        })
        campaign = mongo.db.campaigns.find_one({"campaign_name": campaign_name})
        tasks = mongo.db.tasks
        tasks = list(tasks.find())
        return render_template("task_list.html", campaign=campaign, tasks=tasks, session_user=session_user)
    return redirect(url_for('index'))


@app.route('/renew_task/<task>/<begin_point>')
def renew_task(task, begin_point):
    session_user = mongo.db.user_database.find_one({'name': session['username']})
    today = datetime.datetime.now()
    task = mongo.db.tasks.find_one({'_id': bson.objectid.ObjectId(task)})
    campaign = mongo.db.campaigns.find_one({'campaign_name': task['campaign_name']})
    locations = [(task['route'][begin_point][1]['lat'], task['route'][begin_point][1]['lng'])]
    locs = [begin_point]
    for loc in task['route']:
        if task['route'][loc][0] is False:
            locs.append(loc)
            locations.append((task['route'][loc][1]['lat'], task['route'][loc][1]['lng']))
    task_num = 1
    data = create_data_model(locations, task_num)
    routing = pywrapcp.RoutingModel(
        data["num_locations"],
        data["num_vehicles"],
        data["depot"]
    )
    stop_point, assignment, routing = organize_task(routing, data, campaign['visit_duration'])
    route_list = get_task_list(data, routing, assignment)
    d = "%.2f" % round(route_list[0][1], 2)
    loc_list = {}
    for loc in task['route']:
        if task['route'][loc][0]:
            loc_list[loc] = task['route'][loc]
    for sub in route_list:
        for i in sub[0]:
            loc_list[locs[i]] = (False, task['route'][locs[i]][1])
    mongo.db.tasks.update_one({
        '_id': task['_id']}, {
        '$set': {
            'route': loc_list,
            'duration': d
        }
    })
    # task = mongo.db.tasks.find_one({"canvasser": session['username']})
    users = mongo.db.user_database
    existing_user = users.find_one({'name': session['username']})
    current_avadata = existing_user["ava_data"]
    tasks = mongo.db.tasks.find()
    tasks_list = []
    current_task = None
    for task in tasks:
        if "canvasser" in task and "date" in task:
            if task["canvasser"] == session['username'] and task["date"] > today.strftime('%Y-%m-%d'):
                tasks_list.append(task)
            elif task["canvasser"] == session['username'] and task["date"] == today.strftime('%Y-%m-%d'):
                current_task = task
    if current_task:
        tasks_list = [current_task] + tasks_list

    flash('New route has been created!\nThe duration of the rest  route is ' + str(d) + '.')
    session_user = mongo.db.user_database.find_one({'name': session['username']})
    return render_template("canvasser.html", sessionUser=session_user, ava_date=current_avadata, length=len(current_avadata), repeatdata=0, tasks_info=tasks_list,session_user=session_user)
    # Setting first solution heuristic (cheapest addition).


@app.route('/createTask/<campaign_name>')
def create_task(campaign_name):
    session_user = mongo.db.user_database.find_one({'name': session['username']})
    campaign = mongo.db.campaigns.find_one({"campaign_name": campaign_name})
    locations = [(0, 0)]
    for loc in campaign['location']:
        locations.append((loc[1]['lat'], loc[1]['lng']))
    num_locations = len(locations)

    max_distance = 0
    for i in range(1, num_locations-1):
        max_distance += manhattan_distance(locations[i], locations[i+1])
    max_distance += manhattan_distance(locations[1], locations[-1])
    possible_time = max_distance / average_speed + num_locations * campaign['visit_duration']
    task_num = math.ceil(possible_time / maximum_worktime)
    if task_num > num_locations:
        task_num = num_locations
    last_route_list = None
    flag = True
    while flag:
        data = create_data_model(locations, task_num)
        routing = pywrapcp.RoutingModel(
            data["num_locations"],
            data["num_vehicles"],
            data["depot"]
        )
        stop_point, assignment, routing = organize_task(routing, data, campaign['visit_duration'])
        if stop_point is 1 and task_num != 1:
            route_list = get_task_list(data, routing, assignment)
            for time in route_list:
                print('time.', time[1])
                if time[1] > maximum_worktime:
                    print('time.',time[1])
                    flag = False
            if flag:
                last_route_list = route_list
                task_num -= 1
        elif stop_point is 1 and task_num is 1:
            route_list = get_task_list(data, routing, assignment)
            for time in route_list:
                print('time.', time[1])
                if time[1] > maximum_worktime:
                    print('time.',time[1])
                    flag = False
            if flag:
                last_route_list = route_list

            break
        else:
            break
    if last_route_list is None:
        print('hello')
        task_num += 1
        flag = True
        while flag:
            data = create_data_model(locations, task_num)
            routing = pywrapcp.RoutingModel(
                data["num_locations"],
                data["num_vehicles"],
                data["depot"]
            )
            stop_point, assignment, routing = organize_task(routing, data, campaign['visit_duration'])
            print('task_num',task_num)
            if stop_point is 1:
                flag = False
                last_route_list = get_task_list(data, routing, assignment)
                for time in last_route_list:
                    print('hi')
                    print(time)
                    if time[1] > maximum_worktime:
                        flag = True
                if flag:
                    task_num += 1
            else:
                task_num += 1
    # count for ava canvasser
    ava_time = []
    for can in campaign['canvassers']:
        canvasser = mongo.db.user_database.find_one({"_id": bson.objectid.ObjectId(can)})
        for date in canvasser['ava_data']:
            if (date >= campaign['duration'][0]) and (date <= campaign['duration'][1]) and canvasser['ava_data'][date]:
                ava_time.append((canvasser['name'], date))
# create task
    tasks = mongo.db.tasks
    loc = campaign['location']
    ava_num = len(ava_time)-1
    task_list = []
    for task in last_route_list:
        task_loc = {}
        for i in task[0]:
            if i != 0 :
                task_loc[loc[i-1][0]] = (False, loc[i-1][1])
        # name of location
        count = 0
        d = "%.2f" % round(task[1], 2)
        count += 1
        if ava_num != -1:
            _id = tasks.insert({
                'campaign_name': campaign_name,
                'route': task_loc,
                'loc_num': len(task_loc),
                'duration': d,
                'canvasser': ava_time[i][0],
                'date': ava_time[i][1]
            })
            # disable the used canvasser
            user = mongo.db.user_database.find_one({"name": ava_time[i][0]})
            user['ava_data'][ava_time[i][1]] = False
            mongo.db.user_database.update_one({
                '_id': user['_id']}, {
                '$set': {
                    'ava_data': user['ava_data']
                }
            })
            ava_num -= 1
        else:
            _id = tasks.insert({
                'campaign_name': campaign_name,
                'route': task_loc,
                'loc_num': len(task_loc),
                'duration': d
            })
        task_list.append(_id)

    mongo.db.campaigns.update_one({
        '_id': campaign['_id']}, {
        '$set': {
            'tasks': task_list
        }
    })
    #
    flash('The tasks of ' + campaign_name + ' were created successfully!')
    campaigns = mongo.db.campaigns.find()
    return render_template("show_camp_list.html", campaigns=campaigns, session_user=session_user)
    # Setting first solution heuristic (cheapest addition).


def create_data_model(_locations, num):
    """Stores the data for the problem"""
    data = {}
    data["locations"] = _locations
    data["num_locations"] = len(data["locations"])
    data["num_vehicles"] = num
    data["depot"] = 0
    return data


def organize_task(routing, data, visit_duration):
    distance_callback = create_distance_callback(data, visit_duration)
    routing.SetArcCostEvaluatorOfAllVehicles(distance_callback)
    add_distance_dimension(routing,distance_callback)
    search_parameters = pywrapcp.RoutingModel.DefaultSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)  # pylint: disable=no-member
    # Solve the problem.
    search_parameters.time_limit_ms = 3000
    try:
        assignment = routing.SolveWithParameters(search_parameters)
    except:
        pass
    return routing.status(), assignment, routing


def create_distance_callback(data, visit_duration):
    """Creates callback to return distance between points."""
    global _distance
    _distance = {}

    for from_node in range(data["num_locations"]):
        _distance[from_node] = {}
        for to_node in range(data["num_locations"]):
            if from_node * to_node is 0:
                _distance[from_node][to_node] = 0
            elif from_node == to_node:
                _distance[from_node][to_node] = visit_duration
            else:
                _distance[from_node][to_node] = (
                    manhattan_distance(data["locations"][from_node],
                        data["locations"][to_node])/average_speed + visit_duration)

    def distance_callback(from_node, to_node):
        """Returns the manhattan distance between the two nodes"""
        return _distance[from_node][to_node]
    return distance_callback


def manhattan_distance(position_1, position_2):
    """Computes the Manhattan distance between two points"""
    return lat_lon_distance(position_1[0], position_1[1], position_2[0], position_1[1]) + \
        lat_lon_distance(position_1[0], position_1[1], position_1[0], position_2[1])


def lat_lon_distance(lat1, lon1, lat2, lon2):
    r = 6373.0
    d_lon = radians(lon2) - radians(lon1)
    d_lat = radians(lat2) - radians(lat1)
    a = sin(d_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(d_lon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return r * c


def add_distance_dimension(routing, distance_callback):
    """Add Global Span constraint"""
    distance = 'Distance'
    # Maximum distance per vehicle.
    routing.AddDimension(
        distance_callback,
        0,  # null slack
        maximum_worktime,
        True,  # start cumul to zero
        distance)
    distance_dimension = routing.GetDimensionOrDie(distance)
    # Try to minimize the max distance among vehicles.
    distance_dimension.SetGlobalSpanCostCoefficient(100)


def get_task_list(data, routing, assignment):
    """Print routes on console."""
    node_list = []
    for vehicle_id in range(data["num_vehicles"]):
        index = routing.Start(vehicle_id)
        node_sublist = []
        while not routing.IsEnd(index):
            node_sublist.append(routing.IndexToNode(index))
            index = assignment.Value(routing.NextVar(index))
        node_sublist.append(routing.IndexToNode(index))

        duration = visit_duration
        from_node = node_sublist[0]
        for i in range(0, len(node_sublist)):
            to_node = node_sublist[i]
            duration += _distance[from_node][to_node]
            from_node = to_node
        node_list.append((node_sublist, duration))
    return node_list


if __name__ == '__main__':
    app.secret_key = 'sekret'
    app.debug = True
    app.run()
