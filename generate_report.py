#!/usr/bin/env python
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import json
import matplotlib.pyplot as plt
import os
import pandas as pd

class Report(object):
    def __init__(self, website, version="0.0", downloads="0"):
        self.website = website
        self.version = version
        self.downloads = downloads

    def __repr__(self):
        return "[%s:%s:%s]" % (self.website, self.version, str(self.downloads))


class SourceforgeReport(Report):
    def __init__(self, filename):
        super(SourceforgeReport, self).__init__("sourceforge")

        shortname = os.path.split(filename)[-1].replace('.json','')
        self.version = shortname.replace('sourceforge-', '')

        with open(filename, 'r') as handle:
            doc = json.load(handle)
            self.downloads = doc['total']

class GithubReport(Report):
    def __init__(self, releasedoc, shortenVersion=True):
        super(GithubReport, self).__init__("github")

        self.version = releasedoc['tag_name'].replace('v','')
        if shortenVersion:
            self.version = '.'.join(self.version.split('.')[:2])

        self.downloads = 0
        for asset in releasedoc['assets']:
            self.downloads += asset['download_count']

def combineGithubVersions(orig):
    splitted = {}
    for item in orig:
        if item.version in splitted:
            splitted[item.version].downloads += item.downloads
        else:
            splitted[item.version] = item
    return splitted.values()


def parseGithub(filename):
    with open(filename, 'r') as handle:
        doc = json.load(handle)
        items = []
        for release in doc:
            items.append(GithubReport(release))

    return combineGithubVersions(items)

direc = os.path.abspath(os.curdir)
print("Finding json files in", direc)

jsonfilenames = [name for name in os.listdir(direc) \
                 if name.endswith(".json")]

items = []
for filename in jsonfilenames:
    if filename.startswith("sourceforge"):
        items.append(SourceforgeReport(filename))
    elif filename.startswith("github"):
        items.extend(parseGithub(filename))

# key:[sourceforge.downloads, github.downloads]
versions={}
indexes = {'sourceforge':0, 'github':1}
for item in items:
    if item.version not in versions:
        versions[item.version] = [0,0]
    index = indexes[item.website]
    versions[item.version][index] = item.downloads
# data = pd.DataFrame(versions)

keys = versions.keys()
keys.sort()

with open('versions.csv', 'w') as handle:
    handle.write(','.join(['versions', 'sourceforge', 'github'])+"\n")
    for key in keys:
        stuff = [str(downloads) for downloads in versions[key]]
        stuff.insert(0, key)
        handle.write(','.join(stuff) + "\n")

data = pd.read_csv('versions.csv',index_col='versions')
data.plot(kind='bar', stacked=True)
plt.show()
