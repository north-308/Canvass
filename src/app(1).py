from __future__ import print_function
from six.moves import xrange
from ortools.constraint_solver import pywrapcp
from ortools.constraint_solver import routing_enums_pb2
from math import sin, cos, sqrt, atan2, radians

from flask import Flask, render_template, url_for, request, session, redirect
from flask_pymongo import PyMongo

import requests
import json
import bson

from key import key

######### Global Value ############
visit_duration = 1
average_speed = 70
######### Global Value ############

app = Flask(__name__)
# connection for database
app.config['MONGO_DBNAME'] = 'canvassing_db'
app.config['MONGO_URI'] = 'mongodb://songyy:cse308@ds125953.mlab.com:25953/canvassing_db'

mongo = PyMongo(app)  # instantiate the db connection
search_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"   # either json or xml
details_url = "https://maps.googleapis.com/maps/api/place/details/json"


###logger###
# class NoParsingFilter(logging.Filter):
#     def filter(self, record):
#         return "GET" not in record.getMessage() and "POST" not in record.getMessage()
# logger = logging.getLogger()
# logger.setLevel(logging.DEBUG)
# fh = logging.FileHandler("none.log", mode='w')
# fh.setLevel(logging.DEBUG)
# formatter = logging.Formatter("%(levelname)s %(asctime)s = %(message)s")
# fh.setFormatter(formatter)
# fh.addFilter(NoParsingFilter())
# logger.addHandler(fh)
@app.route('/editGlobal',  methods=['POST'])
def editGlobal():
    if 'username' not in session:
        return render_template('login.html')
    global visit_duration            # Access the global var
    global average_speed
    visit_duration = request.form['visit_duration']
    average_speed = request.form['average_speed']
    print(visit_duration)
    print(average_speed)
    if 'username' in session:
        user = mongo.db.user_database
        users = user.find({})
        count = user.count({})
        return render_template('home.html', namevalues=users, number=count, visitD=visit_duration, averageS=average_speed)
    return render_template('redirect.html')

@app.route('/')
def index():
    if 'username' in session:
        users = mongo.db.user_database
        login_user = users.find_one({'name': session['username']})
        if login_user['role'] == 'administrator':
            user = mongo.db.user_database
            users = user.find({})
            count = user.count({})
            return render_template('home.html', namevalues=users, number=count, visitD=visit_duration, averageS=average_speed)
        return render_template("manager_cam.html")

    return render_template('login.html')


@app.route('/login', methods=['POST', 'GET'])
def login():
    users = mongo.db.user_database
    login_user = users.find_one({'name': request.form['username']})

    if login_user:
        if request.form['pass'] == login_user['password'] and request.form['role'] \
                == login_user['role']:
            session['username'] = request.form['username']
            if request.form['role'] == 'administrator':

                session['username'] = request.form['username']
                if 'username' in session:
                    user = mongo.db.user_database
                    users = user.find({})
                    count = user.count({})

                    # logger.info("login as administer: " + request.form['username'])

                    return render_template('home.html', namevalues=users, number=count, visitD=visit_duration, averageS=average_speed)
                return redirect(url_for('index'))

            # logger.info("# login as manager:" + request.form['username'])
            elif request.form['role'] == 'manager':

                session['username'] = request.form['username']
                return render_template('manager_cam.html')
            else:
                session['username'] = request.form['username']
                return redirect(url_for('canvasser'))


    # logger.info("# user: "+ request.form['username']+"not found")
    return render_template('redirect.html')  # redirect back to login page



@app.route('/logout')
def logout():
    # logout the username
    session.pop('username', None)
    return redirect(url_for('index'))


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        users = mongo.db.user_database
        existing_user = users.find_one({'name': request.form['username']})

        if existing_user is None and request.form['key'] == 'cse308':

            users.insert({'name': request.form['username'],
                          'password': request.form['pass'], 'role': request.form['role']})
            session['username'] = request.form['username']
            if 'username' in session:
                user = mongo.db.user_database
                users = user.find({})
                count = user.count({})

                return render_template('home.html', namevalues=users, number=count, visitD=visit_duration, averageS=average_speed)
            return redirect(url_for('index'))

        return 'Username Already Exists'

    return render_template('register.html')


@app.route('/add', methods=['POST'])
def add():
    if 'username' not in session:
        return render_template('login.html')
    if request.method == 'POST':
        useradd = mongo.db.user_database
        existing_user = useradd.find_one({'name': request.form['username']})

        if existing_user is None:
            useradd.insert_one({'name': request.form['username'], 'password': request.form['pass'],
                                'role': request.form['role']})
            print('test in add:')
            print(visit_duration)
            print(average_speed)
            if 'username' in session:
                user = mongo.db.user_database
                users = user.find({})
                count = user.count({})
                return render_template('home.html', namevalues=users, number=count, visitD=visit_duration, averageS=average_speed)
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
            userdelete.delete_one({'name': request.form['username']})
            if 'username' in session:
                user = mongo.db.user_database
                users = user.find({})
                count = user.count({})
                return render_template('home.html', namevalues=users, number=count, visitD=visit_duration, averageS=average_speed)
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
            if request.form['newrole'] != "":
                if request.form['newrole'] != user_ori['role']:
                    useredit.find_one_and_update({'name': correct_name},
                                                 {"$set": {'role': request.form['newrole']}})
            # check the difference between new average speed and original average peed for canvasser.
            # if request.form['newavespeed'] != "":
            #     if request.form['newavespeed'] != user_ori['avespeed']:
            #         useredit.find_one_and_update({'name': correct_name},
            #                                      {"$set": {'avespeed': request.form['newavespeed']}})

            if 'username' in session:
                user = mongo.db.user_database
                users = user.find({})
                count = user.count({})
                return render_template('home.html', namevalues=users, number=count, visitD=visit_duration, averageS=average_speed)
            return redirect(url_for('index'))
        return render_template('redirect.html')


'''
Below is campaign.py
'''
@app.route('/Camp')
def Camp():
    # if 'username' not in session:
    #     return render_template('login.html')
    return render_template("manager_cam.html")


@app.route('/create', methods=['GET', 'POST'])      #whatever webpage you wanna connect
def create():
    # if 'username' not in session:
    #     return render_template('login.html')
    if request.method == 'GET':
        user = mongo.db.user_database
        users = list(user.find())
        return render_template("create_camaign.html", users=users)
    else:
        campaigns = mongo.db.campaigns
        campaigns.insert({
            'campaign_name': request.form['campaign_name'],
            'dates': request.form['dates'],
            'talking_points': request.form['talk_p'],
            'location': request.form.getlist('address'),
            'duration': [request.form['v_b'], request.form['v_e']],
            'questionnaire': request.form.getlist('Que'),
            'managers': request.form.getlist('manager'),
            'canvassers': request.form.getlist('canvasser'),
                      })
        return redirect(url_for('Camp'))


@app.route('/view')
def view():
    # if 'username' not in session:
    #     return render_template('login.html')
    users = mongo.db.user_database
    users = list(users.find())
    campaigns = mongo.db.campaigns.find()
    return render_template("view_campaign.html", campaigns=campaigns, users=users)



@app.route('/edit')
def edit():
    # if 'username' not in session:
    #     return render_template('login.html')
    campaigns = mongo.db.campaigns.find()
    return render_template("show_camp_list.html", campaigns=campaigns)


@app.route('/edit_campaigns/<campaign_name>')
def edit_campaigns(campaign_name):
    # if 'username' not in session:
    #     return render_template('login.html')
    campaign = mongo.db.campaigns.find_one({"campaign_name": campaign_name})
    users = mongo.db.user_database
    users = list(users.find())
    return render_template("edit_camp.html", campaign=campaign, users=users)


@app.route('/update_camp_info/<campaign_name>', methods=['GET', 'POST'])
def update_camp_info(campaign_name):
    # if 'username' not in session:
    #     return render_template('login.html')
    if request.method == 'POST':
        campaign = mongo.db.campaigns
        campaign.replace_one(
            {'campaign_name': campaign_name},
            {
                'campaign_name': request.form['campaign_name'],
                'dates': request.form['dates'],
                'talking_points': request.form['talk_p'],
                'location': request.form.getlist('address'),
                'duration': [request.form['v_b'], request.form['v_e']],
                'questionnaire': request.form.getlist('Que'),
                'managers': request.form.getlist('manager'),
                'canvassers': request.form.getlist('canvasser')
            }
        )
        return redirect(url_for('Camp'))
    else:
        return render_template("create_campaign.html")

@app.route('/viewLocationsOnMap/<campaign_name>')
def view_locations_on_map(campaign_name):
    # if 'username' not in session:
    #     return render_template('login.html')
    campaign = mongo.db.campaigns.find_one({"campaign_name": campaign_name})
    location = []
    for loc in campaign['location']:
        # place search -- get place id for the very first result
        search_payload = {"key": key, "query": loc}
        search_req = requests.get(search_url, params=search_payload)
        search_json = search_req.json()  # json representation of the data
        location.append(search_json["results"][0]["geometry"]["location"])
        #data = [(l[1], l[3] ) for l in location.append(search_json["results"][0]["geometry"]["location"])]
        #print(search_json["results"][0]["geometry"]["location"]['lat'])
    return render_template('location_map.html', location=json.dumps(location))



@app.route('/createTask/<campaign_name>')
def create_task(campaign_name):
    # if 'username' not in session:
    #     return render_template('login.html')
    campaign = mongo.db.campaigns.find_one({"campaign_name": campaign_name})
    location = []
    for loc in campaign['location']:
        # place search -- get place id for the very first result
        search_payload = {"key": key, "query": loc}
        search_req = requests.get(search_url, params=search_payload)
        search_json = search_req.json()  # json representation of the data
        location.append((search_json["results"][0]["geometry"]["location"]["lat"], search_json["results"][0]["geometry"]["location"]["lng"]))
    count_date = 0
    ava_time =[]
    for can in campaign['canvassers']:
        canvasser = mongo.db.user_database.find_one({"_id" : bson.objectid.ObjectId(can)})
        for date in canvasser['ava_data']:
            if date >= campaign['duration'][0] and date <= campaign['duration'][1]:
                ava_time.append((canvasser['name'], date))
                count_date += 1
    flag = True
    Last_assignment = None
    while(flag):
        data = create_data_model(location, count_date)
        routing = pywrapcp.RoutingModel(
            data["num_locations"],
            data["num_vehicles"],
            data["depot"])
    # Define weight of each edge
        distance_callback = create_distance_callback(data)
        routing.SetArcCostEvaluatorOfAllVehicles(distance_callback)
        add_distance_dimension(routing, distance_callback)
        stop_point, assignment = organize_task(routing, data)
        if stop_point is 1 and count_date !=1:
            count_date -= 1
            Last_assignment = assignment
        elif count_date is 1:
            flag =False
            Last_assignment = assignment
        else:
            flag = False
    not_enough = False
    if Last_assignment is None:
        not_enough = True
        count_date +=1
        flag = True
        while (flag):
            data = create_data_model(location, count_date)
            routing = pywrapcp.RoutingModel(
                data["num_locations"],
                data["num_vehicles"],
                data["depot"])
            # Define weight of each edge
            distance_callback = create_distance_callback(data)
            routing.SetArcCostEvaluatorOfAllVehicles(distance_callback)
            add_distance_dimension(routing, distance_callback)
            stop_point, assignment = organize_task(routing, data)
            if stop_point is 1:
                flag = False
                Last_assignment = assignment
            else:
                count_date +=1
    print(Last_assignment)
    node_list = print_solution(data, routing, Last_assignment)
    loc =campaign['location']
    loc_list = []
    for sub in node_list:
        sub_loc = []
        for i in sub:
            sub_loc.append(loc[i])
        loc_list.append(sub_loc)
    tasks = mongo.db.tasks
    i = len(ava_time)-1
    for sub in loc_list:
        if i != -1:
            tasks.insert({
                'campagin_name':campaign_name,
                'route': sub,
                'canvasser': ava_time[i][0],
                'date': ava_time[i][1]
            })
            i -= 1
        else:
            tasks.insert({
                'campagin_name':campaign_name,
                'route': sub,
            })
    return "Hello world"
    #return render_template("task_list.html", node_list=node_list, location=location, ava_time=ava_time, not_enough=not_enough,loc_name=campaign['location'])
    # Setting first solution heuristic (cheapest addition).

def organize_task(routing,data):
    search_parameters = pywrapcp.RoutingModel.DefaultSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)  # pylint: disable=no-member
    # Solve the problem.
    search_parameters.time_limit_ms = 3000
    try:
        assignment = routing.SolveWithParameters(search_parameters)
    except:
        pass
    return routing.status(), assignment


def create_data_model(_locations,time):
  """Stores the data for the problem"""
  data = {}
  data["locations"] =_locations
  data["num_locations"] = len(data["locations"])
  data["num_vehicles"] = time
  data["depot"] = 0
  return data

def manhattan_distance(position_1, position_2):
  """Computes the Manhattan distance between two points"""
  return latlondiatance(position_1[0],position_1[1],position_2[0],position_1[1])+\
         latlondiatance(position_1[0],position_1[1],position_1[0],position_2[1])


def latlondiatance(lat1,lon1,lat2,lon2):
    R = 6373.0
    dlon = radians(lon2) - radians(lon1)
    dlat = radians(lat2) - radians(lat1)
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


def create_distance_callback(data):
  """Creates callback to return distance between points."""
  _duration= {}

  for from_node in xrange(data["num_locations"]):
    _duration[from_node] = {}
    for to_node in xrange(data["num_locations"]):
      if from_node == to_node:
        _duration[from_node][to_node] = visit_duration
      else:
        _duration[from_node][to_node] = (
            manhattan_distance(data["locations"][from_node],
                               data["locations"][to_node]))/average_speed +visit_duration

  def distance_callback(from_node, to_node):
    """Returns the manhattan distance between the two nodes"""
    return _duration[from_node][to_node]
  return distance_callback

def add_distance_dimension(routing, distance_callback):
  """Add Global Span constraint"""
  distance = 'Distance'
  maximum_worktime = 8  # Maximum distance per vehicle.
  routing.AddDimension(
      distance_callback,
      0,  # null slack
      maximum_worktime,
      True,  # start cumul to zero
      distance)
  distance_dimension = routing.GetDimensionOrDie(distance)
  # Try to minimize the max distance among vehicles.
  distance_dimension.SetGlobalSpanCostCoefficient(100)
###########
# Printer #
###########
def print_solution(data, routing, assignment):
  """Print routes on console."""
  node_list=[]
  for vehicle_id in xrange(data["num_vehicles"]):
    index = routing.Start(vehicle_id)
    plan_output = 'Route for vehicle {}:\n'.format(vehicle_id)
    node_sublist=[]
    while not routing.IsEnd(index):
        node_sublist.append(routing.IndexToNode(index))
        index = assignment.Value(routing.NextVar(index))
    node_sublist.append(routing.IndexToNode(index))
    node_list.append(node_sublist)
  return node_list



# canvasser
@app.route('/canvasser', methods=['GET','POST'])
def canvasser():
    # if 'username' not in session:
    #     return render_template('login.html')
    if request.method == 'POST':
        users = mongo.db.user_database
        existing_user = users.find_one({'name': session['username'] })
        current_avadata = existing_user["ava_data"]
        if request.form['aday'] in current_avadata or request.form['aday'] == "":
            return render_template("canvasser.html", ava_date=current_avadata, length=len(current_avadata),repeatdata = 1)

        current_avadata.append(str(request.form['aday']))
        users.find_one_and_update({'name': session['username'] },
                                     {"$set": {'ava_data': current_avadata}})
        return render_template("canvasser.html",ava_date = current_avadata,length = len(current_avadata ),repeatdata = 0)
    else:
        users = mongo.db.user_database
        existing_user = users.find_one({'name': session['username']})
        current_avadata = existing_user["ava_data"]
        return render_template("canvasser.html",ava_date = current_avadata,length = len(current_avadata ),repeatdata = 0)

@app.route('/delte_canvasser_date', methods=['GET','POST'])
def delte_canvasser_date():
    # if 'username' not in session:
    #     return render_template('login.html')
    if request.method == 'POST':
        users = mongo.db.user_database
        existing_user = users.find_one({'name': session['username']})
        current_avadata = existing_user["ava_data"]
        delete_date = request.form.getlist('delete_date')

        l3 = [x for x in current_avadata if x not in delete_date]

        users.find_one_and_update({'name': session['username']},
                                  {"$set": {'ava_data': l3}})
        return render_template("canvasser.html", ava_date=l3, length=len(l3), repeatdata=0)





if __name__ == '__main__':
    app.secret_key = 'sekret'
    app.debug = True
    #app.run(ssl_context=('cert.pem', 'key.pem'))
    #app.run(ssl_context='adhoc')  # run as HTTPS
    app.run()
