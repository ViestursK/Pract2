from naked import *
import datetime

from datetime import timezone
from datetime import datetime

print("Asteroid in DB test")
print("----------")
print("Testing function \"mysql_check_if_ast_exists_in_db\"")
# Testing with valid parameters that are checked to be in DB
dt = datetime.now(timezone.utc)
utc_time = dt.replace(tzinfo=timezone.utc)
utc_timestamp = utc_time.timestamp()
millis = datetime.utcfromtimestamp(utc_timestamp).strftime('%Y-%m-%d %H:%M:%S')
init_db()
get_cursor()
assert mysql_check_if_ast_exists_in_db(millis , "085") == 0
print("OK")
print("----------")

