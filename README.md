# pyhprof
Python library for parsing and analyzing Java hprof files. This repo was forked from https://github.com/matthagy/pyhprof. A few bugs were squashed along with an upgrade to Python 3. The major difference is the addition of the variables attribute on the ReferenceBuilder object.

The [hprof format](http://hg.openjdk.java.net/jdk8/jdk8/jdk/raw-file/tip/src/share/demo/jvmti/hprof/manual.html) doesn't explicitly state what ends up being stored. The Spring Framework ends up storing configuration details and environment variables in PRIMITIVE ARRAY DUMP objects. Two different formats were identified, which do not appear to be tied to the HPROF version (JAVA PROFILE 1.0.1 or 1.0.2). The pyhprof/references.py script has comments describing the differences. The library will accept a flag dictionary to determine what parsing type to use. If none is chosen, a best guess is made off of the JAVA PROFILE string. 

The spring_heapdumper.py script was written as an example that will properly use the library and attempt to print out interesting sensitive data. All parsed variables, HTTP requests/responses, and any references (linked or unlinked) that match a truffleHog signature will be dumped in the output.

## Usage

```
$ python3 ./spring_heapdumper.py -h                                               
usage: spring_heapdumper.py [-h] -f FILENAME [-t1] [-t2]

Parse JAVA HPROF files

optional arguments:
  -h, --help            show this help message and exit
  -f FILENAME, --filename FILENAME
                        HPROF file to parse
  -t1, --type-one       Force Type 1 parsing of variables
  -t2, --type-two       Force Type 2 parsing of variables
 
$ python3 ./spring_heapdumper.py -f heapdump -t1
```

Note that if this crashes, you will need to allocate more RAM to your host. Nothing is printed until the library is finished parsing the HPROF. 

## Improvements

The truffleHog regex list can easily be extended to include custom patterns. 

If you are testing this against a common deployment platform or set of apps, there is likely fixed environment variables that could be used as a better heuristic for variable block alignment. For example you can check if 2 blocks past the "PATH" key contains "/bin" or if instead it's 4 blocks past the "PATH" key.