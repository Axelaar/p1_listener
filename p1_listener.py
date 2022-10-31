#!/usr/bin/python3
#
# Obtain actual energy consumption and send it 
# as an IP telegram, as a websocket transmission or
# as an update of a RRD database.
# This script relies on two text files:
#  A file containing a standard telegram;
#  A file containing the obis definitions;
# The obis definitions in the 'obis definitions'file define
# which values will be read from the smart meter.
# The location of these files is specified in the config file.
# 
# Configuration settings are taken from p1_listener.conf.
#
# This script is triggered by systemd service 'p1_listener.service' 
# when the network is up.
#
# Created by Bram Langen - Mar 3, 2020
# version 4.10 - Added error trapping in parser section.

from    colorama                    import Fore, Style
from    configparser                import ConfigParser;
from    os.path                     import isfile;
from    re                          import sub as substitute;
import  serial;
import  sys;
from    time                        import sleep;
# Add the local library to the default path listing.
sys.path.insert(0, '/home/pi/local_lib');
try:
    from custom_functions  import *;
except:
    print(f'{Style.BRIGHT}{Fore.RED}Error importing from module {Fore.WHITE}custom_functions{Fore.RED}, script halted.{Style.RESET_ALL}');
    exit();

############################################################
# For testing purposes this this script is to be called with 
# any argument.
# This debug mode will display the most relevant information.
############################################################
if len(sys.argv) > 1:
    debug = True;
else:
    debug = False;

############################################################
# Obtain the logfile and config file names based on the
# name of the script.
# sys.argv[0] is the script path and file name
############################################################
path, logfile, configfile = generate_filenames(sys.argv[0]);
if path == '':
    # obtain the path if the script is run locally
    import pathlib;
    path = str(pathlib.Path(__file__).parent.resolve()) + '/';
if debug:
    print(f'path:    {Style.BRIGHT}{path}{Style.NORMAL}');
    print(f'logfile: {Style.BRIGHT}{logfile}{Style.NORMAL}');

############################################################
# Set default variables.  These values can be overridden
# by the configuration settings.
############################################################
target_timezone         = 'Europe/Amsterdam';  # Must come before logsettings
delimiter               = ';';
logsettings             = path + logfile, target_timezone;
timer_IP                = 300;
timer_rrd               = 300;
timer_ws                = 300;

############################################################
# Obtain the variables from the configuration file.
############################################################
if isfile(configfile):
    try:
        if debug:
            print(f'Parsing configuration file {configfile}.');
        parser = ConfigParser();
        parser.read(configfile);
        #################  PATH  ################
        if 'path' in parser['path']:
            path            = parser['path']['path'];
            if debug: 
                print(f'variable {Style.BRIGHT}path{Style.NORMAL} set to '
                    f'{Style.BRIGHT}{path}{Style.NORMAL}');
        #################  FILES  ###############
        standard_telegram   = path + parser['files']['standard telegram'];
        object_definitions  = path + parser['files']['object definitions'];
        if 'log' in parser['files']:
            logfile         = path + parser['files']['log'];
            if debug:
                print(f'\r\nLogfile {Style.BRIGHT}{logfile}{Style.NORMAL} will be used.');
        if 'daily counter logfile' in parser['files'] and len(parser['log counters']) > 0:
            daily_logfile   = path + parser['files']['daily counter logfile'];
            if debug:
                print(f'\r\ndaily counter logfile {Style.BRIGHT}{daily_logfile}{Style.NORMAL} will be used with entries:');
            log_object_list  = [];
            log_object_index = [];
            for key in parser['log counters']:
                log_object_index.append(key);
                log_object_list.append((parser['log counters'], parser['log counters'][key]));
                if debug:
                    print(f'{Style.BRIGHT}{parser["log counters"][key]}{Style.NORMAL}');
        else:
            if debug:
                print('\r\nno daily counter logfile will be used.');
        #################  PORTS  ###############
        p1_usb_port         = parser['ports']['p1 usb port'];
        if debug:
            print(f'\r\nUSB port to be used: {Style.BRIGHT}{parser["ports"]["p1 usb port"]}{Style.NORMAL}');
        ###############  TIMEZONE  ##############
        if 'target' in parser['timezone']:
            target_timezone = parser['timezone']['target'];
            if debug: 
                print(f'\r\nvariable {Style.BRIGHT}target_timezone{Style.NORMAL} set to '
                    f'{Style.BRIGHT}{target_timezone}{Style.NORMAL}');
        ###################  IP  ################
        if len(parser['IP telegrams']) > 0:
            use_IP_telegram         = True;
            host                    = parser['IP telegrams']['host'];
            timer_IP                = int(parser['IP telegrams']['timer']);
            try:
                from socket import socket, AF_INET, SOCK_DGRAM;
            except:
                print(f'{Style.BRIGHT}{Fore.RED}Error importing from module: {Fore.WHITE}socket{Style.RESET_ALL}');
                write_log_entry('a', 'Error importing from module "socket"', logsettings);
                exit();
            try:
                from IP_transmit import *;
            except:
                print(f'{Style.BRIGHT}{Fore.RED}Error importing from module: {Fore.WHITE}IP_transmit{Style.RESET_ALL}');
                write_log_entry('a', 'Error importing from module IP_transmit', logsettings);
                exit();
            UDPSock                 = socket(AF_INET, SOCK_DGRAM);
            UDPSock_error           = False;
            IP_object_list          = [];
            if debug: 
                print(f'\r\nUse IP telegrams?  {Style.BRIGHT}{str(use_IP_telegram)}{Style.NORMAL}');
                print('The following obis code/port/IP combinations will be used:');
            for key in parser['IP telegrams']:
                if key != 'host' and key != 'timer':
                    # Add the host IP and convert the data to a tuple...
                    data            = substitute(' +', ' ', parser['IP telegrams'][key] + ' ' + host).split(' ');
                    if debug:
                        print(f'{Style.BRIGHT}{data}{Style.NORMAL}');
                    # ... convert the port number from string to integer...
                    data[1]         = int(data[1]);
                    # ... and finally append this dataset to the list
                    IP_object_list.append(data);
        else:
            use_IP_telegram         = False;
            if debug: 
                print(f'\r\nUse IP telegrams?  {Style.BRIGHT}{str(use_IP_telegram)}{Style.NORMAL}');
        ###################  WS  ################
        if len(parser['websocket']) > 0:
            use_ws_telegram         = True;
            ws_connection           = parser['websocket']['connection detail'];
            timer_ws                = int(parser['websocket']['timer']);
            try:
                from websocket import create_connection;
            except:
                print(f'{Style.BRIGHT}{Fore.RED}Error importing from module: {Fore.WHITE}websocket{Style.RESET_ALL}');
                write_log_entry('a', 'Error importing from module "websocket"', logsettings);
                exit();
            try:
                from ws_transmit import *;
            except:
                print(f'{Style.BRIGHT}{Fore.RED}Error importing from module: {Fore.WHITE}ws_transmit{Style.RESET_ALL}');
                write_log_entry('a', 'Error importing from module "ws_transmit"', logsettings);
                exit();
            ws_object_list          = [];
            if debug: 
                print(f'\r\nUse Websocket?  {Style.BRIGHT}{str(use_ws_telegram)}{Style.NORMAL}');
                print(f'Websocket connection: {Style.BRIGHT}{ws_connection}{Style.NORMAL}');
                print('The following obis code/ID combinations will be used:');
            for key in parser['websocket']:
                if key != 'connection detail' and key != 'timer':
                    # Convert the data to a tuple...
                    data            = substitute(' +', ' ', parser['websocket'][key]).split(' ');
                    if debug:
                        print(f'{Style.BRIGHT}{data}{Style.NORMAL}');
                    # ... and append this dataset to the list
                    ws_object_list.append(data);
        else:
            use_ws_telegram         = False;
            if debug: 
                print(f'\r\nUse Websocket?  {Style.BRIGHT}{str(use_IP_telegram)}{Style.NORMAL}');
        ###############  DATABASE  ##############
        if len(parser['database']) > 0:
            use_rrd                 = True;
            if 'rrddb_e' in parser['database']:
                rrddb_e             = path + parser['database']['rrddb_e'];
            if 'rrddb_g' in parser['database']:
                rrddb_g             = path + parser['database']['rrddb_g'];
            timer_rrd               = int(parser['database']['timer']);
            try:
                from update_rrd import *;
            except:
                print(f'{Style.BRIGHT}{Fore.RED}Error importing from module: {Fore.WHITE}update_rrd{Style.RESET_ALL}');
                write_log_entry('a', 'Error importing from module "update_rrd"', logsettings);
                exit();
            write_log               = True;
            rrd_object_list         = [];
            if debug: 
                print(f'\r\nWrite to database(s)?  {Style.BRIGHT}{str(use_rrd)}{Style.NORMAL}');
                if 'rrddb_g' in locals():
                    print(f'Gas db: {Style.BRIGHT}{rrddb_g}{Style.NORMAL}');
                if 'rrddb_e' in locals():
                    print('The following obis codes will be used to write to '
                        f'Electricity db: {Style.BRIGHT}{rrddb_e}{Style.NORMAL}');
            for key in parser['database']:
                if key[:3] != 'rrd' and key != 'timer':
                    if debug and 'rrddb_e' in locals():
                        print(f'{Style.BRIGHT}{parser["database"][key]}{Style.NORMAL}');
                    rrd_object_list.append(parser['database'][key]);
        ###############  Wrap-up  ##############
        logsettings = path + logfile, target_timezone;
        if not use_IP_telegram and not use_rrd and not use_ws_telegram:
            if debug:
                print(f'{Style.BRIGHT}{Fore.RED}Nothing to send, script halted.{Style.RESET_ALL}');
            write_log_entry('a', 'Nothing to send, script halted.', logsettings);
            exit(0);
    except:
        if debug:
            print('Error while parsing config file, script halted.');
        write_log_entry('a', 'Error while parsing config file, script halted.', logsettings);
        exit(0);
else:
    message = f'Config file {configfile} not found, script halted..';
    if debug:
        print(message);
    write_log_entry('a', message, logsettings);
    exit();

############################################################
# Define data_object class.
# This class is used to link the obis code to the variable,
# and to the transmission identifiers for websocket and IP.
# Variable is the variable name as used in this script to
# refer to an obis code in normal text.  For instance, 
# obis code '1-0:1.8.1' becomes 'kwh_total_in_tariff1' in 
# the calculations in this script.
# ws_id is the 5-character code used as identifier in the 
# websocket transmissions, i.e. 'L__In' for obis code '1-0:1.8.1'
############################################################
class data_object:
    def __init__(self, obis, starting_position, ending_position, variable, IP_id, ws_id):
        self.obis = obis;
        self.starting_position  = starting_position;
        self.ending_position    = ending_position;
        self.variable           = variable;
        self.IP_id              = IP_id;
        self.ws_id              = ws_id;

############################################################
# Populate the attributes of the objects by
# reading the object definitions file.
# Set each variable to 'None'.
# Declare a companion 'previous' variable for each object
# entry, and set it to 'None' as well.
# Any error in this section will terminate the script.
############################################################
if debug:
    print(f'\r\nReading object definitions file {object_definitions}.');

if isfile(object_definitions):
    linecounter = 0;
    try:
        f_read = open(object_definitions, 'r');
        object_list = [];           # List contains all definitions per object
        obis_list   = [];           # List contains only the obis identifiers
        while True:
            input_line = f_read.readline();
            if input_line == '':
                break;
            elif (delimiter in input_line and input_line[:9] != '1-3:0.2.8'):
                # The 'and' statement in this 'elif' skips the dsmr version line.
                defs = input_line.split(delimiter);
                # Data object attributes are: obis, starting_position, ending_position, variablename 
                # and the two placeholders for the IP and ws identifiers.
                object_list.append(data_object(defs[0], defs[1], defs[2], defs[3], defs[4], defs[5]));
                obis_list.append(defs[0]);
                # Now set the variable and 'previous variable' to 'None'
                exec(f'{defs[3]} = {"previous_" + defs[3]} = None');
                linecounter += 1;
        if debug:
            print(f'\r\nProcessed {linecounter} object definitions (index, obis code, variable name):');
            for i in range(len(object_list)):
                print(f'{i}: \t{object_list[i].obis} \t{object_list[i].variable}');
    except:
        message = 'Error reading object definitions, script halted.';
        if debug:
            print(f'{Style.BRIGHT}{Fore.RED}{message}{Style.RESET_ALL}');
        write_log_entry('a', message, logsettings);
        sys.exit (message);
    f_read.close();
else:
    message = 'Object definitions file not found, script halted.';
    if debug:
        print(f'{Style.BRIGHT}{Fore.RED}{message}{Style.RESET_ALL}');
    write_log_entry('a', message, logsettings);
    sys.exit (message);

############################################################
# Find and assign the indexes of the kWh_total obis codes.
############################################################
index_list = [];
for obis in obis_list:
    if obis   == '1-0:1.8.1':
        index_list.append(obis_list.index(obis));
    elif obis == '1-0:1.8.2':
        index_list.append(obis_list.index(obis));
    elif obis == '1-0:2.8.1':
        index_list.append(obis_list.index(obis));
    elif obis == '1-0:2.8.2':
        index_list.append(obis_list.index(obis));

if debug:
    print(f'\r\nindex_list contains {Style.BRIGHT}{len(index_list)}{Style.NORMAL} kWh_total entries.');

############################################################
# Update the object_list with the IP identifiers,
# if IP telegrams are used.
# The list is declared by default, as it is used
# further on in the script.
############################################################
IP_obis_list = [];
if use_IP_telegram:
    linecounter = 0;
    for i in range(len(IP_object_list)):
        IP_obis = IP_object_list[i][0];
        IP_obis_list.append(IP_obis);
        linecounter += 1;
        for obis in obis_list:
            if obis == IP_obis:
                index = obis_list.index(obis);
                object_list[index].IP_id = IP_object_list[i][2],IP_object_list[i][1];
    if debug:
        print(f'\r\nProcessed   {linecounter} IP objects (index, obis code, host, port):');
        for i in range(len(IP_object_list)):
            list_entry = IP_object_list[i];
            print(f'{i}: \t{list_entry[0]} \t{list_entry[2]} \t{list_entry[1]}');
    ############################################################
    # Determine which kWh totals must be transmitted, if any.
    ############################################################
    IP_kWh_counters_index_list = [];
    linecounter = 0;
    for index in index_list:
        if obis_list[index] in IP_obis_list:
            IP_kWh_counters_index_list.append(index);
            linecounter += 1;
    if debug:
        print(f'\r\nProcessed {Style.BRIGHT}{linecounter}{Style.NORMAL} IP kWh counter objects.');
    if len(IP_kWh_counters_index_list) > 0:
        transmit_IP_counters = True;
    else:
        transmit_IP_counters = False;

############################################################
# Set the websocket identifiers if websocket is used.
# The list is declared by default, as it is used
# further on in the script.
############################################################
ws_obis_list = [];
if use_ws_telegram:
    linecounter = 0;
    for ws_obis in ws_object_list:
        ws_obis_list.append(ws_obis[0]);
        linecounter += 1;
        for obis in obis_list:
            if obis == ws_obis[0]:
                index = obis_list.index(obis);
                object_list[index].ws_id = ws_obis[1];
        
    if debug:
        print(f'\r\nProcessed {linecounter} Websocket objects (index, obis code, name):');
        for i in range(len(ws_object_list)):
            list_entry = ws_object_list[i];
            print(f'{i}: \t{list_entry[0]} \t{list_entry[1]}');
    ############################################################
    # Determine which kWh totals must be transmitted, if any.
    ############################################################
    ws_kWh_counters_index_list = [];
    linecounter = 0;
    for index in index_list:
        if obis_list[index] in ws_obis_list:
            ws_kWh_counters_index_list.append(index);
            linecounter += 1;
    
    if debug:
        print(f'\r\nProcessed {Style.BRIGHT}{linecounter}{Style.NORMAL} Websocket kWh counter objects.');
    
    if len(ws_kWh_counters_index_list) > 0:
        transmit_ws_counters = True;
    else:
        transmit_ws_counters = False;

############################################################
# Obtain the dsmr version from the standard telegram file.
############################################################
if isfile(standard_telegram):
    try:
        f_read = open(standard_telegram, 'r');
        while True:
            input_line = f_read.readline();
            if input_line == '':
                break;
            elif input_line[:9] == '1-3:0.2.8':
                index = input_line.find('(');
                dsmr_version = input_line[index+1];
                break;
            elif input_line[:4] == '/FLU':
                dsmr_version = input_line[4];
                break;
        # Test to see if the DSMR version has been obtained.
        test = dsmr_version;
        if debug:
            print(f'DMSR version to be used: {Style.BRIGHT}{dsmr_version}{Style.NORMAL}.');
         
    except:
        message = 'Error reading dsmr version, script halted.';
        
        if debug:
            print(f'{Style.BRIGHT}{Fore.RED}{message}{Style.RESET_ALL}');
        write_log_entry('a', message, logsettings);
        sys.exit (message);
    f_read.close();
else:
    message = 'standard telegram file not found, script halted.';
    if debug:
        print(f'{Style.BRIGHT}{Fore.RED}{message}{Style.RESET_ALL}');
    write_log_entry('a', message, logsettings);
    sys.exit (message);

############################################################
# Set COM port config depending on dsmr version
############################################################
ser                 = serial.Serial();
ser.port            = p1_usb_port;
ser.timeout         = 20;
if dsmr_version == '3':
    ser.baudrate    = 9600;
    ser.bytesize    = serial.SEVENBITS;
    ser.parity      = serial.PARITY_EVEN;
    ser.stopbits    = serial.STOPBITS_ONE;
    ser.xonxoff     = 1;
    ser.rtscts      = 0;#              # Enable hardware (RTS/CTS) flow control.
elif dsmr_version > '3':
    ser.baudrate    = 115200;
    ser.bytesize    = serial.EIGHTBITS;
    ser.parity      = serial.PARITY_NONE;
    ser.stopbits    = serial.STOPBITS_ONE;
    ser.xonxoff     = 1;
    ser.rtscts      = 0;

if debug:
    print(f'\r\nport settings are: {Style.BRIGHT}{ser.baudrate}'
        f'{ser.bytesize} {ser.parity} {ser.stopbits}{Style.NORMAL}\r\n');

#############################################################
# Initialize variables
############################################################
counter_IP                  = 250;
counter_rrd                 = 250;
counter_ws                  = -2;
data_is_good                = False;
do_daily_log                = True;
error_msg                   = '';
found_p1_telegram_start     = False;
log_e                       = True;
log_g                       = True;
midnight                    = False;
new_gas_reading             = False;
p1_telegram_complete        = False;
serial_port_is_open         = False;
ts_gas = previous_ts_gas    = None;

############################################################
#
# Main script starts here
#
############################################################
write_log_entry('a', f'Script {sys.argv[0]} successfully started.', logsettings);

###########################################################
# Open COM port, if it fails then abort the script.
# Start the perpetual loop
############################################################
while True:
    if not serial_port_is_open:
        try:
            ser.open();
            message = f'Serial port {ser.name} opened.';
            write_log_entry('a', message, logsettings);
            serial_port_is_open = True;
            if debug:
                print(message);
        except:
            message = f'Error opening port {ser.name}, script halted.';
            write_log_entry('a', message, logsettings);
            if debug:
                print(f'{Style.BRIGHT}{Fore.RED}{message}{Style.RESET_ALL}');
            sys.exit (message);

    ############################################################
    # Receive a data transmission line 
    ############################################################
    try:
        p1_raw = ser.readline();                                        # readline() returns bytes, not text!
    except:
        message = f'Error reading port {ser.name}, port will be closed.';
        write_log_entry('a', message, logsettings);
        ser.close();
        serial_port_is_open = False;
        if debug:
            print(message);
        sleep(15);
    ##############################################################
    # Only execute the rest of the code if the port is open and
    # hence a transmission could have been received.
    ##############################################################
    try:
        if serial_port_is_open:
            p1_line = bytes.decode(p1_raw, errors='ignore').strip();    # Ignore errors - they occur when the p1
            data_is_good = True;                                        # cable has been disconnected and then reconnected.
    except:
        message = f'Error decoding data, port {ser.name} will be closed.';
        write_log_entry('a', message, logsettings);
        ser.close();
        serial_port_is_open = False;
        data_is_good        = False;
        if debug:
            print(message);
        sleep(15);
    if data_is_good:
        ##########################################################
        # When the script first starts up, the received line of
        # transmitted data may be in the middle of a telegram set. 
        # This means some variables may still be 'None', causing
        # incomplete data.
        # Only start the interpretation of data once the opening
        # telegram line has been received.  The first character
        # of (only) that line is '/'.
        ##########################################################
        if not found_p1_telegram_start:
            try:
                if p1_line[0] == '/':
                    found_p1_telegram_start = True;
            except:
                pass;
        elif found_p1_telegram_start:
            ##########################################################
            # Interpret the received line of transmitted data.
            # The data lines start with the obis code, followed by 
            # the transmitted data.  When a matching code is found, assign
            # the data value to the variable linked to the obis code as 
            # defined in the data_object dataset.
            ##########################################################
            if not p1_telegram_complete:
                try:
                    if p1_line[0:1] == '!':                     # end of a complete transmission reached
                        p1_telegram_complete = True;
                except:
                    pass;
            try:
                if (p1_line[0:1] == "/"):                   # This signals the first line of a telegram set.
                    if dsmr_version > '4':                  # It is used to increment the time counters.
                            counter_IP  += 1;               # dsmr version 5 and higher sends every second.
                            counter_ws  += 1;
                            counter_rrd += 1;
                    else:                                   # up to dsmr version 4 telegrams are sent every 10 seconds.
                            counter_IP  += 10;              # add the 10-second tick to the counters
                            counter_ws  += 10;
                            counter_rrd += 10;
                for obis in obis_list:
                    if obis in p1_line:
                        index = obis_list.index(obis);
                        if obis[2] == '0':
                            # Electricity data is listed on channel '0', which is
                            # the third character (=index '2') of the obis code.
                            # Gas data is typically listed on channel '1'.
                            value = float(p1_line[int(object_list[index].starting_position):int(object_list[index].ending_position)]);
                            if 'kW' in p1_line or 'V' in p1_line:
                                exec('%s = %f' % (object_list[index].variable, value));
                            else:
                                exec('%s = %d' % (object_list[index].variable, value));
                        else:
                            ts_gas = p1_line[int(object_list[index].starting_position):p1_line.find(')')];
                            if ts_gas != previous_ts_gas:
                                previous_ts_gas = ts_gas;
                                new_gas_reading = True;
                                value = float(p1_line[p1_line.find(')(') + 2 :int(object_list[index].ending_position)]);
                                exec('%s = %f' % (object_list[index].variable, value));
                        break;
            except:
                message = 'Error decoding telegram.';
                write_log_entry('a', message, logsettings);
                if debug:
                    print(message);
        
        if p1_telegram_complete:
            ##########################################################
            #
            # Now do something with the received data - send it to the
            # receiver(s) as defined in the configuration file.
            # 
            ##########################################################
            ##########################################################
            # Which variables are to be used is defined in the config 
            # file, they will be part of the IP_obis_list
            # or ws_obis_list or both.
            #
            # Each received line of transmitted data is evaluated here
            # to see if it matches an obis code in an obis list.
            # 
            # For each change in tariff or power in/out, send 
            # an IP and/ or ws transmission.
            # Send the Electricity counter totals only when the timer 
            # reaches the setpoint.
            # Send the gas counter total only when a new timestamp 
            # has been received.
            ##########################################################
            addr = object_list[index].IP_id;
            if object_list[index].obis == '0-0:96.14.0':
                # This is the tariff indicator
                if tariff != previous_tariff:
                    previous_tariff = tariff;
                    if debug:
                        print(f'0-0:96.14.0 \t{tariff}');
                    if '0-0:96.14.0' in IP_obis_list:
                        UDPSock_error, error_msg = IP_transmit(addr, str(tariff), UDPSock_error);
                    if '0-0:96.14.0' in ws_obis_list:
                        ws_transmit(ws_connection, object_list[index].ws_id, tariff, delimiter);
            elif object_list[index].obis == '1-0:1.7.0':
                # This is the actual power in, in kW.
                if kw_actual_in != previous_kw_actual_in:
                    previous_kw_actual_in = kw_actual_in;
                    if debug:
                        print(f'1-0:1.7.0 \t{kw_actual_in}');
                    if '1-0:1.7.0' in IP_obis_list:
                        UDPSock_error, error_msg = IP_transmit(addr, str(kw_actual_in), UDPSock_error);
                    if '1-0:1.7.0' in ws_obis_list:
                        ws_transmit(ws_connection, object_list[index].ws_id, kw_actual_in, delimiter);
            elif object_list[index].obis == '1-0:2.7.0':
                # This is the actual power out, in kW.
                if kw_actual_out != previous_kw_actual_out:
                    previous_kw_actual_out = kw_actual_out;
                    if debug:
                        print(f'1-0:2.7.0 \t{kw_actual_out}');
                    if '1-0:2.7.0' in IP_obis_list:
                        UDPSock_error, error_msg = IP_transmit(addr, str(kw_actual_out), UDPSock_error);
                    if '1-0:2.7.0' in ws_obis_list:
                        ws_transmit(ws_connection, object_list[index].ws_id, kw_actual_out, delimiter);
            elif object_list[index].obis == '1-0:21.7.0':
                # This is the actual power in for phase A, in kW.
                if kw_actual_in_a != previous_kw_actual_in_a:
                    previous_kw_actual_in_a = kw_actual_in_a;
                    if debug:
                        print(f'1-0:21.7.0 \t{kw_actual_in_a}');
                    if '1-0:21.7.0' in IP_obis_list:
                        UDPSock_error, error_msg = IP_transmit(addr, str(kw_actual_in_a), UDPSock_error);
                    if '1-0:21.7.0' in ws_obis_list:
                        ws_transmit(ws_connection, object_list[index].ws_id, kw_actual_in_a, delimiter);
            elif object_list[index].obis == '1-0:41.7.0':
                # This is the actual power for phase B, in kW.
                if kw_actual_in_b != previous_kw_actual_in_b:
                    previous_kw_actual_in_b = kw_actual_in_b;
                    if debug:
                        print(f'1-0:41.7.0 \t{kw_actual_in_b}');
                    if '1-0:41.7.0' in IP_obis_list:
                        UDPSock_error, error_msg = IP_transmit(addr, str(kw_actual_in_b), UDPSock_error);
                    if '1-0:41.7.0' in ws_obis_list:
                        ws_transmit(ws_connection, object_list[index].ws_id, kw_actual_in_b, delimiter);
            elif object_list[index].obis == '1-0:61.7.0':
                # This is the actual power for phase C, in kW.
                if kw_actual_in_c != previous_kw_actual_in_c:
                    previous_kw_actual_in_c = kw_actual_in_c;
                    if debug:
                        print(f'1-0:61.7.0 \t{kw_actual_in_c}');
                    if '1-0:61.7.0' in IP_obis_list:
                        UDPSock_error, error_msg = IP_transmit(addr, str(kw_actual_in_c), UDPSock_error);
                    if '1-0:61.7.0' in ws_obis_list:
                        ws_transmit(ws_connection, object_list[index].ws_id, kw_actual_in_c, delimiter);
            elif object_list[index].obis == '1-0:22.7.0':
                # This is the actual power out for phase A, in kW.
                if kw_actual_out_a != previous_kw_actual_out_a:
                    previous_kw_actual_out_a = kw_actual_out_a;
                    if debug:
                        print(f'1-0:22.7.0 \t{kw_actual_out_a}');
                    if '1-0:22.7.0' in IP_obis_list:
                        UDPSock_error, error_msg = IP_transmit(addr, str(kw_actual_out_a), UDPSock_error);
                    if '1-0:22.7.0' in ws_obis_list:
                        ws_transmit(ws_connection, object_list[index].ws_id, kw_actual_out_a, delimiter);
            elif object_list[index].obis == '1-0:42.7.0':
                # This is the actual power for phase B, in kW.
                if kw_actual_out_b != previous_kw_actual_out_b:
                    previous_kw_actual_out_b = kw_actual_out_b;
                    if debug:
                        print(f'1-0:42.7.0 \t{kw_actual_out_b}');
                    if '1-0:42.7.0' in IP_obis_list:
                        UDPSock_error, error_msg = IP_transmit(addr, str(kw_actual_out_b), UDPSock_error);
                    if '1-0:42.7.0' in ws_obis_list:
                        ws_transmit(ws_connection, object_list[index].ws_id, kw_actual_out_b, delimiter);
            elif object_list[index].obis == '1-0:62.7.0':
                # This is the actual power for phase C, in kW.
                if kw_actual_out_c != previous_kw_actual_out_c:
                    previous_kw_actual_out_c = kw_actual_out_c;
                    if debug:
                        print(f'1-0:62.7.0 \t{kw_actual_out_c}');
                    if '1-0:62.7.0' in IP_obis_list:
                        UDPSock_error, error_msg = IP_transmit(addr, str(kw_actual_out_c), UDPSock_error);
                    if '1-0:62.7.0' in ws_obis_list:
                        ws_transmit(ws_connection, object_list[index].ws_id, kw_actual_out_c, delimiter);
            elif object_list[index].obis == '1-0:32.7.0':
                # This is the actual voltage for phase A, in V.
                if v_pha != previous_v_pha:
                    previous_v_pha = v_pha;
                    if debug:
                        print(f'1-0:32.7.0 \t{v_pha}');
                    if '1-0:32.7.0' in IP_obis_list:
                        UDPSock_error, error_msg = IP_transmit(addr, v_pha, UDPSock_error);
                    if '1-0:32.7.0' in ws_obis_list:
                        ws_transmit(ws_connection, object_list[index].ws_id, v_pha, delimiter);
            elif object_list[index].obis == '1-0:52.7.0':
                # This is the actual voltage for phase B, in V.
                if v_phb != previous_v_phb:
                    previous_v_phb = v_phb;
                    if debug:
                        print(f'1-0:32.7.0 \t{v_phb}');
                    if '1-0:32.7.0' in IP_obis_list:
                        UDPSock_error, error_msg = IP_transmit(addr, v_phb, UDPSock_error);
                    if '1-0:32.7.0' in ws_obis_list:
                        ws_transmit(ws_connection, object_list[index].ws_id, v_phb, delimiter);
            elif object_list[index].obis == '1-0:72.7.0':
                # This is the actual voltage for phase C, in V.
                if v_phc != previous_v_phc:
                    previous_v_phc = v_phc;
                    if debug:
                        print(f'1-0:32.7.0 \t{v_phc}');
                    if '1-0:32.7.0' in IP_obis_list:
                        UDPSock_error, error_msg = IP_transmit(addr, v_phc, UDPSock_error);
                    if '1-0:32.7.0' in ws_obis_list:
                        ws_transmit(ws_connection, object_list[index].ws_id, v_phc, delimiter);
            elif object_list[index].obis == '0-1:24.2.1':
                if new_gas_reading:
                    if debug:
                        print(f'0-1:24.2.1 \t{gas}');
                    if '0-1:24.2.1' in IP_obis_list:
                        UDPSock_error, error_msg = IP_transmit(addr, str(gas), UDPSock_error);
                        counter_IP = timer_IP + 1;
                    if '0-1:24.2.1' in ws_obis_list:
                        ws_transmit(ws_connection, object_list[index].ws_id, gas, delimiter);
                        counter_ws = timer_ws + 1;
            if error_msg != '':
                write_log_entry('a', error_msg, logsettings);
                if debug:
                    print(error_msg);
            if use_IP_telegram and counter_IP > timer_IP and transmit_IP_counters:
                # When the preset time has been reached, send the kWh_total counter data,
                # and reset the counter (timer).
                for index in IP_kWh_counters_index_list:
                    exec(f'counter_value = {object_list[index].variable}');
                    IP_transmit(object_list[index].IP_id, str(counter_value), UDPSock_error);
                    if debug:
                        print(f'IP transmit {object_list[index].IP_id} \t{str(counter_value)}');
                counter_IP = -2;
            if use_ws_telegram and counter_ws > timer_ws and transmit_ws_counters:
                # When the preset time has been reached, send the kWh_total counter data,
                # and reset the counter (timer).
                for index in ws_kWh_counters_index_list:
                    exec(f'kWh_value = {object_list[index].variable}');
                    ws_transmit(ws_connection, object_list[index].ws_id, kWh_value, delimiter);
                    if debug:
                        print(f'Websocket transmit {object_list[index].ws_id} \t{kWh_value}');
                counter_ws = -2;
            ##########################################################
            if use_rrd:
                if counter_rrd > timer_rrd:                 # Update the electricity db each time interval as
                    #                                       # defined in the config file.
                    if 'rrddb_e' in locals():               # Test to see if the electricity db has been assigned.
                        ##########################################################
                        # Which variables are to be used is defined in the config 
                        # file, they will be part of the rrd_object_list.
                        ##########################################################
                        data = [];
                        for rrd_obis in rrd_object_list:
                            for obis in obis_list:
                                if obis == rrd_obis:
                                    index = obis_list.index(obis);
                                    break;
                            exec(f'data.append({object_list[index].variable})');
                        # Multiply each kW value in the tuple by 1000 and convert to an integer,
                        # and write the converted values to the database.
                        data_to_rrd = tuple(int(i * 1000) for i in data);
                        log_e = rrd_trigger(rrddb_e, data_to_rrd, log_e, logsettings);
                        if debug:
                            print(f'Wrote to database {rrddb_e}: {data_to_rrd}');
                            if not log_e:
                                print(f'An error occurred, see log file {logsettings[0]}.');
                if 'rrddb_g' in locals():               # Test to see if the gas db has been assigned.
                    if new_gas_reading:                 # Only write to the db when a new gas counter transmission has arrived
                        # Multiply the gasmeter reading by 1000, convert to an integer, and write to the database.
                        log_g = rrd_trigger(rrddb_g, int(gas * 1000), log_g, logsettings);
                        if debug:
                            print(f'Wrote to database {rrddb_g}: {int(gas * 1000)}');
                            if not log_g:
                                print(f'An error occurred, see log file {logsettings[0]}.');
            new_gas_reading = False;
            if counter_rrd > timer_rrd:
                counter_rrd = 0;
            ##########################################################
            # Add the counter totals to the daily log file,if this
            # option has been set in the config file.
            ##########################################################
            if 'daily_logfile' in locals():
                timestamp = get_time(target_timezone);
                if   timestamp[11:16] == "00:00":
                    midnight        = True;
                elif timestamp[11:16] == '00:01':
                    midnight        = False;
                    do_daily_log    = True;         # Reset the trigger to write the daily log
                try:
                    if midnight and do_daily_log:   # Send the data to the log file once per day
                        f=open(daily_logfile, 'a');
                        f.write (timestamp);
                        f.write (delimiter);
                        for log_object in log_object_list:
                            for obis in obis_list:
                                if obis == log_object[1]:
                                    index = obis_list.index(obis);
                                    break;
                            exec(f'rrd_val = ({object_list[index].variable})');
                            f.write (f'{rrd_val:.3f}'); #Always write 3 decimals
                            f.write (delimiter);
                        for log_object in log_object_list:
                            for obis in obis_list:
                                if obis == log_object[1]:
                                    index = obis_list.index(obis);
                                    break;
                            f.write (f"{object_list[index].variable.replace('kwh_total_','').replace('ariff','')}");
                            f.write (delimiter);
                        f.write ('\r\n');
                        f.close();
                        do_daily_log = False;
                except:
                    write_log_entry('a', (f'Error writing {daily_logfile}.', logsettings ));
exit(0)
