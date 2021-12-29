#!/usr/bin/python3
#
# BEFORE RUNNING THIS 'dsmr_definition.py' SCRIPT:
# Generate a text file with a complete single P1 telegram in
# directory /home/pi/dsmr/ by executing 'p1_telegram_discovery.py'.
# Default text file name is 'standard_telegram.txt'.
#
# Script 'dsmr_definition.py' analyzes the standard p1 telegram 
# to define the length of required datafields.
# Run this script to generate the telegram definitions
# to be used by the 'p1_listener.py' script.
#
# This script evaluates only the obis codes that are
# included in the obis code listing specified in the config file.
# The value shown with each OBIS code is the variable
# name to be used in the 'p1_listener.py' script.
#
# Configuration settings are taken from /home/pi/dsmr/dsmr_definition.conf.
#
# Created by Bram Langen - Mar 5, 2020.
# v1.50 - Modified to work with a config file.

from    colorama                   import Fore, Style
from    configparser               import ConfigParser;
import  os;
from    re                         import sub as substitute;
import  sys;
# Add the local library to the default path listing.
sys.path.insert(0, '/home/pi/local_lib');
from    local_lib.custom_functions import *;

############################################################
# Obtain the config file name based on the
# name of the script.
# sys.argv[0] is the script path and file name
############################################################
path, logfile, configfile = generate_filenames(sys.argv[0]);
if path == '':
    # obtain the path if the script is run locally
    import pathlib;
    path = str(pathlib.Path(__file__).parent.resolve()) + '/';

############################################################
# Initialize / declare variables
############################################################
obis_count      = 0;
object_list     = [];
obis            = 0;
long_text       = 1;
IP_id           = 2;
ws_id           = 3;


############################################################
# Obtain the variables from the configuration file.
# Create object_list tuple: obis, long_text, IP_id, ws_id
############################################################
print(f'Parsing configuration file {configfile}.');

if os.path.isfile(configfile):
    parser = ConfigParser();
    parser.read(configfile);
    if 'path' in parser['path']:
        path            = parser['path']['path'];
    standard_telegram   = parser['files']['standard telegram'];
    object_definitions  = parser['files']['object definitions'];
    if 'log' in parser['files']:
        logfile         = parser['files']['log'];
    if 'target' in parser['timezone']:
        target_timezone = parser['timezone']['target'];
    for key in parser['obis']:
        # combine the key name with the key data...
        obis_data       = parser['obis'][key] + ' ' + key + ' ' + ' ';
        # ... convert the data to a tuple ...
        obis_data       =   obis_data.split(' ');
        # ... and append this dataset to the list
        object_list.append(obis_data);
else:
    print('a', f'Config file {configfile} not found.');
    exit();

############################################################
# Verify directory dsmr exists, and create it if it doesn't
# (Normally not needed, as this script should reside in
# the dsmr directory.
############################################################
if not os.path.isdir('/home/pi/dsmr'):
    os.mkdir('home/pi/dsmr');
    print ('Directory "dsmr" created.');

############################################################
# Read the file with the complete telegram as transmitted
# by the smart meter.  For each matching line, write an 
# entry in the definitions file with the specifics for
# each data object.
############################################################
if os.path.isfile(standard_telegram):
    print (f'Now reading file {Style.BRIGHT}{standard_telegram}{Style.RESET_ALL}');
    f_read  = open(standard_telegram, 'r');
    print (f'and writing file {Style.BRIGHT}{object_definitions}{Style.RESET_ALL}.');
    f_write = open(object_definitions, 'w');
    f_write.write('# This file is generated by ' + sys.argv[0] + '\r\n');
    while True:
        input_line = f_read.readline();
        if input_line[0:1] == '!':
            # The last line of the telegram is the CRC value, preceded by an exclamation mark.
            break
        for object in object_list:
            if object[0] in input_line:
                if input_line[2] == '0':
                    # The channel number is '0' for the electricity meter, and a higher number for the gas meter.
                    stripped_line = substitute(r'[a-zA-Z*]', '', input_line);
                    starting_position = stripped_line.find('(') +1;
                    ending_position = stripped_line.find(')');
                else:
                    stripped_line = input_line.replace('*m3', '');
                    starting_position = stripped_line.find('(') +1;
                    ending_position = stripped_line.find(')', -2);     # search for the ending bracket only.
                f_write.write(object[obis] + ';' + str(starting_position) + ';' + \
                    str(ending_position) + ';' + object[long_text] + ';' + \
                    object[IP_id] + ';' + object[ws_id] + ';\r\n');
                obis_count += 1;
    f_read.close();
    f_write.close();
    print (f'Script completed {Fore.GREEN}{Style.BRIGHT}succesfully{Style.RESET_ALL}, converted {Style.BRIGHT}{obis_count}{Style.NORMAL} obis codes.');
else:
    print (f'Error: file {standard_telegram} not found');
exit()
