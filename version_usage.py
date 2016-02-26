#!/usr/bin/env python
import datetime
import json
import locale
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

def truncateDates(json_doc):
    for item in json_doc:
        item['dateTime'] = item['dateTime'][0:10]
    return json_doc

def getData(dateMin, dateMax):
    filename = "usage-%s-%s.json" % (dateMin, dateMax)

    if not os.path.exists(filename):
        results = getJson(dateMin, dateMax)
        results = truncateDates(results)
        print "Writing json to '%s'" % filename
        with open(filename, 'w') as handle:
            json.dump(results, handle)

    print "Loading information from '%s'" % filename
    with open(filename, 'r') as handle:
        data = pandas.read_json(handle)#, date_unit='D')

    return data

def filter(data, key, values, isIn=True):
    return data[data[key].isin(values)==isIn]

def truncateMantidVersion(data):
    versions = [ '3.%d' % minor for minor in xrange(1,7) ]

    for version in versions:
        exp = version + '.20\d\d.+'
        nightly = version + '-nightly'
        data['mantidVersion'] = data['mantidVersion'].str.replace(exp, nightly)
    return data

locale.setlocale(locale.LC_ALL,'')

# get the data and load into pandas
today = datetime.datetime.now()
dateMin = (today - datetime.timedelta(90)).strftime("%Y-%m-%d")
tomorrow = today +  datetime.timedelta(1)
dateMax = tomorrow.strftime("%Y-%m-%d")
data = getData(dateMin, dateMax)

# filter data
rhel7 = ['CentOS Linux 7 (Core)',
         'Red Hat Enterprise Linux',
         'Red Hat Enterprise Linux Server 7.1 (Maipo)',
         'Red Hat Enterprise Linux Workstation 7.1 (Maipo)',
         'Red Hat Enterprise Linux Workstation 7.2 (Maipo)',
         'Scientific Linux 7.1 (Nitrogen)']
mtdStable = ['3.1.0', '3.1.1', '3.2.0', '3.2.1', '3.3.0', '3.4.0', '3.4.1', '3.5.0', '3.5.1']
print "before filtering:", locale.format('%d', data.size, True)
data = filter(data, 'uid', ['c87a8ca60f0891b79d192fa86f019916'], False)
data = filter(data, 'osName', ['Linux'])
data = filter(data, 'osArch', ['x86_64'])
#data = filter(data, 'mantidVersion', ['3.3.0', '3.4.0', '3.5.0'], False)
#data = filter(data, 'mantidVersion', mtdVersions, False)
print "before osReadable filtering:", locale.format('%d', data.size, True)
data = filter(data, 'osReadable', rhel7)
print "after filtering:", locale.format('%d', data.size, True)

# transform data
data = truncateMantidVersion(data)
#data = data.set_index(['dateTime', 'mantidVersion'])
#data = data.set_index('dateTime', ['mantidVersion', 'osVersion', 'osReadable'])

groups = data.groupby('dateTime')
byVersion = groups.mantidVersion.apply(pandas.value_counts).unstack(-1).fillna(0)


##### plotting in ipython
#%pylab
#byVersion.plot()
