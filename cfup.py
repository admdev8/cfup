#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" cfup.py

    cfup (CloudFlare Updater) is a simple 
    command line utility to update DNS 
    records of a given CloudFlare account.

    Author: marpie (marpie@a12d404.net)

    Last Update:  20140117
    Created:      20130905

"""
import argparse
import copy
import json
import os
import re
import time
import json
import urllib
import urllib2

# Version Information
__version__ = "0.0.1"
__program__ = "cfup v" + __version__
__author__ = "marpie"
__email__ = "marpie+cfup@a12d404.net"
__license__ = "BSD License"
__copyright__ = "Copyright 2013-2014, a12d404.net"
__status__ = "Prototype"  # ("Prototype", "Development", "Testing", "Production")

SCRIPT_PATH = os.path.dirname( os.path.realpath( __file__ ) )
LOOKUP_HISTORY_FILE = os.path.join(SCRIPT_PATH, "history.log")
CONFIG_FILE = os.path.join(SCRIPT_PATH, "cfup.json")

REGEX_IP = re.compile(r'[0-9]+(?:\.[0-9]+){3}')
EXIT_SUCCESS = "success"

#############################################################################
# Config

class Config(object):
    def __init__(self, filename):
        self.filename = filename
        try:
            with open(self.filename, 'r') as f:
                self._cfg = json.load(f)
            self._ready = True
        except:
            self._ready = False

    def __get(self, key):
        try:
            return self._cfg[key]
        except:
            return None

    def ready():
        doc = "The ready property."
        def fget(self):
            return self._ready
        return locals()
    ready = property(**ready())

    def user():
        doc = "The user property."
        def fget(self):
            return self.__get("user")
        return locals()
    user = property(**user())

    def api_key():
        doc = "The api_key property."
        def fget(self):
            return self.__get("api_key")
        return locals()
    api_key = property(**api_key())

    def entries():
        doc = "The entries property."
        def fget(self):
            zones = self.__get("zones")
            if not zones:
                return
            for zone, entries in zones.items():
                yield (zone, entries,)
        return locals()
    entries = property(**entries())

    def dyndns_entries():
        doc = "The entries property."
        def fget(self):
            dyndns = self.__get("dyndns")
            if not dyndns:
                return
            for entry, record_id in zones.items():
                yield (entry, record_id,)
        return locals()
    dyndns_entries = property(**dyndns_entries())

cfg     = Config(CONFIG_FILE)
USER    = cfg.user
API_KEY = cfg.api_key

#############################################################################
# Auxiliary Functions

def http_get(url):
    try:
        f = urllib2.urlopen(url, timeout=2)
        try:
            return f.read()
        finally:
            f.close()
    except:
        return None

def get_wan_ip():
    res = http_get("http://checkip.dyndns.org/")
    if not res:
        res = http_get("http://checkip.dyndns.com/")
    if not res:
        return None
    return REGEX_IP.search(res).group(0)

#############################################################################
# LookupHistory

class LookupHistory(object):
    def __init__(self, filename):
        self._filename = filename
        self._entries = []
        self.__load()

    def entries():
        doc = "The entries property."
        def fget(self):
            return copy.deepcopy(self._entries)
        return locals()
    entries = property(**entries())

    def __load(self):
        try:
            with open(self._filename, 'r') as f:
                res = json.load(f)
            if type(res) is not list:
                return False
            self._entries = res
            return True
        except:
            return False

    def __save(self):
        try:
            with open(self._filename, 'w') as f:
                json.dump(self._entries, f)
            return True
        except:
            return False

    def get_last_ip(self):
        try:
            return self._entries[-1][0]
        except:
            pass
        return ""

    def last_ip_is(self, ip_address):
        try:
            if self._entries[-1][0] == ip_address:
                return True
        except:
            pass
        return False

    def add(self, ip_address):
        if len(self._entries) > 0:
            if self.last_ip_is(ip_address):
                return False
        self._entries.append((ip_address, time.strftime("%Y-%m-%d_%H-%M-%S"),))
        self.__save()
        return True

#############################################################################
# CloudFlare API

class CloudFlare(object):
    URL = "https://www.cloudflare.com/api_json.html"

    def __init__(self, email, api_key):
        self._email = email
        self._api_key = api_key

    def __request(self, action, params={}):
        if type(params) is not dict:
            return None
        params["a"] = action
        params["tkn"] = self._api_key
        params["email"] = self._email

        data = urllib.urlencode(params)
        response = urllib2.urlopen(urllib2.Request(self.URL, data))
        content = None
        try:
            content = response.read()
        finally:
            response.close()
        # parse JSON response
        if content:
            try:
                content = json.loads(content)
            except:
                return None
        return content

    def get_domains(self):
        res = self.__request("zone_load_multi")
        try:
            if res["result"] != EXIT_SUCCESS:
                return None
            zones = res["response"]["zones"]
            if zones["count"] < 1:
                return None
            return zones["objs"]
        except:
            pass
        return None

    def get_records(self, zone_name):
        res = self.__request("rec_load_all", {"z": zone_name})
        try:
            if res["result"] != EXIT_SUCCESS:
                return None
            entries = res["response"]["recs"]
            if entries["count"] < 1:
                return None
            return entries["objs"]
        except:
            pass
        return None

    def get_entry(self, zone_name, record_id):
        records = self.get_records(zone_name)
        if not records:
            return None
        for entry in records:
            if entry["rec_id"] == record_id:
                return entry
        return None

    def update_content(self, zone_name, record_id, new_content):
        entry = self.get_entry(zone_name, record_id)
        if not entry:
            return {"result": "Unknown Failure"}
        if entry["content"] == new_content:
            return {"result": EXIT_SUCCESS}
        params = {
            "z": zone_name,
            "type": entry["type"],
            "id": record_id,
            "name": entry["name"],
            "content": new_content,
            "ttl": entry["ttl"],
        }
        if (entry["type"] == "A") or (entry["type"] == "AAAA") or (entry["type"] == "CNAME"):
            params["service_mode"] = entry["service_mode"]
        elif (entry["type"] == "MX"):
            params["prio"] = entry["prio"]
        elif (entry["type"] == "SRV"):
            params["prio"] = entry["prio"]
            params["service"] = entry["service"]
            params["srvname"] = entry["srvname"]
            params["protocol"] = entry["protocol"]
            params["weight"] = entry["weight"]
            params["port"] = entry["port"]
            params["target"] = entry["target"]
        return self.__request("rec_edit", params)

def cmd_list_domains():
    cf = CloudFlare(USER, API_KEY)
    res = cf.get_domains()
    if not res:
        return "Error receiving Zones."
    for zone in res:
        print("Zone:\n  ID:   %s\n  Name: %s\n" % (zone["zone_id"], zone["zone_name"]))

def cmd_list_entries(zone_name):
    cf = CloudFlare(USER, API_KEY)
    res = cf.get_records(zone_name)
    if not res:
        return "Error receiving entries from %s." % (zone_name)
    print("Zone: %s\n" % zone_name)
    for entry in res:
        print("ID:    %s\nTTL:   %s\nType:  %s\nName:  %s\nValue: %s\n" % (entry["rec_id"], entry["ttl"], entry["type"], entry["name"], entry["content"]))

def cmd_update_entries(new_value):
    func_res = False
    cf = CloudFlare(USER, API_KEY)
    for zone, entries in cfg.entries:
        for entry in entries:
            res = cf.update_content(zone, entry["record_id"], new_value)
            if res["result"] != EXIT_SUCCESS:
                print(res)
            else:
                func_res = True
    return func_res

def cmd_update_remote_entries():
    try:
        response = urllib2.urlopen('localhost:8090')
        content = response.read()
        response.close()
    except:
        return False
    if not ("=" in content):
        return False
    cf = CloudFlare(USER, API_KEY)
    for entry in content.split(";"):
        if not ("=" in entry):
            continue
        hostname, new_value = entry.split("=")
        for dyndns_entry, record_id in cfg.dyndns_entries():
            if hostname == dyndns_entry:
                zone = '.'.join(hostname.split(".")[-2:])
                res = cf.update_content(zone, record_id, new_value)
                if res["result"] != EXIT_SUCCESS:
                    print(res)
    return

# Main
def main(argv):
    if not cfg.ready:
        print("Error while parsing configurtion file.")
        return False

    if len(argv) < 2:
        print("cfup.py [action]")
        return False

    parser = argparse.ArgumentParser(description='CloudFlare Updater')
    parser.add_argument(
        'action', 
        type=str, 
        help='action to perform (list-zones, list-entries, update-entries)'
    )
    parser.add_argument(
        '--zone-name', 
        metavar='ZONE',
        dest='zone_name', 
        help='name of the zone.'
    )
    args = parser.parse_args()

    action = args.action
    if action == ("list-zones") or (action == "list"):
        cmd_list_domains()
    elif action == "list-entries":
        cmd_list_entries(args.zone_name)
    elif action == "update-entries":
        lh = LookupHistory(LOOKUP_HISTORY_FILE)
        ip = get_wan_ip()
        if not ip:
            return False
        if (not lh.last_ip_is(ip)) and cmd_update_entries(ip):
            lh.add(ip)
        cmd_update_remote_entries()
    else:
        print("Available commands: list-zones, list-entries, update-entry")

    return True


if __name__ == "__main__":
    import sys
    sys.exit( not main( sys.argv ) )
