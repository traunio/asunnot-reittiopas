# Asunnot-reittiopas

The goals of this project are:
* Test [www.digitransit.fi] (https://www.digitransit.fi) API
* Help try to assess potential new apartment's public transportation
* Make very first useful web app (with Flask)
* Deploy it somewhere

Words of caution. This is a learning project with little testing, so many bugs persist for certain.

## Implementation

Given two addresses the program will check a rough estimate on number of connection for each hour. The exact APIs are available [here] (https://digitransit.fi/en/developers/). The idea is to use check how good are connections from a potential new flat to POI. Exact presentation of the results remains to be decided, but should include:
* How many busses/trains/metro in an hour
* How long does the connection take.

