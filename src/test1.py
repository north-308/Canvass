from flask import Flask

from flask_pymongo import PyMongo

# from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config['MONGO_DBNAME'] = 'canvassing_db'
app.config['MONGO_URI'] = 'mongodb://songyy:cse308@ds125953.mlab.com:25953/canvassing_db'


mongo = PyMongo(app)

@app.route('/add')
def add():
    user = mongo.db.users
    user.insert({'name' : 'jqt'})
    return 'Added user!'