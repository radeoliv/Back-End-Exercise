'''
Simple example of testing framework for implemented Rest API (Python 3.6.6 64-bit)

Pytest is required to run the test cases
- Install: pip install -U pytest requests pytest-html
- Run: pytest (in the Test folder)
'''

import requests
import sys
import util
import json as js
from dateutil.tz import tzutc

#=============================================================
# Request handlers
#=============================================================
def request_get(url, json=None, auth=None, verify=False):
	try:
		if auth == None:
			resp = requests.get(url, json=json, verify=verify)
		else:
			resp = requests.get(url, json=json, auth=auth, verify=verify)
	except Exception as ex:
		print('requests.get() failed with exception:', str(ex))
		return None
	
	return resp
	
def request_post(url, json=None, auth=None, verify=False):
	try:
		# send post request
		resp = requests.post(url, json=json, verify=verify)
	except Exception as ex:
		print('requests.post() failed with exception:', str(ex))
		return None
	
	return resp

#=============================================================
# Tests
#=============================================================
host = '127.0.0.1'
port = '5000'

#
# Basic test for the REST API endpoint that processes and stores new logs in the db
#
def test_add_logs():
	url = f'http://{host}:{port}/savelogs'
	
	# Add new log to db
	logs = util.generate_documents(numDocuments=5)
	userId = 'TestingUser'
	
	# Set same username for all logs and adjust datetime format for JSON
	for log in logs:
		log['userId'] = userId
		log['time'] = log['time'].replace(tzinfo=tzutc()).isoformat()

	# Try to add logs by using the REST API
	resp = request_post(url, json=logs)
	
	# Retrieve logs from the db
	filter = {'userId':userId}
	newLogs = util.get_documents(filter)
	
	# Delete logs
	util.remove_documents(filter)

	# Adjust generated log format
	for log in newLogs:
		log['time'] = log['time'].replace(tzinfo=tzutc()).isoformat()

	assert resp != None
	assert resp.status_code == 200
	# Check if there is any difference between the lists of logs
	assert len([i for i in logs + newLogs if i not in logs or i not in newLogs]) == 0

#
# Basic test for the REST API endpoint that retrieves logs
#
def test_get_logs():
	url = f'http://{host}:{port}/logs'
	
	# Add new log to db
	logs = util.generate_documents(numDocuments=1)
	userId = 'TestingUser'
	typeStr = 'TestingType'
	logs[0]['userId'] = userId
	logs[0]['type'] = typeStr
	util.add_documents(logs)
	
	# Try to retrieve the log by using the REST API:
	# With userId
	filterUser = {'userId':userId}
	respUser = request_get(url, json=filterUser)
	# With type
	filterType = {'type':typeStr}
	respType = request_get(url, json=filterType)
	
	# Delete log
	util.remove_documents(filterUser)
	
	# Adjust generated log format
	logs[0]['time'] = logs[0]['time'].replace(tzinfo=tzutc()).isoformat()
	del logs[0]['_id']

	assert respUser != None
	assert respUser.status_code == 200
	assert respUser.json()[0] == logs[0]

	assert respType != None
	assert respType.status_code == 200
	assert respType.json()[0] == logs[0]