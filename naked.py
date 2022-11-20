import requests
import json
import datetime
import time
import yaml
import logging
import logging.config
import mysql.connector
from mysql.connector import Error

from datetime import datetime
from configparser import ConfigParser

# Loading logging configuration
with open('./log_worker.yaml', 'r') as stream:
   log_config = yaml.safe_load(stream)

logging.config.dictConfig(log_config)

	# Creating logger
logger = logging.getLogger('root')

logger.info('Asteroid processing service')

# Initiating and reading config values.
logger.info('Loading configuration from file')

try:
	config = ConfigParser()
	config.read('config.ini')

	nasa_api_key = config.get('nasa', 'api_key')
	nasa_api_url = config.get('nasa', 'api_url')


	mysql_config_mysql_host = config.get('mysql_config', 'mysql_host')
	mysql_config_mysql_db = config.get('mysql_config', 'mysql_db')
	mysql_config_mysql_user = config.get('mysql_config', 'mysql_user')
	mysql_config_mysql_pass = config.get('mysql_config', 'mysql_pass')
except:
	logger.exception('')
logger.info('DONE')

def init_db():
	global connection
	connection = mysql.connector.connect(host=mysql_config_mysql_host, database=mysql_config_mysql_db, user=mysql_config_mysql_user, password=mysql_config_mysql_pass)

def get_cursor():
	global connection
	try:
		connection.ping(reconnect=True, attempts=1, delay=0)
		connection.commit()
	except mysql.connector.Error as err:
		logger.error("No connection to db " + str(err))
		connection = init_db()
		connection.commit()
	return connection.cursor()

# Check if asteroid exists in db
def mysql_check_if_ast_exists_in_db(request_day, ast_id):
	records = []
	cursor = get_cursor()
	try:
		cursor = connection.cursor()
		result  = cursor.execute("SELECT count(*) FROM ast_daily WHERE `create_date` = '" + str(request_day) + "' AND `ast_id` = '" + str(ast_id) + "'")
		records = cursor.fetchall()
		connection.commit()
	except Error as e :
		logger.error("SELECT count(*) FROM ast_daily WHERE `create_date` = '" + str(request_day) + "' AND `ast_id` = '" + str(ast_id) + "'")
		logger.error('Problem checking if asteroid exists: ' + str(e))
		pass
	return records[0][0]

# Asteroid value insert
def mysql_insert_ast_into_db(create_date, hazardous, name, url, diam_min, diam_max, ts, dt_utc, dt_local, speed, distance, ast_id):
	cursor = get_cursor()
	try:
		cursor = connection.cursor()
		result  = cursor.execute( "INSERT INTO `ast_daily` (`create_date`, `hazardous`, `name`, `url`, `diam_min`, `diam_max`, `ts`, `dt_utc`, `dt_local`, `speed`, `distance`, `ast_id`) VALUES ('" + str(create_date) + "', '" + str(hazardous) + "', '" + str(name) + "', '" + str(url) + "', '" + str(diam_min) + "', '" + str(diam_max) + "', '" + str(ts) + "', '" + str(dt_utc) + "', '" + str(dt_local) + "', '" + str(speed) + "', '" + str(distance) + "', '" + str(ast_id) + "')")
		connection.commit()
	except Error as e :
		logger.error( "INSERT INTO `ast_daily` (`create_date`, `hazardous`, `name`, `url`, `diam_min`, `diam_max`, `ts`, `dt_utc`, `dt_local`, `speed`, `distance`, `ast_id`) VALUES ('" + str(create_date) + "', '" + str(hazardous) + "', '" + str(name) + "', '" + str(url) + "', '" + str(diam_min) + "', '" + str(diam_max) + "', '" + str(ts) + "', '" + str(dt_utc) + "', '" + str(dt_local) + "', '" + str(speed) + "', '" + str(distance) + "', '" + str(ast_id) + "')")
		logger.error('Problem inserting asteroid values into DB: ' + str(e))
		pass

def push_asteroids_arrays_to_db(request_day, ast_array, hazardous):
	for asteroid in ast_array:
		if mysql_check_if_ast_exists_in_db(request_day, asteroid[9]) == 0:
			logger.debug("Asteroid NOT in db")
			mysql_insert_ast_into_db(request_day, hazardous, asteroid[0], asteroid[1], asteroid[2], asteroid[3], asteroid[4], asteroid[5], asteroid[6], asteroid[7], asteroid[8], asteroid[9])
		else:
			logger.debug("Asteroid already IN DB")

if __name__ == "__main__":

	connection = None
	connected = False

	init_db()

	# Opening connection to mysql DB
	logger.info('Connecting to MySQL DB')
	try:
		# connection = mysql.connector.connect(host=mysql_config_mysql_host, database=mysql_config_mysql_db, user=mysql_config_mysql_user, password=mysql_config_mysql_pass)
		cursor = get_cursor()
		if connection.is_connected():
			db_Info = connection.get_server_info()
			logger.info('Connected to MySQL database. MySQL Server version on ' + str(db_Info))
			cursor = connection.cursor()
			cursor.execute("select database();")
			record = cursor.fetchone()
			logger.debug('Your connected to - ' + str(record))
			connection.commit()
	except Error as e :
		logger.error('Error while connecting to MySQL' + str(e))

	# Getting todays date.
	dt = datetime.now()
	request_date = str(dt.year) + "-" + str(dt.month).zfill(2) + "-" + str(dt.day).zfill(2)  
	logger.debug("Generated today's date: " + str(request_date))

	# Printing information of todays date, time, used api key and url.
	logger.debug("Request url: " + str(nasa_api_url + "rest/v1/feed?start_date=" + request_date + "&end_date=" + request_date + "&api_key=" + nasa_api_key))
	r = requests.get(nasa_api_url + "rest/v1/feed?start_date=" + request_date + "&end_date=" + request_date + "&api_key=" + nasa_api_key)

	# Printing information about request response - status code, headers and content.
	logger.debug("Response status code: " + str(r.status_code))
	logger.debug("Response headers: " + str(r.headers))
	logger.debug("Response content: " + str(r.text))

	if r.status_code == 200:

		json_data = json.loads(r.text)

		# Arrays for storing safe/hazardous asteroid objects.
		ast_safe = []
		ast_hazardous = []

		# If element_count is NOT empty, the integer is assigned to ast_count variable and used to display today's asteroid count.
		if 'element_count' in json_data:
			ast_count = int(json_data['element_count'])
			logger.info("Asteroid count today: " + str(ast_count))

			# Checks if ast_count is larger than 0. If true - enters for loop.
			if ast_count > 0:
				# Iterating through near_earth_objects of today.
				for val in json_data['near_earth_objects'][request_date]:
					# If name, url, size and other parameters are NOT empty, ~sort of an object~ is created with those parameters.
					if 'name' and 'nasa_jpl_url' and 'estimated_diameter' and 'is_potentially_hazardous_asteroid' and 'close_approach_data' in val:
						tmp_ast_name = val['name'] # Assigning name.
						tmp_ast_nasa_jpl_url = val['nasa_jpl_url'] # Assigning the url.
						# Getting id of asteroid
						tmp_ast_id = val['id']
						# If kilometers section is not empty in JSON file, the estimated diameter of the asteroid is given to variable.
						if 'kilometers' in val['estimated_diameter']:
							# If estimated_diameter_min and estimated_diameter_max sections are NOT empty in the JSON file, values get assigned to variables.
							if 'estimated_diameter_min' and 'estimated_diameter_max' in val['estimated_diameter']['kilometers']:
								tmp_ast_diam_min = round(val['estimated_diameter']['kilometers']['estimated_diameter_min'], 3)
								tmp_ast_diam_max = round(val['estimated_diameter']['kilometers']['estimated_diameter_max'], 3)
							# In case of the estimated_diameter_min and estimated_diameter_max fields being empty in JSON, the min and max diameter values are set to 2.
							else:
								tmp_ast_diam_min = -2
								tmp_ast_diam_max = -2
						# If asteroids estimated_diameter does not have kilometers key, estimated_diameter_min and estimated_diameter_max variable values are set to 1. 
						else:
							tmp_ast_diam_min = -1
							tmp_ast_diam_max = -1

						# Boolean temporary variable that indicates if asteroid is hazadrous, is set to the value found in response.
						tmp_ast_hazardous = val['is_potentially_hazardous_asteroid']

						# Checks If length in asteroids close_approach_data field is greater than 0, if true, the next if/else check is made. 
						if len(val['close_approach_data']) > 0:
							# If the first element of asteroids close_approach_data contains values for epoch_date_close_approach, relative_velocity, miss_distance.
							if 'epoch_date_close_approach' and 'relative_velocity' and 'miss_distance' in val['close_approach_data'][0]:
								tmp_ast_close_appr_ts = int(val['close_approach_data'][0]['epoch_date_close_approach']/1000) # Parsing data about close approach to miliseconds.
								tmp_ast_close_appr_dt_utc = datetime.utcfromtimestamp(tmp_ast_close_appr_ts).strftime('%Y-%m-%d %H:%M:%S') # Formatting miliseconds to UTC time format.
								tmp_ast_close_appr_dt = datetime.fromtimestamp(tmp_ast_close_appr_ts).strftime('%Y-%m-%d %H:%M:%S') # Converting miliseconds to local time.

								# If close_approach_data's first element's (relative_velocity object) contains kilometers_per_hour 
								# it then selects kilometers per hour of asteroids relative velocity and parses it to float and integer at the end to get rid of decimal points.
								if 'kilometers_per_hour' in val['close_approach_data'][0]['relative_velocity']:
									tmp_ast_speed = int(float(val['close_approach_data'][0]['relative_velocity']['kilometers_per_hour']))
								# If close_approach_data's first element's (relative_velocity object) DOES NOT contain kilometers_per_hour, tmp_ast_speed value is set to -1.
								else:
									tmp_ast_speed = -1

								# If close_approach_data's first element's (miss_distance object) contains "kilometers", that value gets rounded with 3 digits after the comma and assigned as value to tmp_ast_miss_dist.
								if 'kilometers' in val['close_approach_data'][0]['miss_distance']:
									tmp_ast_miss_dist = round(float(val['close_approach_data'][0]['miss_distance']['kilometers']), 3)
								# If close_approach_data's first element's (miss_distance object) does NOT contain "kilometers", the tmp_ast_miss_dist value is set to "-1".
								else:
									tmp_ast_miss_dist = -1
							# If line 73 IF statement does not go through, these parameters for these variables are set.
							else:
								tmp_ast_close_appr_ts = -1
								tmp_ast_close_appr_dt_utc = "1969-12-31 23:59:59"
								tmp_ast_close_appr_dt = "1969-12-31 23:59:59"
						# If line 71 IF statement does not go through, a pront-out is made and parameters set to specified variables.
						else:
							logger.warning("No close approach data in message")
							tmp_ast_close_appr_ts = 0
							tmp_ast_close_appr_dt_utc = "1970-01-01 00:00:00"
							tmp_ast_close_appr_dt = "1970-01-01 00:00:00"
							tmp_ast_speed = -1
							tmp_ast_miss_dist = -1

						# Printing information about the asteroid: name, info, size, speed and time + date.
						logger.info("------------------------------------------------------- >>")
						logger.info("Asteroid name: " + str(tmp_ast_name) + " | INFO: " + str(tmp_ast_nasa_jpl_url) + " | Diameter: " + str(tmp_ast_diam_min) + " - " + str(tmp_ast_diam_max) + " km | Hazardous: " + str(tmp_ast_hazardous))
						logger.info("Close approach TS: " + str(tmp_ast_close_appr_ts) + " | Date/time UTC TZ: " + str(tmp_ast_close_appr_dt_utc) + " | Local TZ: " + str(tmp_ast_close_appr_dt))
						logger.info("Speed: " + str(tmp_ast_speed) + " km/h" + " | MISS distance: " + str(tmp_ast_miss_dist) + " km")
						
						# Adding asteroid data to the corresponding array.
						if tmp_ast_hazardous == True:
							ast_hazardous.append([tmp_ast_name, tmp_ast_nasa_jpl_url, tmp_ast_diam_min, tmp_ast_diam_max, tmp_ast_close_appr_ts, tmp_ast_close_appr_dt_utc, tmp_ast_close_appr_dt, tmp_ast_speed, tmp_ast_miss_dist, tmp_ast_id])
						else:
							ast_safe.append([tmp_ast_name, tmp_ast_nasa_jpl_url, tmp_ast_diam_min, tmp_ast_diam_max, tmp_ast_close_appr_ts, tmp_ast_close_appr_dt_utc, tmp_ast_close_appr_dt, tmp_ast_speed, tmp_ast_miss_dist, tmp_ast_id])

			# If line 45 IF statement does not go through, a print-out is made with no asteroids hitting Earth.
			else:
				logger.info("No asteroids are going to hit earth today")

		# Printing Hazadous and Safe asteroids.
		logger.info("Hazardous asteorids: " + str(len(ast_hazardous)) + " | Safe asteroids: " + str(len(ast_safe)))

		# If length of ast_hazardous is greater than "0", It is sorted. 
		if len(ast_hazardous) > 0:

			ast_hazardous.sort(key = lambda x: x[4], reverse=False)

			# Printing a message and entering a for loop of asteroids in ast_hazardous list.
			logger.info("Today's possible apocalypse (asteroid impact on earth) times:")
			for asteroid in ast_hazardous:
				# Structuring a printout with date, time, name and a link to more information.
				logger.info(str(asteroid[6]) + " " + str(asteroid[0]) + " " + " | more info: " + str(asteroid[1]))

			# Sorting and printing the closest passing asteroid and providing extra details like speed.
			ast_hazardous.sort(key = lambda x: x[8], reverse=False)
			logger.info("Closest passing distance is for: " + str(ast_hazardous[0][0]) + " at: " + str(int(ast_hazardous[0][8])) + " km | more info: " + str(ast_hazardous[0][1]))
		# If line 126 IF statement does not go through, a print-out is made.
		else:
			logger.info("No asteroids close passing earth today")

		
		push_asteroids_arrays_to_db(request_date, ast_safe, 0)
	
	# If line 31 IF statement does not go through, an error message of "Unable to get response from API." is provided with details.
	else:
		logger.error("Unable to get response from API. Response code: " + str(r.status_code) + " | content: " + str(r.text))
