# Asunnot-reittiopas/Asuntosaitti

The goals of this project are:
* Test [www.digitransit.fi] (https://www.digitransit.fi) API
* Help try to assess potential new apartment's public transportation
* Make very first useful web app (with Flask)
* Deploy it somewhere

Words of caution. This is a learning project with little testing, so many bugs persist for certain.

## Implementation

Given two addresses the program will check a rough estimate on number of connection for each hour from Digitransit. The exact APIs are available [here] (https://digitransit.fi/en/developers/). The idea is to use check a rough estimate on how good public transportation connections are available from place A to place B. Results are displayed as a bar chart, which shows
* How many busses/trains/metro in an hour
* How long does the connection take.

Example picture below
![Example pic on 22.11.2016 version][screenshot]

Technically the implementation relies on querying 11 from journey planner API during Monday morning. This gives direct routes, i.e. with only one bus/train, and then multileg routes, which might use two busses, bus+train etc. Then the stop schedules for these combinations are queried and results constructed.

## Miscellaneous notes

Initial version was made with iPython notebook and is still available in misc-subdirectory. This version has not been updated since the change to flask app, and hence has some bugs, which are fixed already in the flask app.

The most challenging part in this project has been learning the graphQL API provided by Digitransit and learning in what kind of form the data comes. Trying javascript and Chart.js for the first times were easier.

The css style is copied directly 


[screenshot]: misc/Pic_2016_11_22.png "Screenshot of example results" 

