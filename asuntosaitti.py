from flask import Flask, request, session, g, redirect, url_for, \
    abort, render_template, flash, jsonify

import backend

#configuration
DEBUG = True

app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('FLASKR_SETTINGS', silent=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data', methods=['POST'])
def data():
    startloc = request.form['asunto']
    poi = request.form['poi']
    startcoord = backend.getLocation(startloc)
    poicoord = backend.getLocation(poi)

    print('Finding connections from "%s" to "%s"' % (startloc, poi))

    if len(startcoord) == 0:        
        print("Ups, can't find even similar location for \"%s\"" % startloc)
        return jsonify({'error':"Ups, can't find  location \"%s\"" % startloc})
    if len(poicoord) == 0:        
        print("Ups, can't find even similar location for \"%s\"" % poiloc)
        return jsonify({'error':"Ups, can't find  location \"%s\"" % poiloc})

    results = backend.tellResults(startcoord,poicoord)

    backend.pprint.pprint(jsonify(results))

    return jsonify(results)


if __name__ == '__main__':
    app.run()
