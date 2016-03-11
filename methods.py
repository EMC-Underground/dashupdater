### All imports ###
import sched, time
import json
import multiprocessing
import request
from requests_ntlm import HttpNtlmAuth

### Load config files and declare globals ###
with open('config.json') as config_file:
  config = json.load(config_file)

username = config['username']
password = config['password']
domain = config['domain']
url1 = config['iburl']
url2 = config['iburl2']

gdun_index = multiprocessing.Value('i', 0)

### Methods ###

# listener to give visibility into job completetion
def error_listener(event):
  if event.exception:
    print("The job failed...{0}".format(event.exception))
  else
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
  url = url1+str(gdun)+url2
  r = requests.get(url,auth=HttpNtlmAuth('{0}\\{1}'.format(domain,username),password))
  if r.status_code == 200:
    array_data = r.json()
  return array_data

def Arrays.get_expiring_data(array_data)
  data = array_data["rows"]
  expiring = []
  today = time.mktime(time.localtime(time.time()))
  for array in data:
    if array['CONTRACT_SUBLINE_STATUS'] != "NA":
      expiration_date = time.mktime(datetime.datetime.strptime(myDate, "%Y-%m-%d %H:%M:%S").timetuple())
      days_til_expire = (expiration_date - today)/(60*60*24)
      if array['INSTALL_BASE_STATUS'] == 'Install' && days_til_expire < 120
        expiring.append(array)
  return expiring

# Primary job function
def rotating():
  # Get a customer to display
  gdun_data = rotating_gdun(gdun_index.value)
  gdun = gdun_data['num']
  cust_name = gdun_data['name']
  cust_logo = gdun_data['image']
  gdun_index.value = gdun_data['next-index']

  installs_url = config['dash_url'] + ":1337/csv/installreport/" + gdun.to_s
  sev1_url = config['dash_url'] + ":1337/csv/sev1report/" + gdun.to_s
  sr_url = config['dash_url'] + ":1337/csv/srreport/" + gdun.to_s


  array_data = getArrayData(gdun)
  expiring_data = get_expiring_data(array_data)
  puts expiring_data
  num_expiring = expiring_data.length
  expiring_counts = Arrays.trimArrayCounts(Arrays.get_expired_counts(expiring_data))
  sr_data = Sr.getSRData(gdun)
  array_counts = Arrays.trimArrayCounts(Arrays.getArrayCounts(array_data))
  sev1_hash = Sr.sev1_data(sr_data)
  array_hash = Hash.new({ value: 0 })
  array_counts.each do |array|
    array_hash[array[0]] = { label: array[0], value: array[1].to_s, link: installs_url }

  expiring_hash = Hash.new({ value: 0 })
  expiring_counts.each do |array|
    expiring_hash[array[0]] = { label: array[0], value: array[1].to_s }

  test_hash = Hash.new()
  puts sev1_hash
  sr_counts = Sr.countSRBySev(sr_data)
  sr_array = []
  sr_array.push ['SR Severity', 'Quantity']
  sr_counts.each do |array|
    sr_array.push [array[0],array[1]]

  send_event('mychart', slices: sr_array)
  send_event('total_srs', { value: sr_data["rows"].length(), link: sr_url})
  send_event('array_counts',   { items: array_hash.values })
  send_event('sev_1s', { value: sr_counts['S1'] || 0, link: sev1_url})
  send_event('picture', image: cust_logo)
  send_event('sev1_data', { items: sev1_hash.values, link: sev1_url })
  send_event('num_expiring', value: num_expiring)
  send_event('expiring_counts', { items: expiring_hash.values })

def getSRData(gdun):
  url = @url1+gdun+@url2
  request = HTTPI::Request.new
  request.url = url
  request.auth.ntlm(@username, @pass, @domain)
  response = HTTPI.get(request)
  sr_data = JSON.parse(response.body)
  return sr_data

def countSRBySev(sr_data):
  data = sr_data
  data = data["rows"]
  counts = {}
  data.each do |sr|
  if counts[sr['Sev']]
    counts[sr['Sev']] +=1
  else
    counts[sr['Sev']] = 1
  return counts

def Sr.sev1_data(sr_data):
  data = sr_data
  data = data["rows"]
  sev1_data = Hash.new()
  sev1_data['Headers'] = { col1: 'SR Num. ', col2: 'Age', col3: 'Family   ', col4: 'Site Name' }
  count = 1
  data.each do |sr|
    if sr['Sev'] == 'S1'
      sev1_data[count] = { col1: sr['SR_NUMBER'] , col2: sr['Age'].to_i , col3: sr['Family'] , col4: sr['CS Customer Name'] }
      count+=1
  return sev1_data
