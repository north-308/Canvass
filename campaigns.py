from flask import Flask

from flask_pymongo import PyMongo

app = Flask(__name__)

app.config['MONGO_DBNAME'] = 'canvassing_db'
app.config['MONGO_URI'] = 'mongodb://songyy:cse308@ds125953.mlab.com:25953/canvassing_db'
app.config['ENV'] = 'development'

mongo = PyMongo(app)

@app.route('/add')
def add():
    user = mongo.db.users
    print(user);
    user.insert({'name' : 'jqqq'})
    return 'Added user!'

if __name__ == '__main__':
    app.run(debug = False)