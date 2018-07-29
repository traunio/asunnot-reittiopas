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
@app.route('/index.html')
def index():
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
        return jsonify({'error':'Jotain meni pieleen osoitteissa tai niiden koordinaattien haussa'})

    start = [address[1] for address in backend.sort_ok(startcoord)]
    end = [address[1] for address in backend.sort_ok(poicoord)]

    if len(start) == 0:
        return jsonify({'noasunto': 'Lähtöosoitetta ei löytynyt'})

    if len(end) == 0:
        return jsonify({'nopois': 'Määränpään osoitetta ei löytynyt'})

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

    try:
        results = backend.tell_results(startcoord,poicoord, d)
    except:
        print("Something went wrong")
        print(sys.exc_info()[0])
        traceback.print_exc()
        return jsonify({'error':'Jotain meni pieleen, pahoittelut'})

    if DEBUG:
        backend.pprint.pprint(jsonify(results))

    return jsonify(results)


if __name__ == '__main__':
    app.run()

