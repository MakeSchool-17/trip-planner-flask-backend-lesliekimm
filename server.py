from flask import Flask, request, make_response, jsonify
from flask_restful import Resource, Api
from pymongo import MongoClient
from bson.objectid import ObjectId
from utils.mongo_json_encoder import JSONEncoder

# basic setup
app = Flask(__name__)                       # create flask instance
mongo = MongoClient('localhost', 27017)     # establish connection to local MDB
app.db = mongo.develop_database             # specify DB to store data
# create instance of flask_restful API to add diff endpts to this API
# provides specific format for defining endpts fro diff resources in our app
api = Api(app)


# implement REST Resource
# most apps will defined one resource for each entity that can be stored in app
# resource implements one method for each HTTP verb that is supported
class MyObject(Resource):
    # invoked to create a new instance of MyObject on the server
    # client that calls this endpt provides a JSON body as part of HTTP request
    def post(self):
        # access JSON that client provides
        new_myobject = request.json
        # access collection where we will store new object
        # typically, one collection per entity
        myobject_collection = app.db.myobjects
        # insert JSON document into collection
        result = myobject_collection.insert_one(new_myobject)
        # retrieve the result - use the result to fetch inserted doc from the
        # collection using the find_one method
        # find_one takes a dictionary that describers filter criteria for docs
        myobject = myobject_collection.find_one(
            {"_id": ObjectId(result.inserted_id)})
        # return selected doc to client
        return myobject

    def get(self, myobject_id):
        # reference my_collection to select the doc that client is trying to
        # access
        myobject_collection = app.db.myobjects
        # build a query based on my_objet_id that we recieved as poart of
        # client's request
        myobject = myobject_collection.find_one({"_id": ObjectId(myobject_id)})

        # if doc w/ provided id isn't found, return a 404 statement, else
        # return doc to client
        if myobject is None:
            response = jsonify(data=[])
            response.status_code = 404
            return response
        else:
            return myobject


class Trip(Resource):
    # create an instance of Trip - trip with waypoints
    def post(self, trip_id=None):
        trip = request.json
        trip_collection = app.db.trips
        result = trip_collection.insert_one(trip)   # inserting doc
        # retrieve the result of inserting doc & use to fetch inserted doc
        # from the collection using find_one - takes a dictionary that
        # describes filter criteria for our dogs (i.e. _id) the _id field is
        # auto maintained by MongoDB & stores unique ID for each doc stored
        # we wrap result.inserted_id into TripId type - not a string!
        my_trip = trip_collection.find_one(
            {"_id": ObjectId(result.inserted_id)})

        return my_trip

    # retrieve a Trip instance
    def get(self, trip_id=None):
        trip_collection = app.db.trips
        trip = trip_collection.find_one({"_id": ObjectId(trip_id)})

        if trip is None:
            response = jsonify(data=[])
            response.status_code = 404
            return response
        else:
            return trip

    # update a Trip
    def put(self, trip_id):
        trip_update = request.json
        trip_collection = app.db.trips
        print(trip_update)
        print(trip_id)

        result = trip_collection.update_one(
            {'_id': trip_id}, {'$set': {'name': 'San Fran',
             'waypoints': ['mission', 'soma', 'nob hill']}}, upsert=False)

        # UPDATE - check pymongo documentation
        return result

    # delete a Trip
    def delete(self, trip_id):
        trip_collection = app.db.trips

        # DELETE - check pymongo documentation
        return

# add REST resource to API by mapping btw routes and resources
# a route defines a URL that can be called by a client app
# first param is resource we want to map to a specific URL
# next are collection of endpts
api.add_resource(MyObject, '/myobject/', '/myobject/<string:myobject_id>')
api.add_resource(Trip, '/trip/', '/trip/<string:trip_id>')

# provide a custom JSON serializer for flaks_restful
@api.representation('application/json')
def output_json(data, code, headers=None):
    resp = make_response(JSONEncoder().encode(data), code)
    resp.headers.extend(headers or {})
    return resp

if __name__ == '__main__':
    # Turn this on in debug mode to get detailled information about request
    # related exceptions: http://flask.pocoo.org/docs/0.10/config/
    app.config['TRAP_BAD_REQUEST_ERRORS'] = True
    app.run(debug=True)
