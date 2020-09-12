import json
import database
from flask import Flask, request
from dateutil.parser import parse, ParserError
from dateutil.tz import tzutc

app = Flask(__name__)

#=======================================================================================
# Routes handling
#=======================================================================================
@app.errorhandler(404)
def not_found(error):
    return 'The route you are trying to access does not exist.', 404

# Only kept this here for debugging purposes.
#@app.route('/')
#def home():
#	return 'Server ready for requests.'


@app.route('/save_log', methods=['POST'])
def save_log():
	return process_logs(request, False)


@app.route('/save_logs', methods=['POST'])
def save_logs():
	return process_logs(request)


@app.route('/get_logs', methods=['GET'])
def get_logs():
	# I'll assume that if the request body is empty all logs should be returned.
	# I understand that this is impractical in a real-world scenario.
	filter = {}
	
	try:
		json_object = request.get_json(force=True)
	except:
		json_object = request.get_json()

	if json_object != None:
		try:
			# Check filters format
			if is_valid_filter(json_object):
				# Convert datetimes, if needed
				if 'start' in json_object and type(json_object['start']) is str:
					json_object['start'] = parse(json_object['start'])
				if 'end' in json_object and type(json_object['end']) is str:
					json_object['end'] = parse(json_object['end'])
								
				filter = create_filter_query(json_object)
			else:
				return 'Invalid data in request.', 400
		except ParserError:
			return 'Invalid datetime format.', 400
		except ValueError:
			return 'Invalid body content in request.', 400
		except:
			return 'Error processing request.', 500
	
	logs = database.get_logs(filter)
	
	# Transform datetime into whatever time zone is to be used. Keeping UTC here for consistency.
	for log in logs:
		log['time'] = log['time'].replace(tzinfo=tzutc()).isoformat()

	return json.dumps(logs)


#=======================================================================================
# Auxiliar functions
#=======================================================================================
def process_logs(request, multiple=True):
	try:
		json_object = request.get_json(force=True)
	except:
		json_object = request.get_json()
	
	if json_object != None:
		try:
			if not multiple:
				json_object = [json_object]
			
			# Make sure that the request is a list of logs
			if type(json_object) is not list:
				raise ValueError()
			
			for log in json_object:
				# Do basic check to see if the log is valid (contains all required properties)
				# -> I didn't incorporate mongoDB schema/validation due to lack of time
				if is_valid_log(log):
					# Convert datetime, if needed
					if type(log['time']) is str:
						log['time'] = parse(log['time'])
				else:
					return 'Invalid or missing data in request.', 400
					
			# Save logs in database
			ids = database.add_logs(json_object)

			if ids != None:
				if len(ids) == 1:
					return 'Log saved successfully with id {}.'.format(ids[0])
				else:
					return '{} logs saved successfully.'.format(len(ids))
			else:
				return 'Error saving log(s).', 500
		except ParserError:
			return 'Invalid datetime format.', 400
		except ValueError:
			return 'Invalid body content in request.', 400
		except:
			return 'Error processing request.', 500
	else:
		return 'Empty body content in request.', 400

def is_valid_log(log):
	keys = ['userId', 'sessionId', 'time', 'type', 'properties']
	for key in keys:
		if key not in log:
			return False
	return True
	
def is_valid_filter(filter):
	keys = ['userId', 'start', 'end', 'type']
	for f in filter.keys():
		if f not in keys:
			return False
	return True
	
def create_filter_query(filter):
	conditions = {}
	constraints = filter.keys()
	if 'userId' in constraints:
		tmp = {'userId':filter['userId']}
		conditions.update(tmp)
	if 'start' in constraints:
		tmp = {'time':{'$gte':filter['start']}}
		conditions.update(tmp)
	if 'end' in constraints:
		tmp = {'time':{'$lte':filter['end']}}
		# Check if 'time' has already been set
		if 'time' in conditions.keys():
			conditions['time'].update(tmp['time'])
		else:
			conditions.update(tmp)
	if 'type' in constraints:
		tmp = {'type':filter['type']}
		conditions.update(tmp)
		
	return conditions


# Run in HTTP (only used when running application locally)
if __name__ == '__main__':
	app.run(host='127.0.0.1', port='5000')
