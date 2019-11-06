#!/usr/bin/env python3

import datetime
import time
import socket
import urllib.request
import urllib.parse
import sys
import threading
import os
import signal

socket_timeout=5.000
server_version="6.0"
server_version_url="http://proserver.msmbps.com/version.txt"
server_targets=None
server_targets_url="http://proserver.msmbps.com/url.txt"
number_of_threads=30
thread_lock=None
index_to_test=0
result=None
done=0
server_report_url="http://proserver.msmbps.com/report/"

def read_url(url):
    try:
        contents=urllib.request.urlopen(url).read().decode('utf-8')
    except:
        contents="ERROR"
    return contents

def connect_time(address, port):
    global socket_timeout
    try:
        ip=socket.gethostbyname(address)
    except:
        ip='255.255.255.255'
    s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(socket_timeout)
    a=(ip, port)
    b=0
    start=time.perf_counter()
    try:
        s.connect(a)
    except:
        b=5555
    end=time.perf_counter()
    try:
        s.shutdown(socket.SHUT_RDWR)
        s.close()
    except:
        b=5555
    if b==5555:
        return 5555
    else:
        between=end-start
        result=round(between*1000)
        return result

def thread_function():
    global thread_lock, index_to_test, server_targets, result, done
    while True:
        thread_lock.acquire()
        if index_to_test>len(server_targets)-1:
            thread_lock.release()
            return
        else:
            my_index=index_to_test
            index_to_test=index_to_test+1
        target=server_targets[my_index];
        thread_lock.release()
        min_time=9999
        for i in range(5):
            a=connect_time(target,80)
            if a>=9999:
                a=9999
            if a<min_time:
                min_time=a
        if min_time>=9999:
            min_time=9999
        thread_lock.acquire()
        result[my_index]=min_time
        done=done+1
        thread_lock.release()

def http_post(url, data):
    post=urllib.parse.urlencode(data).encode("utf-8")
    req=urllib.request.Request(url, post)
    response=urllib.request.urlopen(req)
    return response.read().decode('utf-8')

def signal_handler(sig, frame):
    sys.exit(0)

def main():
    global server_version, server_version_url, server_targets, server_targets_url, number_of_threads, thread_lock, index_to_test, result, done, server_report_url
    signal.signal(signal.SIGINT, signal_handler)
    print("")
    print("msmbps (Version 6.0)")
    print("Source code of this program is available at:")
    print("https://github.com/msmbps/msmbps-python")
    print("")
    print("1/5 Checking server version ...", end=' ')
    if(read_url(server_version_url)==server_version):
        print("OK (version: "+server_version+")")
    else:
        print("FAILED")
        sys.exit()
    print("2/5 Getting the list of targets ...", end=' ')
    a=read_url(server_targets_url)
    if a=="ERROR":
        print("FAILED")
        sys.exit()
    a=a.replace("http://","")
    a=a.replace("/","")
    a=a.replace("\r","")
    server_targets=a.split("\n")
    print("OK (total: "+str(len(server_targets))+")")
    print("3/5 Testing the time of TCP/IP connect ...")
    thread_lock=threading.Lock()
    result=[]
    for i in range(len(server_targets)):
        result.append(9876)
    index_to_test=0
    done=0
    for i in range(number_of_threads):
        t=threading.Thread(target=thread_function)
        t.daemon=True
        t.start()
    while done<len(server_targets):
        time.sleep(1)
        print("\r    "+str(done)+"/"+str(len(server_targets))+"  "+str(round(done*100/len(server_targets)))+"%  (CTRL+C to quit)     ", end=' ')
        sys.stdout.flush()
    print("\r    "+str(done)+"/"+str(len(server_targets))+"  "+str(round(done*100/len(server_targets)))+"%  (CTRL+C to quit)     ", end=' ')
    sys.stdout.flush()
    print("")
    print("4/5 Generating report ...")
    s=""
    for i in range(len(server_targets)):
        s=s+str(result[i]).zfill(4)
    data={"number": s}
    html=http_post(server_report_url,data)
    a=datetime.datetime.now()
    a=a.strftime("msmbps.report.%Y.%m.%d.%H.%M.%S");
    html=html.replace("[TITLE]",a)
    html_file=open(a+".html", "w")
    html_file.write(html)
    html_file.close()
    print("5/5 Done.")
    print("    File: "+a+".html")
    print("    Folder: "+os.getcwd())
    print("")
    x=input("(ENTER to quit)")

main()