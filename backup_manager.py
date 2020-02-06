#!/usr/bin/python3

### IMPORTS ###
import dateutil.parser
import os
from datetime import *
from systemd import journal

### DEFAULTS ###
backup_dir   = "/home/backup/"
backup_name  = "all"
extensions   = ["tar.gz","tar.gz.gpg"]
debug        = False

max_daily   = 7
max_weekly  = 3
max_monthly = 3
max_yearly  = 1
min_total   = 8

day_of_monthly_backup   = 1
day_of_weekly_backup    = 1       #monday = 1, sunday = 7
month_of_yearly_backup  = 1

### Journal Streams ###
log_debug = journal.stream("BackupRotation-" + str(backup_name),priority=7)
log_warning = journal.stream("BackupRotation-" + str(backup_name),priority=4)

def debug(s):
    if debug:
        print("DEBUG: "+str(s))

### FUNCTIONS ###
del_list = dict()
def func_walk_dir(dir_name):
    for folder, subs, files in os.walk(dir_name):
        for f in files:
            filearg = func_parse_filename(f,dir_name)
    for k,v in del_list.items():
            #debug(len(v))
        if len(v) <= min_total:
            log_debug.write(str(v[0]) + " not removed because there are less than " + str(min_total) + " backups remaining.")
            continue
        else:
            for entry in v:
                func_delete(*entry)

def func_parse_filename(filename,dir_name):
    underscore_split = filename.split('_')
    name = underscore_split[0]
    try:
        date = underscore_split[1].split('.')[0]
        extension = filename[len(name)+len(date)+2:]
    except IndexError:
        log_debug.write(filename + " in " + dir_name + " no extension " + "-> file ignored\n")
        return
    if extension in extensions:
            #debug((name,filename,dir_name,date,extension))
        if name in del_list:
            del_list[name] += [(filename,dir_name,date,name,extension)]
        else:
            del_list[name] =  [(filename,dir_name,date,name,extension)]

def func_delete(filename,dir_name,str_logdate,name,ext):
    today = datetime.today()
    try:
        logdate = dateutil.parser.parse(str_logdate)
    except ValueError:
        debug(("Value error: "+ filename))
        log_debug.write(filename + " in "+ dir_name + " unrecognized date format: " + str_logdate + " -> file ignored\n")
        return False
    if ( (today - logdate).days < max_daily ):
        debug(("daily: " + filename))
        return False
    if ( logdate.isoweekday() == day_of_weekly_backup  and (today - logdate).days / 7 < max_weekly  ):
        debug(("weekly: " + filename))
        return False
    if ( logdate.day == day_of_monthly_backup and   today.year == logdate.year and today.month - logdate.month  < max_monthly ):
        debug(("monthly: " + filename))
        return False
    if ( logdate.day == day_of_monthly_backup and   logdate.month == month_of_yearly_backup and today.year - logdate.year    < max_yearly  ): 
        debug(("yearly: "+filename))
        return False
    try:
        os.remove(os.path.join(dir_name,filename))
    except Exception as e:
        log_warning.write(str(e)+"\n")
        debug(("exception: " + filename + " " + str(e)))
        return False
    debug(("deleted:" + filename))
    return True

### SCRIPT ###
if backup_dir != None:
    func_walk_dir(backup_dir)
    log_warning.close()
    log_debug.close()
