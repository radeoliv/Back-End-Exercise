import requests
import threading
import queue
import sys
import time
from dateutil.tz import tzutc
import queue
import itertools
import util
from collections import Counter

results = queue.Queue()
host = '127.0.0.1'
port = '5000'

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
# Test function
#=============================================================

# Each test tries to save 5 logs for a user
def test_save_logs(numLogPerUser):
	url = f'http://{host}:{port}/save_logs'
	logs = util.generate_documents(numDocuments=numLogPerUser, numUsers=1, numSessions=1)

	# Set same username for all logs and adjust datetime format for JSON
	userId = 'TestingUser'
	for log in logs:
		log['userId'] = userId
		log['time'] = log['time'].replace(tzinfo=tzutc()).isoformat()

	resp = request_post(url, json=logs)

	return resp.status_code == 200, resp.elapsed.total_seconds()

def perf_test(delay=0, maxIterations=sys.maxsize, numLogPerUser=5):
	count = 0
	while count < maxIterations:
		resultCode, duration = test_save_logs(numLogPerUser)
		results.put([resultCode, duration])

		count += 1
		time.sleep(delay)

#=============================================================
# Statistics
#=============================================================
def stats(numUsers, maxIterations, numLogPerUser, totalTime):
	numPass = 0
	numFail = 0
	totalDuration = 0
	meanDuration = 0
	minDuration = None
	maxDuration = None
	requestsPerSecond = 0

	count = 0
	while True:
		try:
			result = results.get_nowait()
			count += 1
		except queue.Empty:
			break
		
		if result[0]:
			numPass += 1
		else:
			numFail += 1

		totalDuration += result[1]
		if maxDuration == None or result[1] > maxDuration:
			maxDuration = result[1]
		if minDuration == None or result[1] < minDuration:
			minDuration = result[1]

	if count != 0:
		meanDuration = totalDuration / count
	requestsPerSecond = count / totalTime

	print('-----------------Test Statistics-----------------')
	print('Total execution time (s): {:.2f}'.format(totalTime))
	print('Concurrent users: {}'.format(numUsers))
	print('Logs per user: {}'.format(numLogPerUser))
	print('Requests per user: {}'.format(maxIterations))
	print()
	print('Total tests: {} | Pass: {} | Fail: {}'.format(count, numPass, numFail))
	print('Requests per second: {:.1f}'.format(requestsPerSecond))
	print('Request duration (s) - average: {:.3f} | min: {:.3f} | max: {:.3f}'
		.format(meanDuration, minDuration, maxDuration))

#=============================================================
# Main - starting point
#=============================================================
if __name__ == '__main__':
	numUsers = 100
	delay = 0
	maxIterations = 50
	numLogPerUser = 5

	start = time.time()

	threads = []
	for _ in itertools.repeat(None, numUsers):
		thread = threading.Thread(target=perf_test, args=(delay, maxIterations, numLogPerUser), daemon=True)
		thread.start()
		threads.append(thread)

	# Wait for all threads
	for t in threads:
		t.join()

	end = time.time()
	totalTime = end-start

	# Remove test documents
	util.remove_documents({'userId':'TestingUser'})

	# Print test stats
	stats(numUsers, maxIterations, numLogPerUser, totalTime)