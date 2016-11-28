import requests
import json
import urllib
import pprint
from datetime import date, timedelta
import statistics as st
import itertools as it

#payload, date and time to be included
#date format: "2016-05-20",
#time format: "23:28:00"
ROUTEQ = """
{
  plan(from: {lat: %s, lon: %s}, 
       to: {lat: %s, lon: %s},
       modes: "BUS,TRAM,RAIL,SUBWAY,FERRY,WALK",
       walkReluctance: 2.1, walkBoardCost: 600,
       minTransferTime: 180, walkSpeed: 1.2,
       numItineraries: 11,
       date: "%s",
       time: "%s"
       ) {
   itineraries{
      startTime
      walkDistance
      duration
      legs {
        mode
        startTime
        endTime
        duration       
        distance
        from {stop {
          gtfsId
        }}
        trip {tripHeadsign}
        route {
          shortName            
        }
        }       
    }
  }  
}"""      
  

# for checking walk duration and distance
WALKQ = """
{
  plan(from: {lat: %s, lon: %s}, 
       to: {lat: %s, lon: %s},
       modes: "WALK",
       ) {
   itineraries{
      startTime
      walkDistance
      duration       
    }
  }  
}"""  

# date in format e.g. "20160929"
STOPQ = """
{
  stop(id: "%s") {
    stoptimesForServiceDate(date: "%s") { 
      pattern {
        headsign
        route {
          shortName
          mode
        }
      }
      stoptimes {
        scheduledDeparture
      }
    }
  } 
}"""


COLORS = [[166, 206, 227], [43, 128, 184], [150, 203, 145], [81, 175, 66], [184, 156, 116],\
          [237, 80, 81], [240, 112, 71], [253, 163, 63], [237, 144, 71], [174, 144, 197],\
          [134, 97, 153]]

def runQuery(payload):
    req = requests.Request('POST', "https://api.digitransit.fi/" \
                           "routing/v1/routers/hsl/index/graphql", data=payload)
    prepped = req.prepare()
    prepped.headers['Content-Type']='application/graphql'
    s = requests.Session()
    resp = s.send(prepped)

    if resp.status_code == 200: #
        try:
            reslist = resp.json()
            return reslist
        except:
            return None
    else:
        return None

# Input: address as string
# Output: (latitude, longitude) or None
# Gives a latitude longitude pair for a given text address
def getLocation(address):
    payload = "http://api.digitransit.fi/geocoding/v1/search?text=" + \
              urllib.parse.quote(address) # + "&size=1"
    payload = payload + "&focus.point.lat=60.169856&focus.point.lon=24.938379&size=5"
    data = requests.get(payload)
    json_reply = data.json()
    try:
        results = []
        for i in json_reply['features']:
            coord = i['geometry']['coordinates']
            place = i['properties']['label']
            confidence = i['properties']['confidence']
            ok_cities = ["Espoo", "Helsinki", "Kauniainen", "Vantaa", "Kirkkonummi"]
            # print("Debug: %s and coords %s" % (place,coord)) 
            for city in ok_cities:
                if city in place:
                    results.append( (confidence, place, coord[1],coord[0]))
                    break

        return results

    except:
        return None

# reverse search mainly for testing purposes
def getStreetName(coords):
    lat, lon = coords
    lat = str(lat)
    lon = str(lon)
    payload = "http://api.digitransit.fi/geocoding/v1/reverse?point.lat=" + \
              lat + "&point.lon=" + lon +"&size=1"
    response = requests.get(payload)

    # try to find a specific field in json respons. Return None if not successful
    try:
        return response.json()['features'][0]['properties']['label']
    except:
        return None

# input is the results from runRouteQ
def analyseRouteQ(reslist):        
    
    singleroutes = {}
    longerroutes = {}
    walkDistance = 0
    for route in reslist:
        duration = route['duration']
        startTime = route['startTime'] # unit is [microseconds from Unix epoch]
        if route['legs'][0]['mode'] == 'WALK': # It's possible, that the trip starts from station/stop. Hence test
            startShift = route['legs'][0]['duration'] # unit is [s]
        else:
            startShift = 0
            walkDistance = route['walkDistance'] # unit is [m]

        legs = [x for x in route['legs'] if x['mode'] != 'WALK'] # for calculating legs without walking
        shortis = [x['route']['shortName'] if x['route']['shortName'] else x['mode'] \
                   + ' (' + x['trip']['tripHeadsign'] + ')' \
                   for x in route['legs'] if x['route'] != None]       

        if len(legs) < 2 and shortis:
            shortName = shortis[0]

            mode = legs[0]['mode']
            gtfsId = legs[0]['from']['stop']['gtfsId']
            if not shortName in singleroutes.keys():
                singleroutes[shortName] = {'gtfsId':gtfsId, 'mode':mode, \
                                           'duration':duration, 'startTime':startTime,\
                                           'startShift':startShift,\
                                           'walkDistance':walkDistance}

        elif shortis:
            try:
                shortNames = '+'.join(shortis)
            except:
                pprint.pprint(shortis)
                pprint.pprint(route)
            if not shortNames in longerroutes.keys():
                longerroutes[shortNames] = route                    

    return (singleroutes,longerroutes)


# we take a singleroute, and check for stop data
def analyseSingle(shortName,data,weekday=1):

    today = date.today()
    days = [today + timedelta(days=x) for x in range(1,8)]
    days = {x.isoweekday():x.strftime("%Y%m%d") for x in days}  

    gtfsId = data['gtfsId']

    payload = STOPQ % (gtfsId, days[weekday]) # 1 = monday
    temp = runQuery(payload)

    results = temp['data']['stop']['stoptimesForServiceDate']

    starts = next(x['stoptimes'] for x in results if \
                  x['pattern']['route']['shortName']==shortName)
    starts2 = [x['scheduledDeparture']-data['startShift'] for x in starts]

    return [(start,start+data['duration'],data['duration'], \
             data['walkDistance'],shortName) for start in starts2]

# combine multi legged route into one
def analyseMulti(name, legs,weekday=1):
    today = date.today()
    days = [today + timedelta(days=x) for x in range(1,8)]
    days = {x.isoweekday():x.strftime("%Y%m%d") for x in days}  

    datte = days[weekday]

    legs = legs['legs']
    if legs[0]['mode'] == 'WALK':
        startshift = legs[0]['duration']
    else:
        startshift = 0

    stopinfo = lambda x: (x['from']['stop']['gtfsId'], x['route']['shortName'], \
                          x['trip']['tripHeadsign'])
    stops2 = [stopinfo(x) for x in legs if x['mode'] != 'WALK']

    dures = [x['duration'] for x in legs]
    stopids = [x['from']['stop']['gtfsId'] if x['from']['stop'] else None for x in legs]
    stops3 = zip(stops2,it.count(0))

    tripleinfo = lambda x,y: (x, sum(dures[:stopids.index(x[0])]), \
                              sum(dures[:stopids.index(x[0])+1]) + y*180)
    triple = [tripleinfo(x,y) for x,y in stops3]

    if legs[-1]['mode'] == 'WALK':
        endwalk = legs[-1]['duration']
    else:
        endwalk = 0

    # startshift is walk time before first stop
    # endwalk is walk time from last stop to destination

    # check first possible starts
    firststop = triple[0]

    payload = STOPQ % (firststop[0][0], datte)
    reply = runQuery(payload)['data']['stop']['stoptimesForServiceDate'] 

    # check for start times
    starts = stopStarts(reply, firststop[0][1], firststop[0][2])
    ends = [x + firststop[2]- firststop[1] for x in starts]

    # loop over possible stops
    for stop,a,b in triple[1:]:
        payload = STOPQ % (stop[0], datte)
        reply = runQuery(payload)['data']['stop']['stoptimesForServiceDate'] 
        schedules = stopStarts(reply, stop[1], stop[2])

        if(len(schedules) == 0):

            # for debugging. Like a pro!
            pprint.pprint(stop[1])
            pprint.pprint(stop[2])
            pprint.pprint(reply)

        ends = [next(it.dropwhile(lambda y: y < x, schedules)) \
                for x in ends if x < schedules[-1]]
        ends = [x + b - a for x in ends]

    # Final info:
    starts = [x - startshift for x in starts]
    ends = [x + endwalk for x in ends]

    return [(a,b,b-a, 0,name) for a,b in zip(starts,ends)]


def stopStarts(reply, shortName, headsign):
    starts = []
    for route in reply:
        mode = route['pattern']['route']['mode'] 
        if mode == 'TRAM' or mode == 'SUBWAY':
            if route['pattern']['headsign'] == headsign:
                starts.extend(route['stoptimes'])
        else:            
            if route['pattern']['route']['shortName']== shortName:
                starts.extend(route['stoptimes'])

    starts = [x['scheduledDeparture'] for x in starts]
    starts.sort() # we sort scheduled departures, because they might not be inorder
    return starts

def styleLegendText(x,times):
    if '+' in x:
        return '%s, duration: %.0f-%.0f min; median: %.0f min' % \
               (x, min(times)/60, max(times)/60, st.median(times)/60)
    else:
        return '%s, duration: %.0f min' % (x, min(times)/60)


def makeResults(alltrips):
    # alltrips = [start,end,duration,walking,name]

    # we flatten the list of lists
    trips = [item for sublist in alltrips for item in sublist]

    # next we filter non-optimal routes out
    betterExists = lambda x: True if next((y for y in trips \
                                           if x[0] < y[0] and y[1] <= x[1]),None) else False

    filteredlist = [x for x in trips if not betterExists(x)]

    # unique names
    names = list(set(item[-1] for item in filteredlist))        
    names.sort()

    # we recreate list of lists for plotting purposes
    startsAll = [([int(item[0]/3600) for item in filteredlist if item[4]==x],x) for x in names]
    startsAll2 = [([y[0].count(x) for x in range(28)],y[1]) for y in startsAll]

    durations = [(x,[item[2] for item in filteredlist if item[4]==x]) for x in names]
    durations = [styleLegendText(x,times) for x,times in durations]

    colors = []
    cborders = []

    for i, items in enumerate(startsAll2):
        c = COLORS[i]
        colors.append('rgba(%i, %i, %i, 0.7)' % (c[0], c[1], c[2]))
        cborders.append('rgba(%i, %i, %i, 0.9)' %  (c[0], c[1], c[2]))

    return zip(startsAll2, durations, colors, cborders)

        
# create dictionary to use with jsonify
def styleChartjs(data, route):

    labels = ['%s-%s' % (x,x+1) for x in range(28)]
    datasets = [{'label':label, 'data':line[0], 'backgroundColor':c, \
                 'borderColor':b, 'borderWidth':1} for line,label,c,b in data]

    return {'labels':labels, 'datasets':datasets, 'route':route} 


# simple helper function to do the magic
def tellResults(startcoord, poicoord, weekday=1):
    
    today = date.today()
    days = [today + timedelta(days=x) for x in range(1,8)]
    days = {x.isoweekday():x.strftime("%Y-%m-%d") for x in days}
    time = "07:30:00"
    datte = days[weekday] #1 is for Monday

    # check for value with highest confidence (confidence, place, coord, coord2)

    startlist = sorted(startcoord, key=lambda c: c[0])
    poilist = sorted(poicoord, key=lambda c: c[0])
    start = startlist[-1][2:]
    poi = poilist[-1][2:]

    route = '<p>Results from "%s" to "%s"</p>' % (startlist[-1][1], poilist[-1][1])
    pprint.pprint(route)
    pprint.pprint(startlist)
    pprint.pprint(poilist)

    payload = ROUTEQ % (start[0],start[1],poi[0],poi[1],datte,time)

    # (durations,singleroutes,longerroutes)
    result = runQuery(payload)['data']['plan']['itineraries'] 
    (singles,longer) = analyseRouteQ(result)
    
    alltimes = [analyseSingle(k,v,weekday) for k,v in singles.items()]
    alltimes.extend([analyseMulti(k,v,weekday) for k,v in longer.items()])
            
    outcome = makeResults(alltimes)
    results = styleChartjs(outcome, route)
    
    return results
