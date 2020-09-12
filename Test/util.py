import sys
import random
import string
import time
from datetime import datetime, timedelta
import itertools
sys.path.insert(1, '..')
import database

def random_string_generator(str_size):
	allowed_chars = string.ascii_letters + string.digits
	return ''.join(random.choice(allowed_chars) for x in range(str_size))
	
def random_date_generator(start, end):
	if start == None:
		start = datetime(2000, 1, 1)
	if end == None:
		end = datetime(2020, 1, 1)
	
	return start + timedelta(
		# Get a random amount of seconds between `start` and `end`
		seconds=random.randint(0, int((end - start).total_seconds())),
	)

# Note that "for _ in itertools.repeat(None, iterations)" optimizes the total loop time
def generate_documents(numDocuments=100000, numUsers=100, numSessions=200, timeStart=None, timeEnd=None):
	userIds = [random_string_generator(9) for _ in itertools.repeat(None, numUsers)]
	sessionIds = [random_string_generator(9) for _ in itertools.repeat(None, numSessions)]
	types = ['CLICK', 'VIEW', 'NAVIGATE']
	docs = []
	for _ in itertools.repeat(None, numDocuments):
		document = {
			'userId':random.choice(userIds),
			'sessionId':random.choice(sessionIds),
			'type':random.choice(types),
			'time':random_date_generator(timeStart,timeEnd),
			'properties':{}
		}
		docs.append(document)
	return docs

def add_documents(docs):
	return database.add_logs(docs)
	
def get_documents(filter):
	return database.get_logs(filter)
	
def remove_documents(filter={}):
	database.dbInfo.collection.delete_many(filter)	

# Test database performance with the insertion/retrieval of documents
def db_performance_test():
	# Clear database and populate with new random documents
	database.dbInfo.collection.delete_many({})
	print('Database cleaned.')

	docs = generate_documents()

	begin = time.time()
	ids = database.add_logs(docs)
	print('{} documents added. Total time of {} seconds.'.format(len(ids), time.time()-begin))

	begin = time.time()
	docs = database.get_logs()
	print('{} documents retrieved. Total time of {} seconds.'.format(len(docs), time.time()-begin))