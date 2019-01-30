from flask import Flask, render_template, url_for, request, session, redirect
from flask_pymongo import PyMongo


app = Flask(__name__)
# connection for database
app.config['MONGO_DBNAME'] = 'canvassing_db'
app.config['MONGO_URI'] = 'mongodb://songyy:cse308@ds125953.mlab.com:25953/canvassing_db'

mongo = PyMongo(app)  # instantiate the db connection





@app.route('/create_task')
def create_task():
    print()


if __name__ == '__main__':
    app.secret_key = 'sekret'
    app.debug = True
    #app.run(ssl_context=('cert.pem', 'key.pem'))
    #app.run(ssl_context='adhoc')  # run as HTTPS
    app.run()
