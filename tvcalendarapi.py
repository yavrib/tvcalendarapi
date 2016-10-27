from flask import Flask, jsonify, request
from flask_pymongo import PyMongo
import datetime
import requests
import uuid

tvcalendarapi = Flask(__name__)
tvcalendarapi.config['SECRET_KEY'] = '\x06\xae}\xf3\x825\xf0\xcfT\x81\xc7\x91\xef\xee!]\x05\xb9\xb4\x99\xebe\xa0\xe7'
mongo = PyMongo(tvcalendarapi)
tvcalendarapi.config['MONGO_DBNAME'] = 'tvcalendarapi'
tvcalendarapi_context = tvcalendarapi.app_context()

User = {
    'username':None,
    'password':None,
    'email':None,
    'token':None,
    'tvShows':[],
}

def generateToken():
    return str(uuid.uuid4())

def generateUserJson(username,password,email,tvShows):
    User['username']=username
    User['password']=password
    User['email']=email
    User['token']=generateToken()
    User['tvShows']=tvShows
    return User

def checkUser(username,token):
    return mongo.db.users.find_one({'username':username, 'token':token})

def isUsernameAvailable(username):
    viewer = mongo.db.users.find_one({'username':username})
    if viewer == None:
        return True
    else:
        return False

now = datetime.datetime.now()

#Done
@tvcalendarapi.route('/indexShows', methods=['GET'])
def indexShows():
    if request.method == 'GET':
        tvShows = jsonify(requests.get('http://api.tvmaze.com/shows').json())
        tvcalendarapi.logger.debug('Next step is returning tvShows value')
        return tvShows

#Done
@tvcalendarapi.route('/showUserShows/<username>,<token>')
def showUsersShows(username,token):
    if request.method == 'GET':
        with tvcalendarapi_context:
            viewer = checkUser(username, token)
            return jsonify(viewer['tvShows'])

#Done
@tvcalendarapi.route('/addShow/<username>,<token>,<tvShow>')
def addShow(username, token, tvShow):
    if request.method == 'GET':#Revert to POST
        with tvcalendarapi_context:
            viewer = checkUser(username, token)
            if int(tvShow) not in viewer['tvShows']:
                viewer['tvShows'].append(int(tvShow))
            mongo.db.users.update({"username":viewer['username']},{"$set":{"tvShows":viewer['tvShows']}})
            return jsonify(viewer['tvShows'])

#Done
@tvcalendarapi.route('/removeShow/<username>,<token>,<tvShow>')
def removeShow(username, token, tvShow):
    if request.method == 'GET':#Revert to POST
        with tvcalendarapi_context:
            viewer = checkUser(username, token)
            viewer['tvShows'].remove(int(tvShow))
            mongo.db.users.update({'username':viewer['username']},{'$set':{'tvShows':viewer['tvShows']}})
            return jsonify(viewer['tvShows'])

#Done
@tvcalendarapi.route('/createUser/<username>,<password>,<email>')
def createUser(username,password,email):
    if request.method == 'GET':#Revert to POST
        with tvcalendarapi_context:
            if isUsernameAvailable(username):
                viewer = generateUserJson(username, password, email, [])
                mongo.db.users.insert(viewer)
                return jsonify({'username':viewer['username'],'token':viewer['token']})
            else:
                return jsonify({'error':'User already exists!'})

#Done
@tvcalendarapi.route('/login/<username>,<password>')
def login(username, password):
    if request.method == 'GET':#Revert to PUT
        with tvcalendarapi_context:
            viewer = mongo.db.users.find_one({'username':username, 'password':password})
            if viewer is not None:
                viewer['token'] = generateToken()
                mongo.db.users.update({'username':viewer['username']},{'$set':{'token':viewer['token']}})
                return jsonify({'username':viewer['username'],'token':viewer['token']})
            else:
                return jsonify({'error':'Check your credentials!'})

#Done
@tvcalendarapi.route('/logout/<username>,<password>')
def logout(username, password):
    if request.method == 'GET':#Revert to DELETE
        with tvcalendarapi_context:
            viewer = mongo.db.users.find_one({'username':username, 'password':password})
            if viewer is not None:
                viewer['token'] = None
                mongo.db.users.update({'username':viewer['username']},{'$set':{'token':viewer['token']}})
                return jsonify({'username':viewer['username'],'token':viewer['token']})
            else:
                return jsonify({'error':'Logout failed!'})

#Done
@tvcalendarapi.route('/showSchedule/<username>,<token>')
def showSchedule(username, token):
    if request.method == 'GET':
        with tvcalendarapi_context:
            viewerSchedule = []
            viewer = checkUser(username, token)
            today = str(now.year)+'-'+str(now.month)+'-'+str(int(now.day)-1)
            for tvShowIndex in viewer['tvShows']:
                isTodayAiring = requests.get('http://api.tvmaze.com/shows/'+str(tvShowIndex)+'/episodesbydate?date='+today).json()
                if type(isTodayAiring) is list:
                    viewerSchedule.append(tvShowIndex)
            return jsonify(schedule = viewerSchedule)

#Done
@tvcalendarapi.route('/searchShow/<username>,<token>,<show>', methods=['GET'])
def searchShow(username, token, show):
    if request.method == 'GET':
        with tvcalendarapi_context:
            viewer = checkUser(username, token)
            tvShow = requests.get('http://api.tvmaze.com/search/shows?q='+show).json()
            return jsonify(tvShow)

if __name__ == "__main__":
    tvcalendarapi.debug = True
    tvcalendarapi.run()
