#!/bin/python3

from pyhprof.parsers import HProfParser
from pyhprof.references import ReferenceBuilder
import pyhprof
import argparse
import sys

# Use truffleHog to parse any references for common API keys
from truffleHogRegexes.regexChecks import regexes
import re

def main():
	flags = {}
	parser = argparse.ArgumentParser(description='Parse JAVA HPROF files')
	parser.add_argument('-f', '--filename', dest='filename', required=True,
	                    help='HPROF file to parse')
	parser.add_argument('-t1', '--type-one', action='store_true',
	                    help='Force Type 1 parsing of variables')
	parser.add_argument('-t2', '--type-two', action='store_true',
	                    help='Force Type 2 parsing of variables')

	args = parser.parse_args()

	if args.type_one == True and args.type_two == True:
		print("Error: Use -t1 or -t2, but not both")
		sys.exit(1)
	else:
		if args.type_one == True:
			flags['type_one'] = True
		else:
			flags['type_one'] = False
		if args.type_two == True:
			flags['type_two'] = True
		else:
			flags['type_two'] = False
	
	filename = args.filename
	fp = open(filename, 'rb')
	refs = ReferenceBuilder(fp, flags)

	refs.build()

	print("\n\nVariables:\n\n")

	for i in refs.variables.keys():
		key = i.decode("utf-8")
		for v in refs.variables[i]:
			print("%s: %s" % (key, v.decode("utf-8")))

	http_references = []
	secrets = []

	for i in refs.references.keys():
		if type(refs.references[i]) == pyhprof.references.PrimitiveArrayReference:
			data = refs.references[i].ascii_data().decode("utf-8")
			if 'HTTP/1.1' in data:
				http_references.append(data)
			for k in regexes.keys():
				matches = regexes[k].findall(data)
				if len(matches) != 0:
					secrets.append("TruffleHog (%s): %s. Identified from: \n%s" % (k, matches, data))

	print("\n\nHTTP References:\n\n")
	for i in http_references:
		print(i + "\n")

	print("\n\nSecret References:\n\n")
	for i in secrets:
		print(i + "\n")

main()