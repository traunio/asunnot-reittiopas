# Vuorotiheys

The goals of this project are:
* Test [www.digitransit.fi] (https://www.digitransit.fi) API
* Help assessing potential new apartment's public transportation
* Make very first useful web app (with Flask)
* Deploy it somewhere (Heroku)

Words of caution. This is a learning project with little testing, so many bugs persist for certain.

## Implementation

### Non-technical sidee

Given two addresses the program will check a rough estimate on number of connection for each hour from Digitransit. The exact APIs are available [here] (https://digitransit.fi/en/developers/). The idea is to use check a rough estimate on how good public transportation connections are available from place A to place B. Results are displayed as a bar chart, which shows
* How many busses/trains/metro in an hour
* How long does the connection take.

__The implementation is currently available on http://asuntosaitti.herokuapp.com/ (hosted on Heroku). The UI is rough, and no unittests are used in the code. 

Example picture below, although prettier colors than the "production" version.
![Example pic on 22.11.2016 version][screenshot]

### Technical side

Technically the implementation relies on querying 11 from journey planner API during Monday/Saturday/Sunday morning. This gives direct routes, i.e. with only one bus/train, and then multileg routes, which might use two busses, bus+train etc. Then the stop schedules for these combinations are queried and results constructed. Since only 11 journey planner results are queried, this also is the upper limit for different transports.

After different routes have been established, they are divided into two groups:
* Routes with single leg (in addition to walking)
* Routes with two or more legs (in addition to walking)

The stop schedules are then used to make the chart. For multileg journey the stop schedules for each leg is queried. Then these are matched, meaning that the same combination is required. This skews the results a bit. This affects at least bus leg, where there are multiple busses going the same route (e.g. Länsiväylä). For subway leg it is required that the headsign matches the original subway headsign.

Finally the chart is plotted with [Chart.js](http://www.chartjs.org/). Chart.js is a nice JavaScript charting library. Initially I tried [Chartist.js](https://gionkunz.github.io/chartist-js/), but I didn't see the possibility to add legends in the basic version. Nevertheless, Chartist.js also seemed to be nice for plotting.

## Miscellaneous notes

Initial version was made with iPython notebook and is still available in misc-subdirectory. This version has not been updated since the change to flask app, and hence has some bugs, which are fixed already in the flask app.

The most challenging part in this project has been learning the graphQL API provided by Digitransit and learning in what kind of form the data comes. Trying JavaScript and Chart.js for the first times were easier.

The css style is copied directly from flask tutorial. Thanks and sorry.


[screenshot]: misc/Pic_2016_11_22.png "Screenshot of example results" 

