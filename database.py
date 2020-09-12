from pymongo import MongoClient

class DBInfo:
	def __init__(self, host, port, dbName, collectionName):
		self.dbName = dbName
		self.collectionName = collectionName
		self.client = MongoClient(host, port)
		self.db = self.client[dbName]
		self.collection = self.db[collectionName]
		
		if dbName not in self.client.list_database_names():
			self.collection.create_index('userId')
			self.collection.create_index('type')
			self.collection.create_index('time')
			
dbInfo = DBInfo(host='127.0.0.1',port=27017,dbName='OpenHouseAI',collectionName='Logs')

def add_log(log):
	result = dbInfo.collection.insert_one(log)
	if result:
		return result.inserted_id
	else:
		return None
		
def add_logs(logs):
	result = dbInfo.collection.insert_many(logs)
	if result:
		return result.inserted_ids
	else:
		return None
	
def get_logs(filter={}):
	documents = dbInfo.db[dbInfo.collectionName].find(filter,{'_id':0})
	return [d for d in documents]