import server
import unittest
import json
from pymongo import MongoClient
from base64 import b64encode


# unit test for Server.py classes
class FlaskrTestCase(unittest.TestCase):
    # set up before each test case
    def setUp(self):
        self.app = server.app.test_client()     # reference server's Flask app
        server.app.config['TESTING'] = True     # run in testing mode

        mongo = MongoClient('localhost', 27017)     # establish connect to MDB
        db = mongo.test_database                    # injest test DB into app
        server.app.db = db                          # specify DB to store data

    # test Trip POST method
    def test_post(self):
        # create headers by encoding un:pw and encoding using b64
        creds_string = "{0}:{1}".format('lesliekimm', 'password')
        cred_encoded = creds_string.encode('utf-8')
        cred_b64encoded = b64encode(cred_encoded).decode()
        # create headers with properly encoded us:pw
        headers = {'Authorization': 'Basic ' + cred_b64encoded}

        # create Trip with a name and empty waypoints array
        response = self.app.post('/trips/', headers=headers, data=json.dumps(
            dict(name='San Fran', waypoints=[])),
            content_type='application/json')

        # decode the JOSN doc returned which includes _id, name and waypoints
        responseJSON = json.loads(response.data.decode())

        # perform assertion tests
        self.assertEqual(response.status_code, 200)
        assert 'application/json' in response.content_type
        assert 'San Fran' in responseJSON['name']
        self.assertEqual(0, len(responseJSON['waypoints']))

    # test Trip GET method
    def test_get(self):
        # create headers by encoding un:pw and encoding using b64
        creds_string = "{0}:{1}".format('lesliekimm', 'password')
        cred_encoded = creds_string.encode('utf-8')
        cred_b64encoded = b64encode(cred_encoded).decode()
        # create headers with properly encoded us:pw
        headers = {'Authorization': 'Basic ' + cred_b64encoded}

        # create Trip with a name and empty waypoitns array
        response = self.app.post('/trips/', headers=headers, data=json.dumps(
            dict(name='Cross country', waypoints=[])),
            content_type='application/json')

        # decode JSON doc returned and get _id
        postResponseJSON = json.loads(response.data.decode())
        postedObjectID = postResponseJSON['_id']

        # GET the specific trip associated with retrieve _id and decode
        response = self.app.get('/trips/'+postedObjectID)
        responseJSON = json.loads(response.data.decode())

        # perform assertion tests
        self.assertEqual(response.status_code, 200)
        assert 'Cross country' in responseJSON['name']
        self.assertEqual(0, len(responseJSON['waypoints']))

    # test Trip GET method for nonexistent Trip object
    def test_get_nonexistent_trip(self):
        # GET a Trip that doesn't exist
        response = self.app.get('/trips/55f0cbb4236f44b7f0e3cb23')

        # perform assertion tests
        self.assertEqual(response.status_code, 404)

    # test Trip GET method for entire trip collection
    def test_get_no_id(self):
        # TO-DO: FIX GET METHOD TO RETURN COLLECTION!!!
        response = self.app.get('/trips/')
        self.assertEqual(response.status_code, 404)

    # test Trip PUT method
    def test_put(self):
        # create headers by encoding un:pw and encoding using b64
        creds_string = "{0}:{1}".format('lesliekimm', 'password')
        cred_encoded = creds_string.encode('utf-8')
        cred_b64encoded = b64encode(cred_encoded).decode()
        # create headers with properly encoded us:pw
        headers = {'Authorization': 'Basic ' + cred_b64encoded}

        # create Trip with a name and empty waypoints array
        response = self.app.post('/trips/', headers=headers, data=json.dumps(
            dict(name='San Fran', waypoints=[])),
            content_type='application/json')

        # decode JSON doc returned and get _id
        postResponseJSON = json.loads(response.data.decode())
        postedObjectID = postResponseJSON['_id']

        # PUT changes for specified Trip
        response = self.app.put('/trips/'+postedObjectID, data=json.dumps(
            dict(name='BOING',
                 waypoints=['mission', 'soma', 'nob hill'])),
            content_type='application/json')
        responseJSON = json.loads(response.data.decode())

        # perform assertion tests
        self.assertEqual(response.status_code, 200)
        assert 'BOING' in responseJSON['name']
        self.assertEqual(3, len(responseJSON['waypoints']))

    # test Trip DELETE method
    def test_delete(self):
        # create headers by encoding un:pw and encoding using b64
        creds_string = "{0}:{1}".format('lesliekimm', 'password')
        cred_encoded = creds_string.encode('utf-8')
        cred_b64encoded = b64encode(cred_encoded).decode()
        # create headers with properly encoded us:pw
        headers = {'Authorization': 'Basic ' + cred_b64encoded}

        # create Trip with a name and waypoints array
        response = self.app.post('/trips/', headers=headers, data=json.dumps(
            dict(name='San Fran',
                 waypoints=['russian hill', 'pac heights', 'sunset'])),
            content_type='application/json')

        # decode JSON doc returned and get _id
        postResponseJSON = json.loads(response.data.decode())
        postedObjectID = postResponseJSON['_id']

        # DELETE Trip of specified _id
        del_response = self.app.delete('/trips/'+postedObjectID)

        # perform assertion tests
        self.assertEqual(del_response.status_code, 200)

    # test User POST and GET method - will also test auuthentication
    def test_post_user(self):
        # create User with username and password
        self.app.post('/users/', data=json.dumps(dict(
                      username='lesliekimm', password='password')),
                      content_type='application/json')

        # create headers by encoding un:pw and encoding using b64
        creds_string = "{0}:{1}".format('lesliekimm', 'password')
        cred_encoded = creds_string.encode('utf-8')
        cred_b64encoded = b64encode(cred_encoded).decode()
        # create headers with properly encoded us:pw
        headers = {'Authorization': 'Basic ' + cred_b64encoded}

        # GET User which tests authentication
        get_response = self.app.get('/users/', headers=headers)

        # perform assertion tests
        self.assertEqual(get_response.status_code, 200)

    def test_user_trip(self):
        user_resp = self.app.post('/users/', data=json.dumps(dict(
                                  username='lesliekimm', password='password')),
                                  content_type='application/json')
        user_response_JSON = json.loads(user_resp.data.decode())
        user_id = user_response_JSON[:]

        # create headers by encoding un:pw and encoding using b64
        creds_string = "{0}:{1}".format('lesliekimm', 'password')
        cred_encoded = creds_string.encode('utf-8')
        cred_b64encoded = b64encode(cred_encoded).decode()
        # create headers with properly encoded us:pw
        headers = {'Authorization': 'Basic ' + cred_b64encoded}

        response = self.app.post('/trips/', headers=headers, data=json.dumps(
            dict(name='San Fran', waypoints=[], uID=user_id)),
            content_type='application/json')


if __name__ == '__main__':
    unittest.main()                             # run unit test
