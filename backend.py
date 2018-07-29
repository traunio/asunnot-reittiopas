import urllib
import pprint
from datetime import date, timedelta
import statistics as st
import itertools as it
import re
import requests


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
       numItineraries: 9,
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
       walkSpeed: 1.2,
       numItineraries: 1
       ) {
   itineraries{
      walkDistance
      duration      
<    }
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

# These are the colors used in generating the graph in Chart.js
COLORS = [[166, 206, 227], [43, 128, 184], [150, 203, 145], [81, 175, 66], [184, 156, 116],\
          [237, 80, 81], [240, 112, 71], [253, 163, 63], [237, 144, 71], [174, 144, 197],\
          [134, 97, 153]]

def run_query(payload):
    req = requests.Request('POST', "https://api.digitransit.fi/" \
                           "routing/v1/routers/hsl/index/graphql", data=payload)
    prepped = req.prepare()
    prepped.headers['Content-Type'] = 'application/graphql'
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

def get_location(address):
    """
    Input: address as string
    Output: (latitude, longitude) or None
    Gives a latitude longitude pair for a given text address
    """

    # check for naughty address
    match = re.search('["(){}]', address)
    if match:
        return None

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

            results.append((confidence, place, coord[1], coord[0]))

        return results

    except:
        return None

# reverse search mainly for testing purposes
def get_streetname(coords):
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
def analyse_routeq(reslist):

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
            if shortNames not in longerroutes.keys():
                longerroutes[shortNames] = route

    return (singleroutes, longerroutes)


# we take a singleroute, and check for stop data
def analyse_single(shortName, data, weekday=1):

    today = date.today()
    days = [today + timedelta(days=x) for x in range(1, 8)]
    days = {x.isoweekday():x.strftime("%Y%m%d") for x in days}

    gtfsId = data['gtfsId']

    payload = STOPQ % (gtfsId, days[weekday]) # 1 = monday
    temp = run_query(payload)

    results = temp['data']['stop']['stoptimesForServiceDate']

    starts = next(x['stoptimes'] for x in results if \
                  x['pattern']['route']['shortName'] == shortName)
    starts2 = [x['scheduledDeparture']-data['startShift'] for x in starts]

    return [(start, start+data['duration'], data['duration'], \
             data['walkDistance'], shortName) for start in starts2]

# combine multi legged route into one
def analyse_multi(name, legs, weekday=1):
    today = date.today()
    days = [today + timedelta(days=x) for x in range(1, 8)]
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
    stops3 = zip(stops2, it.count(0))

    tripleinfo = lambda x, y: (x, sum(dures[:stopids.index(x[0])]), \
                              sum(dures[:stopids.index(x[0])+1]) + y*180)
    triple = [tripleinfo(x, y) for x, y in stops3]

    if legs[-1]['mode'] == 'WALK':
        endwalk = legs[-1]['duration']
    else:
        endwalk = 0

    # startshift is walk time before first stop
    # endwalk is walk time from last stop to destination

    # check first possible starts
    firststop = triple[0]

    payload = STOPQ % (firststop[0][0], datte)
    reply = run_query(payload)['data']['stop']['stoptimesForServiceDate']

    # check for start times
    starts = stop_starts(reply, firststop[0][1], firststop[0][2])
    ends = [x + firststop[2]- firststop[1] for x in starts]

    # loop over possible stops
    for stop, a, b in triple[1:]:
        payload = STOPQ % (stop[0], datte)
        reply = run_query(payload)['data']['stop']['stoptimesForServiceDate']
        schedules = stop_starts(reply, stop[1], stop[2])

        if not schedules:

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

    return [(a, b, b-a, 0, name) for a, b in zip(starts, ends)]


def stop_starts(reply, shortName, headsign):
    starts = []
    for route in reply:
        mode = route['pattern']['route']['mode']
        if mode == 'TRAM' or mode == 'SUBWAY':
            if route['pattern']['headsign'] == headsign:
                starts.extend(route['stoptimes'])
        else:
            if route['pattern']['route']['shortName'] == shortName:
                starts.extend(route['stoptimes'])

    starts = [x['scheduledDeparture'] for x in starts]
    starts.sort() # we sort scheduled departures, because they might not be inorder
    return starts

def style_legend_text(x, times):
    if '+' in x:
        if int(min(times)/60) != int(max(times)/60): # if durations differ, give more info
            return '%s, kesto: %.0f-%.0f min; mediaani: %.0f min' % \
                (x, min(times)/60, max(times)/60, st.median(times)/60)

    return '%s, kesto: %.0f min' % (x, min(times)/60)


def make_results(alltrips):
    """
    alltrips = [start,end,duration,walking,name]
    """

    # we flatten the list of lists
    trips = [item for sublist in alltrips for item in sublist]

    # next we filter non-optimal routes out
    betterExists = lambda x: True if next((y for y in trips \
                                           if x[0] < y[0] and y[1] <= x[1]), None) else False

    filteredlist = [x for x in trips if not betterExists(x)]

    # unique names
    names = list(set(item[-1] for item in filteredlist))
    names.sort()

    # we recreate list of lists for plotting purposes
    startsAll = [([int(item[0]/3600) for item in filteredlist if item[4] == x], x) for x in names]
    startsAll2 = [([y[0].count(x) for x in range(28)], y[1]) for y in startsAll]

    durations = [(x, [item[2] for item in filteredlist if item[4] == x]) for x in names]
    durations = [style_legend_text(x, times) for x, times in durations]

    colors = []
    cborders = []

    for i, items in enumerate(startsAll2):
        c = COLORS[i]
        colors.append('rgba(%i, %i, %i, 0.7)' % (c[0], c[1], c[2]))
        cborders.append('rgba(%i, %i, %i, 0.9)' %  (c[0], c[1], c[2]))

    return list(zip(startsAll2, durations, colors, cborders))

def style_chart_js(data, route):
    """
    Creates dictionary to use with jsonify
    data = [line, label, c ,b], line[0] = [vuorolkm], label = "linja", c ja b värejä 
    """

    start = 27  # 
    end = 0
    for line, label, c, b in data:
        start = min(start, next(i for i, x in enumerate(line[0]) if x!=0) )
        i = 27
        while line[0][i]==0 and i >= end:
            i-= 1
        end = max(end, i)

    labels = ['%s-%s' % (x, x+1) for x in range(start,end+1)]
    datasets = [{'label':label, 'data':line[0][start:end+1], 'backgroundColor':c, \
                 'borderColor':b, 'borderWidth':1} for line, label, c, b in data]

    return {'labels':labels, 'datasets':datasets, 'route':route}

def give_info(res, start, end, datte, singles, longer):

    route = '<p>Tulokset osoitteesta "%s" osoitteeseen "%s" päivämääränä %s. ' \
            'Reitti sisältää seuraavasti kävelyä:' % (start, end, datte)
    duration = res['data']['plan']['itineraries'][0]['duration']


    # 1.2 refers walking speed of 1.2 m/s
    walks = [[k, int(v['walkDistance']/1.2/60)] for k, v in singles.items()]
    walks.extend([[k, int(v['walkDistance']/1.2/60)] for k, v in longer.items()])

    route += '\n<ul class="list-group">\n'
    for walk in walks:
        line = '%s: kävelyä %i min' % (walk[0], walk[1])
        route += '<li class="list-group-item">' + line + '</li>\n'

    route += '<li class="list-group-item">Koko matkan kävely kestäisi %s minuuttia.</li>\n' % (int(duration/60))
    route += '</ul>'

    return route


def sort_ok(places):
    """
    Input: Whatever the get_location function returns
    Output: [(coordinate, city)]. Could return an empty list, a list with a single tuple, or
    many tuples
    The function check results of get_location function and return either a single address,
    in case only one address had 1 as a score. If there are many, return many :)
    """

    def get_city(place):
        """Helper function to take city name from a tuple from get_location"""
        parts = place[1].split(',')
        if len(parts) < 2:
            return ''
        return parts[1].strip()

    ok_places = ['Espoo', 'Kauniainen', 'Helsinki', 'Vantaa', 'Kirkkonummi',\
                 'Tuusula', 'Kerava', 'Sipoo', 'Järvenpää']

    possible = [x for x in places if get_city(x) in ok_places and x[0]> 0.4]

    if not possible:
        return []

    sorted_possible = sorted(possible, key=lambda c: c[0])

    # confidence over 1 and many places
    candidates = [x for x in possible if x[0] == 1]

    if len(candidates) == 1:
        return [(candidates[-1][2:], candidates[-1][1])]
    elif len(candidates) > 1:
        results = [(item[2:], item[1]) for item in candidates]
        return results

    # we return all possible
    results = [(item[2:], item[1])  for item in sorted_possible]
    return results


def tell_results(startcoord, poicoord, weekday=1):
    """
    Simple helper function to do the magic
    """
    today = date.today()
    days = [today + timedelta(days=x) for x in range(1, 8)]
    days = {x.isoweekday():x.strftime("%Y-%m-%d") for x in days}
    time = "07:30:00"
    datte = days[weekday] #1 is for Monday

    starts = sort_ok(startcoord)
    pois = sort_ok(poicoord)
    if not starts or not pois:
        return {'error':'Osoitetta ei löytynyt'}

    # even if there are multiple choices, we just take the best
    start, startadd = starts[-1]
    poi, poiadd = pois[-1]

    payload = ROUTEQ % (start[0], start[1], poi[0], poi[1], datte, time)

    result = run_query(payload)['data']['plan']['itineraries']
    if not result:
        return None

    (singles, longer) = analyse_routeq(result)

    alltimes = [analyse_single(k, v, weekday) for k, v in singles.items()]
    alltimes.extend([analyse_multi(k, v, weekday) for k, v in longer.items()])
    outcome = make_results(alltimes)

    payload = WALKQ % (start[0], start[1], poi[0], poi[1])
    res = run_query(payload)
    route = give_info(res, startadd, poiadd, datte, singles, longer)

    results = style_chart_js(outcome, route)

    return results
