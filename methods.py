### All imports ###
import sched, time
import json
import multiprocessing
import requests
import datetime
from requests_ntlm import HttpNtlmAuth

### Load config files and declare globals ###
with open('config.json') as config_file:
  config = json.load(config_file)

username = config['username']
password = config['password']
domain = config['domain']
iburl1 = config['iburl']
iburl2 = config['iburl2']
srurl = config['srurl']
srurl2 = config['srurl2']

gdun_index = multiprocessing.Value('i', 0)

### Methods ###

# listener to give visibility into job completetion
def error_listener(event):
  if event.exception:
    print("The job failed...{0}".format(event.exception))
    print("{0}".format(event.traceback))
  else:
    print("The job worked!")

# Function to set gdun index variable
def set_next_index(gdun):
  gdun_index.value = gdun

# Get single customer gdun content
def rotating_gdun(value):
  with open('config.json') as config_file:
    config = json.load(config_file)
  gduns = config['gduns']
  return gduns[value]

def getArrayData(gdun):
  url = iburl1+str(gdun)+iburl2
  r = requests.get(url,auth=HttpNtlmAuth('{0}\\{1}'.format(domain,username),password))
  if r.status_code == 200:
    array_data = r.json()
  return array_data

def get_expiring_data(array_data):
  data = array_data["rows"]
  expiring = []
  today = time.mktime(time.localtime(time.time()))
  for array in data:
    if array['CONTRACT_SUBLINE_STATUS'] != "NA":
      expiration_date = time.mktime(datetime.datetime.strptime(array['CONTRACT_SUBLINE_END_DATE'], "%Y-%m-%d %H:%M:%S").timetuple())
      days_til_expire = (expiration_date - today)/(60*60*24)
      if array['INSTALL_BASE_STATUS'] == 'Install' and days_til_expire < 120:
        expiring.append(array)
  return expiring

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
  for array in data:
    if array['INSTALL_BASE_STATUS'] == 'Install':
      if counts[array['PRODUCT_FAMILY']]:
        counts[array['PRODUCT_FAMILY']] +=1
      else:
        counts[array['PRODUCT_FAMILY']] = 1
  return counts

def getSRData(gdun):
  url = srurl + str(gdun) + srurl2
  r = requests.get(url,auth=HttpNtlmAuth('{0}\\{1}'.format(domain,username),password))
  if r.status_code == 200:
    sr_data = r.json()
  return sr_data

def sev1_data(sr_data):
  data = sr_data["rows"]
  sev1_data['Headers'] = { col1: 'SR Num. ', col2: 'Age', col3: 'Family   ', col4: 'Site Name' }
  count = 1
  for sr in data:
    if sr['Sev'] == 'S1':
      sev1_data[count] = { col1: sr['SR_NUMBER'] , col2: sr['Age'].to_i , col3: sr['Family'] , col4: sr['CS Customer Name'] }
      count += 1
  return sev1_data

def countSRBySev(sr_data):
  data = sr_data["rows"]
  counts = {}
  for sr in data:
    if counts[sr['Sev']]:
      counts[sr['Sev']] +=1
    else:
      counts[sr['Sev']] = 1
  return counts

# Primary job function
def rotating():
  # Get a customer to display
  gdun_data = rotating_gdun(gdun_index.value)
  gdun = gdun_data['num']
  cust_name = gdun_data['name']
  cust_logo = gdun_data['image']
  gdun_index.value = gdun_data['next-index']

  installs_url = config['dash_url'] + ":1337/csv/installreport/" + gdun
  sev1_url = config['dash_url'] + ":1337/csv/sev1report/" + gdun
  sr_url = config['dash_url'] + ":1337/csv/srreport/" + gdun


  array_data = getArrayData(gdun)
  expiring_data = get_expiring_data(array_data)
  num_expiring = expiring_data.length
  expiring_counts = trimArrayCounts(countArrays(expiring_data))
  sr_data = getSRData(gdun)
  array_counts = trimArrayCounts(countArrays(array_data))
  sev1_hash = sev1_data(sr_data)
  array_hash = {}
  for array in array_counts:
    array_hash[array[0]] = { label: array[0], value: array[1].to_s, link: installs_url }

  expiring_hash = {}
  for array in expiring_counts:
    expiring_hash[array[0]] = { label: array[0], value: array[1].to_s }

  sr_counts = countSRBySev(sr_data)
  sr_array = []
  sr_array.append(['SR Severity', 'Quantity'])
  for array in sr_counts:
    sr_array.append([array[0],array[1]])

  r = requests.post('{0}:3030/widgets/api_mychart'.format(config['dash_url']), data = {'auth_token': 'YOUR_AUTH_TOKEN','slices': sr_array})
  r = requests.post('{0}:3030/widgets/api_total_srs'.format(config['dash_url']), data = {'auth_token': 'YOUR_AUTH_TOKEN','value': sr_data["rows"].length(), 'link': sr_url})
  r = requests.post('{0}:3030/widgets/api_array_counts'.format(config['dash_url']), data = {'auth_token': 'YOUR_AUTH_TOKEN','items': array_hash})
  if sr_counts['S1'] is None:
    sr_counts['S1'] = 0
  r = requests.post('{0}:3030/widgets/api_sev_1s'.format(config['dash_url']), data = {'auth_token': 'YOUR_AUTH_TOKEN','value': sr_counts['S1'], 'link': sev1_url})
  r = requests.post('{0}:3030/widgets/api_picture'.format(config['dash_url']), data = {'auth_token': 'YOUR_AUTH_TOKEN','image': cust_logo})
  r = requests.post('{0}:3030/widgets/api_sev1_data'.format(config['dash_url']), data = {'auth_token': 'YOUR_AUTH_TOKEN','items': sev1_hash, 'link': sev1_url})
  r = requests.post('{0}:3030/widgets/api_num_expiring'.format(config['dash_url']), data = {'auth_token': 'YOUR_AUTH_TOKEN','value': num_expiring})
  r = requests.post('{0}:3030/widgets/api_expiring_counts'.format(config['dash_url']), data = {'auth_token': 'YOUR_AUTH_TOKEN','items': expiring_hash})

  # send_event('mychart', slices: sr_array)
  # send_event('total_srs', { value: sr_data["rows"].length(), link: sr_url})
  # send_event('array_counts',   { items: array_hash.values })
  # send_event('sev_1s', { value: sr_counts['S1'] || 0, link: sev1_url})
  # send_event('picture', image: cust_logo)
  # send_event('sev1_data', { items: sev1_hash.values, link: sev1_url })
  # send_event('num_expiring', value: num_expiring)
  # send_event('expiring_counts', { items: expiring_hash.values })
