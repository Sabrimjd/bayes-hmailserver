#!/usr/bin/python3
#title          :bayes.py
#description    :autolearning automation for hmailserver
#author         :Sabri MJAHED
#date           :20190118
#version        :1.1
#usage          :python3 bayes.py -h
#================================================================


import os
import sys
import email
import csv
from email.utils import getaddresses
import shutil
import subprocess
import sqlite3
from argparse import ArgumentParser
from pathlib import Path

srv=["srv2","srv1"]

def arguments():
    parser = ArgumentParser()
    parser.add_argument("-s", "--srv",  dest="srv", required=False, default="all",
                        help="TSV database dump (default: %(default)s)")
    
    parser.add_argument("-t", "--tsv",  dest="tsv", required=False, default="db-dump-SRV-BAYES.tsv",
                        help="TSV database dump (default: %(default)s)")
    
    parser.add_argument("-b", "--bayes",  dest="bayes", required=False, default="spam",
                        help="Bayes learn type (default: %(default)s) spam or ham")
    
    parser.add_argument("-v", "--verbose", dest="debug", required=False, default=False, action='store_true',
                        help="Debug options (default: %(default)s)")

    parser.add_argument('--version', action='version', version='%(prog)s - v0.1')

    args = parser.parse_args()
    return args



args = arguments()
if args.debug == True:
    print('Values')
    print('srv          =', args.srv)
    print('tsv          =', args.tsv)
    print('bayes        =', args.bayes)
    print('Debug        =', args.debug)

def isFileExist(fullpath):
    bool = os.path.isfile(fullpath)
    return bool
    

def createTsv(srv):
    if args.debug == True:
        print("-------------------")
        print("SERVER USED : "+ srv)
        print("BAYES "+args.bayes+" LEARNING")
        os.system('echo "Starting at : " &&  date')
    os.system('bash /home/spamd/'+args.bayes+'-list-retriver.sh '+srv+' '+args.bayes)

    os.system("sed -i '1d' /home/spamd/db-dump-"+srv+"-"+args.bayes+".tsv")
    
    num_lines=sum(1 for line in open("/home/spamd/db-dump-"+srv+"-"+args.bayes+".tsv"))
    
    if args.debug == True:
        print('Number of lines :',num_lines)
        os.system("echo 'size before :' && du -sh /home/learning/*")

def mailDownloader(mnt,dst,tsv):
    with open(tsv) as tsvfile:
        reader = csv.reader(tsvfile, delimiter='\t')
        array = []
        for row in reader:
            try:
                fulldomain = getaddresses([row[2],])
            except:
                print("[ERROR] Can't parse the following row, skipping it : " + ', '.join(row))
                pass
            
            if fulldomain:
                email = fulldomain.pop()[1]
                contact = email.split("@")[0]
                domain = email.split("@")[-1]
                fileprefix=row[0][1:3]
                URI="/"+domain+"/"+contact+"/"+fileprefix+"/"+row[0]
                fullpath = mnt+URI
                localfile = "/home/learning/"+args.bayes+"-archive/"+row[0]
                if isFileExist(localfile) == False:
                    try:
                        shutil.copy2(mnt+URI,dst)
                        if args.debug == True:
                            print("GET :",fullpath)
                    except:
                        pass
#                else:
#                    if args.debug == True:
#                        print("Is already downloaded",fullpath)

def dbDump(srv):
    mnt = "/mnt/smb/" + srv
    dst = "/home/learning/"+args.bayes+"/"
    tsv = "db-dump-" + srv + "-"+args.bayes+".tsv"
    mailDownloader(mnt,dst,tsv)

if args.srv == "all":
    srvChose = srv
else:
    srvChose = args.srv.split(",")
    
def finition():
    if args.debug == True:
        print("Sync bayes DB...")
    os.system("/usr/bin/sa-learn --sync")
    if args.debug == True:
        print("Deleting old tokens...")
    os.system("/usr/bin/sa-learn --force-expire")
    if args.debug == True:
        print("Learning "+args.bayes+"s...")
    os.system("/usr/bin/sa-learn --"+args.bayes+" /home/learning/"+args.bayes+"/")
    if args.debug == True:
        print("Dump :")
    os.system("/usr/bin/sa-learn --dump magic")
    if args.debug == True:
        print("Reloading...")
    os.system("/usr/bin/sa-update --nogpg && service spamd restart")
    if args.debug == True:
        print("Moving To archive...")
    os.system("mv /home/learning/"+args.bayes+"/* /home/learning/"+args.bayes+"-archive/")
    if args.debug == True:
        os.system("echo 'Size after : ' && du -sh /home/learning/"+args.bayes+"/")
        os.system('echo "Finished at : " &&  date')
    if args.debug == True:
        print("----------------------------------------------------------")
        print("----------------------------------------------------------")
    

for s in srvChose:
    createTsv(s)
    dbDump(s)
    
if len(os.listdir("/home/learning/"+args.bayes+"/")) != 0:
    finition()
