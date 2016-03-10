from flask import Flask
import os

app = Flask(__name__)

# Uncomment if you need to debug the site
app.debug = True

port = int(os.getenv('VCAP_APP_PORT', 8080))

@app.route('/')
def hello_world():
  return 'Hello World!'

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=port)
