### All imports ###
import sched, time
import json
import multiprocessing
import requests
import datetime
import boto3

from botocore.client import Config

### Load config files and declare globals ###
with open('config.json') as config_file:
  config = json.load(config_file)

auth_token = config['auth_token']
ecs_url = config['ecs_url']
ecs_user_id = config['ecs_user_id']
ecs_user_access_key = config['ecs_user_access_key']
ecs_installs_bucket = config['ecs_installs_bucket']
ess_srs_bucket = config['ess_srs_bucket']

gdun_index = multiprocessing.Value('i', 0)
prev_gdun_index = multiprocessing.Value('i', -1)

### Methods ###

# listener to give visibility into job completetion
def error_listener(event):
  if event.exception:
    print("The job failed...{0}".format(event.exception))
    print("{0}".format(event.traceback))
  else:
    print("The job worked!")

# Function to set gdun index variable
def set_next_index(packet):

  # Grab the file
  with open('config.json') as config_file:
    config = json.load(config_file)
  gduns = config['gduns']
  found = False

  # See if the customer is already next
  if gduns[gdun_index.value]['num'] == packet['gdun'] or packet['gdun'] in gduns[gdun_index.value]['name']:
    found = True
    return json.dumps({"Status":"OK","Found":found})

  # Search for the gdun
  count = 0
  for gdun in gduns:
    if gdun['num'] == packet['gdun'] or packet['gdun'] in gdun['name']:
      prev_gdun_index.value = gdun_index.value
      gdun_index.value = count
      found = True
      break
    else:
      count += 1
  return json.dumps({"Status":"OK","Found":found})

# Get single customer gdun content
def rotating_gdun(value):
  with open('config.json') as config_file:
    config = json.load(config_file)
  gduns = config['gduns']
  return gduns[value]

def getArrayData(gdun):
  s3 = boto3.resource('s3',use_ssl=False,endpoint_url=ecs_url,aws_access_key_id=ecs_user_id,aws_secret_access_key=ecs_user_access_key,config=Config(s3={'addressing_style':'path'}))
  installsBucket = s3.Bucket('pacnwinstalls')
  installsObject = installsBucket.Object('{0}.json'.format(gdun)).get()
  array_data = json.loads(installsObject['Body'].read())
  return array_data['rows']

def get_expiring_data(array_data):
  data = array_data
  expiring = []
  today = time.mktime(time.localtime(time.time()))
  for array in data:
    if array['CONTRACT_SUBLINE_STATUS'] != "NA" and array['CONTRACT_SUBLINE_END_DATE'] != None:
      expiration_date = time.mktime(datetime.datetime.strptime(array['CONTRACT_SUBLINE_END_DATE'], "%Y-%m-%d %H:%M:%S").timetuple())
      days_til_expire = (expiration_date - today)/(60*60*24)
      if array['INSTALL_BASE_STATUS'] == 'Install' and days_til_expire < 120:
        expiring.append(array)
  return expiring

# DEPRECIATED - Left in to see what was previously condensed; also is incorrect formatin
def trimArrayCounts(counts):
  array_counts = counts
  counts = {"VNX": 0, "Symmetrix": 0, "XtremIO": 0, "Clariion": 0, "Isilon": 0, "Connectrix": 0, "Recoverpoint": 0,
            "Data Domain": 0, "Avamar": 0, "VPLEX": 0, "ScaleIO": 0, "ECS/ViPR": 0, "Other": 0
  }
  for array in array_counts:
    if "VNX" in array[0]:
      counts['VNX'] += array[1]
    elif "SYMMETRIX" in array[0]:
      counts['Symmetrix'] += array[1]
    elif "DATADOMAIN" in array[0]:
      counts['Data Domain'] += array[1]
    elif "ISILON" in array[0]:
      counts['Isilon'] += array[1]
    elif "XTREMIO" in array[0]:
      counts['XtremIO'] += array[1]
    elif "CONNECTRIX" in array[0]:
      counts['Connectrix'] += array[1]
    elif "RECOVERPOINT" in array[0]:
      counts['Recoverpoint'] += array[1]
    elif "AVAMAR" in array[0]:
      counts['Avamar'] += array[1]
    elif "VPLEX" in array[0]:
      counts['VPLEX'] += array[1]
    elif "CLARIION" in array[0]:
      counts['Clariion'] += array[1]
    elif "CELERRA" in array[0]:
      counts['Clariion'] += array[1]
    elif "VIPR" in array[0]:
      counts['ECS/ViPR'] += array[1]
    elif "SCALEIO" in array[0]:
      counts['ScaleIO'] += array[1]
    elif "ECS" in array[0]:
      counts['ECS/ViPR'] += array[1]
    else:
      counts['Other'] += array[1]
  return counts

def countArrays (data):
  counts= {}
  #
  # cycle through the array list
  #
  for array in data:
    #
    # verify it's installed
    #
    if array['INSTALL_BASE_STATUS'] == 'Install':
      #
      # Group together old product names
      #
      product_name = array['PRODUCT_FAMILY']
      if "SYMMETRIX" in product_name:
        product_name = "SYMMETRIX"
      elif "CENTERA" in product_name:
        product_name = "CENTERA"
      elif "CLARIION" in product_name:
        product_name = "CLARIION"
      elif "CELERRA" in product_name:
        product_name = "CELERRA"
      elif "AVAMAR" in product_name:
        product_name = "AVAMAR"
      elif "RECOVERPOINT" in product_name:
        product_name = "RECOVERPOINT"
      elif "DATADOMAIN" in product_name:
        product_name = "DATADOMAIN"
      elif "COMPUTING-NA" in product_name:
        product_name = "GREENPLUM"
      elif "CONNECTRIX" in product_name:
        product_name = "CONNECTRIX"
      elif "ISILON" in product_name:
        product_name = "ISILON"
      elif "XTREMIO" in product_name:
        product_name = "XTREMIO"
      elif "VPLEX" in product_name:
        product_name = "VPLEX"
      elif "VNX" in product_name:
        product_name = "VNX"
      elif "BUSTECH" in product_name:
        product_name = "MAINFRAME-TECH"
      elif "UNIFIED-DL" in product_name:
        product_name = "MAINFRAME-TECH"
      elif "DLM-DL" in product_name:
        product_name = "MAINFRAME-TECH"
      #
      # Clean out non-array components
      #
      elif "BULKSTORAGE" in product_name:
        continue
      elif "FLASH-NA" in product_name:
        continue
      elif "EDM-NA" in product_name:
        continue
      if array['CONTRACT_SUBLINE_STATUS'] == None:
        continue
      #
      # Add to the counts
      #
      try:
        counts[product_name] +=1
      except KeyError:
        counts[product_name] = 1
  return counts

def getSRData(gdun):
  s3 = boto3.resource('s3',use_ssl=False,endpoint_url=ecs_url,aws_access_key_id=ecs_user_id,aws_secret_access_key=ecs_user_access_key,config=Config(s3={'addressing_style':'path'}))
  srsBucket = s3.Bucket('pacnwsrs')
  srsObject = srsBucket.Object('{0}.json'.format(gdun)).get()
  sr_data = json.loads(srsObject['Body'].read())
  return sr_data

def sev1_data(sr_data):
  data = sr_data["rows"]
  sev1_data = []
  sev1_data.append({ "col1":"SR Num. ", "col2": "Age", "col3": "Family   ", "col4": "Site Name" })
  for sr in data:
    if sr['SEV'] == 'S1':
      sev1_data.append({ "col1": sr['SR'] , "col2": int(round(float(sr['Age']))), "col3": sr['Family'] , "col4": sr['CS Customer Name'] })
  return sev1_data

def countSRBySev(sr_data):
  data = sr_data["rows"]
  counts = {}
  for sr in data:
    try:
      counts[sr['SEV']] +=1
    except KeyError:
      counts[sr['SEV']] = 1
  return counts

# Primary job function
def rotating():
  # Get a customer to display
  gdun_data = rotating_gdun(gdun_index.value)
  gdun = gdun_data['num']
  cust_name = gdun_data['name']
  cust_logo = gdun_data['image']

  # Use the previous index if there is one
  if prev_gdun_index.value >= 0:
    gdun_index.value = prev_gdun_index.value
    prev_gdun_index.value = -1
  else:
    gdun_index.value = gdun_data['next-index']

  installs_url = config['dash_url'] + ":1337/csv/installreport/" + gdun
  sev1_url = config['dash_url'] + ":1337/csv/sev1report/" + gdun
  sr_url = config['dash_url'] + ":1337/csv/srreport/" + gdun


  array_data = getArrayData(gdun)
  expiring_data = get_expiring_data(array_data)
  num_expiring = len(expiring_data)
  expiring_counts = countArrays(expiring_data)
  sr_data = getSRData(gdun)
  array_counts = countArrays(array_data)
  array_hash = []
  for array in array_counts:
    array_hash.append({ "label": array, "value": array_counts[array], "link": installs_url })

  expiring_hash = []
  for array in expiring_counts:
    expiring_hash.append( { "label": array, "value": expiring_counts[array] })

  sr_array = []
  sr_array.append(["SR Severity","Quantity"])

  if not sr_data['rows']:
    sr_counts = {}
    sev1_hash = []
  else:
    sr_counts = countSRBySev(sr_data)
    sev1_hash = sev1_data(sr_data)
    for sr in sr_counts:
      sr_array.append([sr,sr_counts[sr]])

  r = requests.post('{0}/widgets/api_mychart'.format(config['dash_url']), data = json.dumps({"auth_token": auth_token,"slices": sr_array}))
  r = requests.post('{0}/widgets/api_total_srs'.format(config['dash_url']), data = json.dumps({"auth_token": auth_token,"value": len(sr_data['rows']), "link": sr_url}))
  r = requests.post('{0}/widgets/api_array_counts'.format(config['dash_url']), data = json.dumps({"auth_token": auth_token,"items": array_hash}))
  try:
    r = requests.post('{0}/widgets/api_sev_1s'.format(config['dash_url']), data = json.dumps({"auth_token": auth_token,"value": sr_counts['S1'], "link": sev1_url}))
  except KeyError:
    r = requests.post('{0}/widgets/api_sev_1s'.format(config['dash_url']), data = json.dumps({"auth_token": auth_token,"value": 0, "link": sev1_url}))
  r = requests.post('{0}/widgets/api_picture'.format(config['dash_url']), data = json.dumps({"auth_token": auth_token,"image": cust_logo}))
  r = requests.post('{0}/widgets/api_sev1_data'.format(config['dash_url']), data = json.dumps({"auth_token": auth_token,"items": sev1_hash, "link": sev1_url}))
  r = requests.post('{0}/widgets/api_num_expiring'.format(config['dash_url']), data = json.dumps({"auth_token": auth_token,"value": num_expiring}))
  r = requests.post('{0}/widgets/api_expiring_counts'.format(config['dash_url']), data = json.dumps({"auth_token": auth_token,"items": expiring_hash}))

  # send_event('mychart', slices: sr_array)
  # send_event('total_srs', { value: sr_data["rows"].length(), link: sr_url})
  # send_event('array_counts',   { items: array_hash.values })
  # send_event('sev_1s', { value: sr_counts['S1'] || 0, link: sev1_url})
  # send_event('picture', image: cust_logo)
  # send_event('sev1_data', { items: sev1_hash.values, link: sev1_url })
  # send_event('num_expiring', value: num_expiring)
  # send_event('expiring_counts', { items: expiring_hash.values })
