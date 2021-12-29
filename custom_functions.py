# Python3 module to be called from other scripts.
# This script contains frequently used custom functions.
# Created March 5, 2020 by Bram Langen.
# Version 1.24 - Added path to the config file name

from datetime   import datetime;
from pytz       import common_timezones, timezone;
from time       import daylight, time, tzname;
import sys

############################################################
# Convert a unix timestamp from one specified timezone to 
# another timezone.
# Default conversion is from local to system timezone.
############################################################
def convert_timezone(original_ts, original_timezone, target_timezone):
    'Convert a unix timestamp from one timezone to another timezone'
    if original_timezone == 'system':
        try:
            original_timezone = tzname[daylight];
        except:
            # Assume local timezone if no timezone was specified,
            # or if the specified timezone does not exist.
            original_timezone = target_timezone;
    elif original_timezone == '' or not original_timezone in common_timezones:
        # Assume local timezone if no timezone was specified,
        # or if the specified timezone does not exist.
        original_timezone = target_timezone;
    original_TzInfo     = timezone(original_timezone);
    
    if target_timezone == 'system':
        target_timezone = tzname[daylight];
    elif target_timezone == '' or not target_timezone in common_timezones:
        # Assume system timezone if no timezone was specified,
        # or if the specified timezone does not exist.
        target_timezone = tzname[daylight];
    target_TzInfo     = timezone(target_timezone);
    
    original_time_tuple = datetime.fromtimestamp(original_ts);
    new_time_tuple      = original_TzInfo.localize(original_time_tuple).astimezone(target_TzInfo);
    naive_time_tuple    = new_time_tuple.replace(tzinfo=None);
    new_ts              = datetime.timestamp(naive_time_tuple);
    return new_ts;

############################################################
# Generate associated filenames based on the script name.
# Added logic to also return proper values if the script
# is called directly using './' in front of the scriptname.
############################################################
def generate_filenames(script):
    'This function generates filenames for logfile and config file, and determines the path'
    if script[0:2] == './':
        # Remove the 'execute' characters, if used.
        script  = script[2:];
    index_start = script.rfind('/')+1;          # Find the last slash
    index_end   = script.find('.');             # Find the extension dot
    scriptname  = script[index_start:index_end];
    path        = script[:index_start];
    logfile     = 'logs/' + scriptname + '.log';
    configfile  = path + script[index_start:index_end] + '.config';
    return path, logfile, configfile;

############################################################
# Generate a timestamp in format 2018-11-25 21:59:25, based
# on the current system time converted to local time.
############################################################
def get_time(target_timezone):
    'This function generates a timestamp'
    ts = time();                        #Obtain current time
    converted_ts = convert_timezone(ts, 'system', target_timezone)
    return datetime.fromtimestamp(converted_ts).strftime('%Y-%m-%d %H:%M:%S');

############################################################
# Write a log entry to the log specified, in the format
#         'timestamp - log_entry_specifics'.
# The first attribute defines whether or not the file
# content will be cleared first, or appended to.
############################################################
def write_log_entry(write_or_append, log_entry_specifics, logsetting):
    'This function writes an entry in the log'
    timestamp = get_time(logsetting[1]);
    f=open(logsetting[0], write_or_append);
    f.write (timestamp);
    f.write (' - ');
    f.write (log_entry_specifics);
    f.write ('\r\n');
    f.close();
    return;

############################################################
# The next section is executed only if this script is called
# directly.  It can be used for testing purposes.
# Call this script with the function name and arguments.
############################################################
if __name__ == '__main__':
    # The first argument  always is the script name, so the
    # count will be only be >1 if  arguments have been supplied.
    # Default timezone for testing is Europe/Amsterdam.
    if len(sys.argv) == 1:
        print ('No arguments supplied!');
        print ('use "get_time" to obtain a timestamp');
        print ('use "write_log_entry [a (append) or w (write over)] [message] [name_of_logfile]" (note: default timezone will be used)');
        print ('use "convert_timezone [unix_timestamp_to_convert] [original_timezone] [target_timezone]"');
        print ('use "generate_filenames [scriptname with or without full path]"');
        print ('All arguments required, entered without quotes or brackets.');
    else:
        target_timezone = 'Europe/Amsterdam';
        if sys.argv[1] == 'get_time':
            print (get_time(target_timezone));
        elif sys.argv[1] == 'write_log_entry':
            if len(sys.argv) != 5:
                print ('use "write_log_entry [w(or a)] [message] [name_of_logfile]" (note: default timezone will be used)');
            else:
                logdir = '/home/pi/logs/';
                if logdir in sys.argv[4]:
                    logfile = sys.argv[4];
                else:
                    logfile = logdir + sys.argv[4];
                write_log_entry(sys.argv[2], sys.argv[3], (logfile, target_timezone));
                print (get_time(target_timezone) + ' - ' + sys.argv[3] + ' written to ' + logfile);
        elif sys.argv[1] == 'convert_timezone':
            if len(sys.argv) != 5:
                print ('use "convert_timezone [unix_timestamp_to_convert] [original_timezone] [target_timezone]"');
            else:
                print (convert_timezone(float(sys.argv[2]), sys.argv[3], sys.argv[4]));
        elif sys.argv[1] == 'generate_filenames':
            if len(sys.argv) != 3:
                print ('use "generate_filenames [scriptname with or without full path]"');
            else:
                path, logfile, configfile = (generate_filenames(sys.argv[2]));
                print('path: ' + path);
                print('logfile: ' + logfile);
                print('configfile: ' + configfile);
        else:
            print ('unknown function name specified');
            
    sys.exit;
