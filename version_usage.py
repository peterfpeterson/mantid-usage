#!/usr/bin/env python
import datetime
import json
import os
import pandas
import requests # python-requests
import sys

BASE_URL="http://reports.mantidproject.org/api/usage"

def getJson(dateMin, dateMax):
    req = requests.get(BASE_URL, params={'datemin':dateMin,
                                         'datemax':dateMax})
    status_code = req.status_code
    if status_code == 403:
        print "status:", status_code
        print req.json()['message']
        sys.exit(-1)

    try:
        json_doc = req.json()
    except TypeError:
        json_doc = req.json
    results = json_doc['results']
    next_url = json_doc['next']

    while status_code == 200:
        # there are more pages

        try:
            print "trying", next_url
            req = requests.get(next_url)
            if status_code == 403:
                print("status:", status_code)
                print(json_doc()['message'])
                sys.exit(-1)
            try:
                json_doc = req.json()
            except TypeError:
                json_doc = req.json
            next_url = json_doc['next']
            results.extend(json_doc['results'])
        except:
            status_code = 0
    return results

def getData(dateMin, dateMax):
    filename = "usage-%s-%s.json" % (dateMin, dateMax)

    if not os.path.exists(filename):
        results = getJson(dateMin, dateMax)
        print "Writing json to '%s'" % filename
        with open(filename, 'w') as handle:
            json.dump(results, handle)

    print "Loading information from '%s'" % filename
    with open(filename, 'r') as handle:
        data = pandas.read_json(handle)

    return data

def filter(data, key, values):
    return data[data[key].isin(values)]

def truncateMantidVersion(data):
    versions = [ '3.%d.2' % minor for minor in xrange(1,7) ]
    for version in versions:
        exp = version + '0\d\d.+'
        data['mantidVersion'] = data['mantidVersion'].str.replace(exp, version)
    return data


today = datetime.datetime.now()
dateMin = (today - datetime.timedelta(90)).strftime("%Y-%m-%d")
tomorrow = today +  datetime.timedelta(1)
dateMax = tomorrow.strftime("%Y-%m-%d")

data = getData(dateMin, dateMax)

mtdVersions = ['3.1.0', '3.1.1', '3.2.0', '3.2.1', '3.3.0', '3.4.0', '3.4.1']
data = filter(data, 'osName', ['Linux'])
data = filter(data, 'osArch', ['x86_64'])
#data = filter(data, 'mantidVersion', mtdVersions)
data = truncateMantidVersion(data)
#data = data.set_index(['dateTime', 'mantidVersion'])
#data = data.set_index('dateTime', ['mantidVersion', 'osVersion', 'osReadable'])

#a = data.groupby('dateTime')
#a.mantidVersion.apply(pd.value_counts).unstack(-1).fillna(0)
