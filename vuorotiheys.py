from flask import Flask, request, session, g, redirect, url_for, \
    abort, render_template, flash, jsonify

import backend
import sys
import os

import traceback

#configuration. Set True for local testing :)
DEBUG = False

app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('FLASKR_SETTINGS', silent=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/index.html')
def hello():
    return render_template('index.html')

@app.route('/data', methods=['POST'])
def data():
    try:
        startloc = request.form['asunto']
        poi = request.form['poi']
        day = request.form['combo']
        startcoord = backend.get_location(startloc)
        poicoord = backend.get_location(poi)

    except:
        print("Something went wrong")
        print(sys.exc_info()[0])
        traceback.print_exc()
        return jsonify({'error':'Something went wrong in day'})

    start = [address[1] for address in backend.sort_ok(startcoord)]
    end = [address[1] for address in backend.sort_ok(poicoord)]

    if len(start) == 0:
        return jsonify({'noasunto': 'Starting place address not found'})

    if len(end) == 0:
        return jsonify({'nopois': 'End place address not found'})

    if len(start) > 1:
        return jsonify({'asuntos': start})

    if len(end) > 1:
        return jsonify({'pois': end})
    
    if day == 'Monday':
        d = 1
    elif day == 'Wednesday':
        d = 3
    elif day == 'Saturday':
        d = 6
    elif day == 'Sunday':
        d = 7
    else:
        d = 1
    
    print('Finding connections from "%s" to "%s" on %s' % (startloc, poi, day))

    if len(startcoord) == 0:        
        print("Ups, can't find even similar location for \"%s\"" % startloc)
        return jsonify({'error':"Ups, can't find  location \"%s\"" % startloc})
    if len(poicoord) == 0:        
        print("Ups, can't find even similar location for \"%s\"" % poiloc)
        return jsonify({'error':"Ups, can't find  location \"%s\"" % poiloc})

    try:
        results = backend.tell_results(startcoord,poicoord, d)
    except:
        print("Something went wrong")
        print(sys.exc_info()[0])
        traceback.print_exc()
        return jsonify({'error':'Something went wrong, sorry'})

    if DEBUG:
        backend.pprint.pprint(jsonify(results))

    return jsonify(results)


if __name__ == '__main__':
    app.run()

