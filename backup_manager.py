#!/usr/bin/python3

### IMPORTS ###
import dateutil.parser
import os
from datetime import *
import argparse

### DEFAULTS ###
EXTENSIONS = [".tar", ".tar.gz", ".tar.gz.gpg"]
DEBUG      = False
SYSLOG     = False

backup_name  = "all"

max_daily   = 7
max_weekly  = 3
max_monthly = 3
max_yearly  = 1
min_total   = 8

day_of_monthly_backup   = 1
day_of_weekly_backup    = 1       #monday = 1, sunday = 7
month_of_yearly_backup  = 1

delList = dict()

def debug(s):
    if DEBUG:
        print(s)

def checkDirectory(dirName):
    '''Check a directory for files'''
   
    # mark files for potential deletion #
    for folder, subs, files in os.walk(dirName):
        for fname in files:
            parseFilename(fname, dirName)

    # check and delete if nessesary #
    for name,entries in delList.items():
        if len(entries) <= min_total:
            debug("Not removing '{}' - less than {} backups ({})".format(name, min_total, len(entries)))
            continue
        else:
            for entry in entries:
                handleDelete(*entry)

def parseFilename(filename, dirName):
    '''Check filename for relevant indentifiers'''
    global delList

    try:
        name, dateAndExtensions = filename.split('_')
        date = dateAndExtensions.split('.')[0]
        extension = filename[len(name) + len(date) + 1:]
        if extension in EXTENSIONS:
            if name in delList:
                delList[name] += [(filename, dirName, date, name, extension)]
            else:
                delList.update({name:[(filename, dirName, date, name, extension)]})
        else:
            debug("Not removing {} {} - extension not whitelisted".format(dirName, filename))
    except (IndexError, ValueError):
        debug("Malformed filename {} {} -> ignored".format(dirName, filename))


def handleDelete(filename, dir_name, str_logdate, name, ext):
    '''Check file against given constraint and delete it if nessesary.
            return: Bool - Information if file has been deleted'''

    today = datetime.today()

    # determine date of backup #
    try:
        logdate = dateutil.parser.parse(str_logdate)
    except ValueError:
        debug("Path {} {} failed (unrecognized format)".format(dirname, filename))
        return False

    # check constraints #
    if (today - logdate).days < max_daily:
        debug("Keeping daily: {}".format(filename))
        return False
    if logdate.isoweekday() == day_of_weekly_backup  and (today - logdate).days / 7 < max_weekly:
        debug("Keeping weekly: {}".format(filename))
        return False
    if logdate.day == day_of_monthly_backup and today.year == logdate.year \
                                            and today.month - logdate.month  < max_monthly:
        debug("Keeping monthly: {}".format(filename))
        return False
    if logdate.day == day_of_monthly_backup and logdate.month == month_of_yearly_backup \
                                            and today.year - logdate.year    < max_yearly:
        debug("Keeping yearly: {}".format(filename))
        return False
    
    # remove file #
    try:
        os.remove(os.path.join(dir_name,filename))
        debug("Deleted: {}".format(filename))
    except Exception as e:
        debug("{} failed: {}".format(filename, e))
        return False

    return True

### SCRIPT ###
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Simple python backup manager', 
                                        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('PATH', nargs='+', help='Paths to check for backups')
    parser.add_argument('--extensions', '-e', nargs='+', default=EXTENSIONS, 
                            help='Whitelist for exentions to handle')
    parser.add_argument('--debug', action='store_const', default=DEBUG, const=True, 
                            help='Print debugging information')

    args = parser.parse_args()

    EXTENSIONS = args.extensions
    DEBUG = args.debug

    for backupDir in args.PATH:
        checkDirectory(backupDir)
