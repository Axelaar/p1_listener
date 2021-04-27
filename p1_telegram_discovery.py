#!/usr/bin/python3
#
# Use the USB0 port to trap a single telegram, and
# write the relevant portion to a file.
# Created by Bram Langen - Apr 26, 2021
# version 1.0

from    pathlib import Path;
import  serial;
import  sys;
from    time    import sleep;

############################################################
# Verify python version to be 3.5 or higher
############################################################
if not sys.version_info >= (3, 5):
    sys.exit ('Incompatible python version ({0}.{1}), must be >= 3.5 \
        '.format(sys.version_info[0], sys.version_info[1]));

############################################################
# Initialize variables
############################################################
dsmr_path           = '/home/pi/dsmr';
line_count          = 0;
output_file         = dsmr_path + '/standard_telegram.txt';
port_timeout        = 20;
port_name           = '/dev/ttyUSB0';
opening_line_found  = False;
use_config          = None;

############################################################
# Tell the user what the script will do
############################################################
print('     \r\nThis script captures a single telegram from the p1 port');
print('     of a smart meter complying with DSMR or ESMR standards.\r\n');
print("     If it does not exist, directory 'dsmr' will be created");
print('     in the pi home directory.\r\n');
print("     The content of the telegram will be written to '{0}'.".format(output_file));
print('     The p1 converter cable is expected to use port {0}.'.format(port_name));
print('');
answer = input('Press the enter key to continue, or any key + enter to quit: ');
if answer != '':
    sys.exit ('\r\nScript terminated.');
    
############################################################
# Set COM port configs
# ser1 is for smart meters up to version 3
# ser2 is for smart meters versions 4 and 5
############################################################
ser1          = serial.Serial();
ser1.baudrate = 9600;
ser1.bytesize = serial.SEVENBITS;
ser1.parity   = serial.PARITY_EVEN;
ser1.stopbits = serial.STOPBITS_ONE;
ser1.xonxoff  = 1;
ser1.rtscts   = 0;
ser1.timeout  = port_timeout;
ser1.port     = port_name;

ser2          = serial.Serial();
ser2.baudrate = 115200;
ser2.bytesize = serial.EIGHTBITS;
ser2.parity   = serial.PARITY_NONE;
ser2.stopbits = serial.STOPBITS_ONE;
ser2.xonxoff  = 1;
ser2.rtscts   = 0;
ser2.timeout  = port_timeout;
ser2.port     = port_name;

############################################################
# Open COM port, test for latest meter configuration first
# If no telegram is received then switch to the 
# configuration for the older meters.
# Two 'no data' receipts are required to decide that
# the serial configuration returns no data.
############################################################
print('Port timeout has been set at {0} seconds, testing ports may take a minute'.format(port_timeout));
for ser in (ser2, ser1):
    blank_line_counter  = 0;
    try:
        ser.open();
    except:
        sys.exit('Error opening port {0}, script halted.'.format(ser.name));
    print('Flushing buffers of port {0}'.format(ser.name));
    ser.flushInput();
    ser.flushOutput();
    sleep(1);      # Some time is needed to actually flush the port.
    print('Reading port {0} using baudrate {1}'.format(ser.name, ser.baudrate));
    while True:
        # Print every line received to the console
        try:
            p1_raw  = ser.readline();
            p1_line = bytes.decode(p1_raw, errors='ignore').strip();
            if p1_line[0:1] == '!':
                # A line starting with the exclamation mark is the
                # final line of the telegram.  If this line is
                # received then the port configuration is valid
                # and selected for use when creating the telegram file.
                print(p1_line);
                use_config = ser;
                break;
            elif p1_line == '':
                blank_line_counter +=1;
                print('(No data)');
                if blank_line_counter > 1:
                    break;
            else:
                print(p1_line);
                blank_line_counter = 0;
        except:
            sys.exit ('Error reading port {0}, script halted.'.format(ser1.name));
    ser.close();
    if use_config != None:
        break;
if use_config == None:
    print('\r\nNo matching port configuration found, no reference file created.\r\n');
else:
    ##########################################################
    # Create the directory if it does not yet exist.
    # Open the outputfile.
    # Read the serial port and start processing once the 
    # opening line has been received.
    # Write each line with an OBIS code to the file.
    ##########################################################
    Path(dsmr_path).mkdir(parents = True, exist_ok = True);
    ser = use_config;
    ser.open();
    ser.flushInput();
    ser.flushOutput();
    sleep(1);
    f = open(output_file, 'w+');
    print('\r\nWriting one complete telegram to file {0}'.format(output_file));
    print('Waiting for the next telegram to arrive...');
    while True:
        p1_raw  = ser.readline();
        p1_line = bytes.decode(p1_raw, errors='ignore').strip();
        if p1_line[0:1] == '/':
            opening_line_found = True;
        if opening_line_found:
            # Skip the first two lines of the telegram, they have no relevance.
            if not p1_line == '' and not p1_line[0:1] == '/':
                f.write(p1_line + '\r\n');
                line_count += 1;
                if p1_line[0:1] == '!':
                    break;
    f.close();
    ser.close();
    print('\r\nDone!  \r\nWrote {0} lines to file {1}.\r\n'.format(line_count, output_file));
exit();
