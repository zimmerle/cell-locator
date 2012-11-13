#!/usr/bin/python
# -*- coding: utf8 -*-

import sys
import getopt
from struct import pack, unpack
from httplib import HTTP
import urllib2
import json

__VERSION__ = "0.1"
__DEVICE__ = "Nokia N95 8Gb"
verbose = False

def v(s):
	if verbose:
		print "*** %s" % s
		return;


def sanity_check (string):
	"""
	Check if a given string is in the format:
	cid, lac, mnc, mcc
	if so, returns the values in this sequence
	"""

	v("Sanity checking the string: %s" % string)
	p = string.split(",")
	res = []
	for i in [0,1,2,3]:
		try:
			res.append(p[i])
		except:
			res.append(0)
			pass

	v("The string: %s contains: cid=%s lac=%s mnc=%s mcc=%s" % (string,
		res[0], res[1], res[2], res[3]))
	return res;

def n(s):
    return s.encode('utf-8').replace('Ã¡', 'á').replace('Ã³', 'ó').replace('Ã§', 'ç').replace('Ã£', 'ã').replace('Ã', 'í')


class Cell:
	lat = 0
	lon = 0
	name = "Duh!"
	address = ""
	accuracy = 0
	country = ""
	localityName = ""
	north = 0
	south = 0
	east = 0
	west = 0
	point = [0, 0, 0]
	coverage = 0

	def __init__(self, j, lat, lon, cov):
		self.lat = lat
		self.lon = lon
		self.coverage = cov


		print str(j)

		self.name = j['name']
		self.address = j['Placemark'][0]['address']
		self.accuracy = int(j['Placemark'][0]['AddressDetails']['Accuracy'])
		self.country = j['Placemark'][0]['AddressDetails']['Country']['CountryName']
		if 'AdministrativeArea' in j['Placemark'][0]['AddressDetails']['Country']:
			if 'Locality' in j['Placemark'][0]['AddressDetails']['Country']['AdministrativeArea']:
				self.localityName = j['Placemark'][0]['AddressDetails']['Country']['AdministrativeArea']['Locality']['LocalityName']
			elif 'SubAdministrativeArea' in j['Placemark'][0]['AddressDetails']['Country']['AdministrativeArea']:
				self.localityName = j['Placemark'][0]['AddressDetails']['Country']['AdministrativeArea']['SubAdministrativeArea']['Locality']['LocalityName']
			else:
				self.localityName = "No found."

	def __str__(self):
		return "Name: %s" % (self.name)


	def printme(self, tab=''):
		print str(tab) + " Name: " + n(self.name) + " (Accuracy: " + str(self.accuracy) + ") (Cell coverage:",
		print str(self.coverage) + ")"  
		print str(tab) + " Address: "  + n(self.address) + " [" + n(self.country) + "/" + n(self.localityName) + "]" 
		print str(tab) + "        : https://maps.google.com/maps?q=" + self.name + "&"

def country_iso(mcc):
	# FIXME: fill the list.
	return "br"

def grab_geo_info(lat, lon):
	url = 'http://maps.google.com/maps/geo?q=%s,%s&output=json&oe=utf8' % (str(lat), str(lon))
	return urllib2.urlopen(url).read()

def grab_information(cid, lac, mnc=0, mcc=0):

	country = country_iso(mcc)

	v("Fetching latitude and longitude...")
	query = pack('>hqh2sh13sh5sh3sBiiihiiiiii',
		21, 0,
		len(country), country,
		len(__DEVICE__), __DEVICE__,
		len('1.3.1'), "1.3.1",
		len('Web'), "Web",
		27, 0, 0,
		3, 0, int(cid), int(lac), 0, 0, 0, 0)


	http = HTTP('www.google.com', 80)
	http.putrequest('POST', '/glm/mmap')
	http.putheader('Content-Type', 'application/binary')
	http.putheader('Content-Length', str(len(query)))
	http.endheaders()
	http.send(query)
	code, msg, headers = http.getreply()
	result = http.file.read()
 
	try:
		(a, b,errorCode, lat, lon, cov, d, e) = unpack(">hBiiiiih",result)
	except:
		a = 0
		b = 0
		errorCode = 0
		lat = 0
		lon = 0
		cov = 0
		d = 0
		e = 0
		pass

	v("a=%s, b=%s, errorCode=%s, cov=%s, d=%s, e=%s" % (str(a), str(b), errorCode, str(cov), str(d), str(e)))
	lat = lat / 1000000.0
	lon = lon / 1000000.0
	v("Here we go: %s and %s" % (lat, lon))
	


	geo_info = None
	geo_info_json = None
	geo_info = grab_geo_info(lat, lon)
	geo_info = grab_geo_info(-8.064159, -34.896666)
	print str(geo_info)
	geo_info_json = json.loads(geo_info)

	v("Geo Info: %s" % geo_info)
	v("Geo Info: %s" % str(geo_info_json))

	c = Cell(geo_info_json, lat, lon, cov)

	return c


def format_results(c):
	c.printme()


def print_help (die=False):
	print """Usage: """ + sys.argv[0] + """ [options] (cid,lac[,mnc,mcc])

 -h, --help	Print _this_ help message
 -v, --verbose 	Print verbose messages
 -V, --verbatim Use verbatim addresses instead of lat/long.
     --version	Print the version number

"""
	if die:
		sys.exit(-1)



if __name__ == '__main__':
	verbatim = False

	try:
		options, remainder = getopt.gnu_getopt(sys.argv[1:], 'vVh',
			["verbose", "verbatim", "help", "version"],
			)
	except getopt.GetoptError, err:
		print str(err)
		print_help(die=True)

	if len(remainder) == 0:
		print_help(die=True)

	for o, a in options:
		if o in ("-h", "--help"):
			print_help(die=True)
		elif o == "--version":
			print str(__VERSION__)
			sys.exit()
		elif o in ("-v", "--verbose"):
			verbose = True
		elif o in ("-V", "--verbatim"):
			verbatim = True

	cells = []
	for i in remainder:
		cid, lac, mnc, mcc = sanity_check(i)

		if lac > 0:
			v("Information queued to be checked.")
			cells.append((cid, lac, mnc, mcc))
		else:
			v("Not valid cellid, not queued.")

	for i in cells:
		c = grab_information(i[0], i[1], i[2], i[3])
		format_results(c)

