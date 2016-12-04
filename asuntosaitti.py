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

@app.route('/data', methods=['POST'])
def data():
    try:
        startloc = request.form['asunto']
        poi = request.form['poi']
        day = request.form['combo']
        startcoord = backend.getLocation(startloc)
        poicoord = backend.getLocation(poi)
    except:
        print("Something went wrong")
        print(sys.exc_info()[0])
        traceback.print_exc()
        return jsonify({'error':'Something went wrong in day'})

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
        results = backend.tellResults(startcoord,poicoord, d)
    except:
        print("Something went wrong")
        print(sys.exc_info()[0])
        traceback.print_exc()
        return jsonify({'error':'Something went wrong, sorry'})

    if DEBUG:
        backend.pprint.pprint(jsonify(results))

    return jsonify(results)


if __name__ == '__main__':
    if DEBUG:
        app.run()
    else:
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port)
