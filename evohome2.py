# Script to monitor and read temperatures from Honeywell EvoHome Web API and send them to Plotly

# Load required libraries
import requests
import json
from datetime import datetime
import time
import plotly
import plotly.plotly as py
import plotly.tools as tls
from plotly.graph_objs import *
import yaml

with open("config.yml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile)

pyuser = cfg['plotly']['user']
pypassword = cfg['plotly']['password']

evouser = cfg['evohome']['user']
evopassword = cfg['evohome']['password']

print "Setting up plotly"

# Sign in
py.sign_in(pyuser, pypassword)

# Stream tokens from plotly
tls.set_credentials_file(stream_ids=[
    "fsz2kt963q",
    "f5hohqqvre",
    "amhp0uwfyu",
    "hqyihgnpif",
    "ckxhc74zeq",
    "l6wsom643d",
    "q0ndkcivxi",
    "owdi3hvg0b",
    "i9z3r6icwk",
    "rdxurbkamu",
    "77c0v4hc3z",
    "lbvvdla29y",
    "mba4vvdg71",
    "9n0lstrhx1",
    "b3ormtxu7v",
    "b3ay7b0nh0",
    "qoka9dp6ki",
    "y16szpsxs7",
    "bewprj82gh",
    "e33yvk0skn",
    "h2dztjvliz",
    "1kf11rdcg7",
    "cegl8bze75",
    "8wd1yyihke",
    "lfxzxknxzg",
    "4topw0l3oe"
])
stream_ids = tls.get_credentials_file()['stream_ids']

print "Signing into TotalConnectComfort (EvoHome)"

# Initial JSON POST to the website to return your userdata
url = 'https://rs.alarmnet.com/TotalConnectComfort/WebAPI/api/Session'
#url = 'https://204.141.56.180/TotalConnectComfort/WebAPI/api/session'
postdata = {'Username':evouser, 'Password':evopassword,'ApplicationId':'91db1612-73fd-4500-91b2-e63b069b185c'}
headers = {'content-type':'application/json'}
response = requests.post(url,data=json.dumps(postdata),headers =headers)
#print response.content
userinfo = json.loads(response.content)

# Extract the sessionId and your userid from the response
#print(userinfo)
userid = userinfo['userInfo']['userID']
sessionId = userinfo['sessionId']

print "Finding devices"

# Next, using your userid, get all the data back about your site
url = 'https://rs.alarmnet.com/TotalConnectComfort/WebAPI/api/locations?userId=%s&allData=True' % userid
headers['sessionId'] = sessionId
response = requests.get(url,data=json.dumps(postdata),headers =headers)
fullData = json.loads(response.content.decode('utf-8'))[0]

print "Initialising Plots"

# We make a plot for every room
i=0
for device in fullData['devices']:
    temp_stream_id = stream_ids[i]
    set_stream_id = stream_ids[i+1]
    i=i+2
    temp_stream = Stream(
        token=temp_stream_id,
        maxpoints=2016
    )
    set_stream = Stream(
        token=set_stream_id,
        maxpoints=2016
    )
    trace1 = Scatter(
           x=[],
           y=[],
           mode='lines+markers',
           line=Line(
               shape='spline'
               ),
           stream = temp_stream
           )
    trace2 = Scatter(
            x=[],
            y=[],
            mode='lines+markers',
            line=Line(
                shape='spline'
                ),
            stream = set_stream
            )

    data = Data([trace1, trace2])
    layout = Layout(title=device['name'], xaxis1=XAxis(title="Date"), yaxis1=YAxis(title="Temperature"))
    fig = Figure(data=data, layout=layout)
    py.plot(fig, filename=device['name'], fileopt='extend', auto_open=False)

# Infinite loop every 5 minutes, send temperatures to plotly
while True:
    try:
        print "Grabbing data"
        # Next, using your userid, get all the data back about your site
        url = 'https://rs.alarmnet.com/TotalConnectComfort/WebAPI/api/locations?userId=%s&allData=True' % userid
        headers['sessionId'] = sessionId
        response = requests.get(url,data=json.dumps(postdata),headers =headers)
    
        capturetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        fullData = json.loads(response.content.decode('utf-8'))[0]

        # Get current time and then send all thermostat readings to plotly
        j=0
        for device in fullData['devices']:
            temp_stream_id = stream_ids[j]
            set_stream_id = stream_ids[j+1]
            j+=2
            t = py.Stream(temp_stream_id)
            s = py.Stream(set_stream_id)
            #print temp_stream_id
            #print set_stream_id
            t.open()
            s.open()
            tijd = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
            try:
                temperature = device['thermostat']['indoorTemperature']
            except KeyError:
                print "couldnt decode temperature"
            else:
                t.write(dict(x=capturetime, y=temperature))
        
            try:
                if "heatSetpoint" in device['thermostat']['changeableValues']:
                    setPoint = device['thermostat']['changeableValues']['heatSetpoint']['value']
                    s.write(dict(x=capturetime, y=setPoint))
            except KeyError:
                print "Couldnt decode heatSetpoint" 
            t.close()
            s.close()
    except Exception as ex:
        print ex
    else:
        print "Sleeping"
        time.sleep(300)
