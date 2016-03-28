# Imports
from flask import Flask, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler import events
import os
import methods

# Globals
app = Flask(__name__)
scheduler = BackgroundScheduler()
port = int(os.getenv('VCAP_APP_PORT', 8080))

# Uncomment if you need to debug the site
# app.debug = True

# Routes
@app.route('/')
def hello_world():
  return 'Hello World!'
#
# Packet attrs: gdun
#
@app.route('/dashboard/', methods=['PUT','POST','DELETE'])
def dashboards():
  if request.method == 'PUT':
    return methods.set_next_index(request.get_json())
  elif request.method == 'POST':
    return methods.add_customer(request.get_json())
#  elif request.method == 'DELETE':
#    return methods.delete_customer(request.get_json())


# Start App
if __name__ == '__main__':
  scheduler.add_job(methods.rotating, 'interval', seconds=300)
  scheduler.add_listener(methods.error_listener, events.EVENT_JOB_EXECUTED | events.EVENT_JOB_ERROR)
  scheduler.start()

  try:
    app.run(host='0.0.0.0', port=port)

  except (KeyboardInterrupt, SystemExit):
    # Not strictly necessary if daemonic mode is enabled but should be done if possible
    scheduler.shutdown()
