# Python3 module to be called from other scripts.
# This script contains the custom function to write
# to an existing RRD database.
# Created November 3, 2020 by Bram Langen.
# Version 1.3 - Added the list check.

from rrdtool                        import update as rrd_update;
from local_lib.custom_functions     import write_log_entry;

############################################################
# Write data to the specified round-robin-database.
# The 'data' argument received MUST be a tuple, even 
# if the database only requires a single argument.
# A tuple with 1 value can be written as (x,).
############################################################
def rrd_trigger(db, data, write_log, logsetting):
    'Update the specified rrd database'
    if type(data) != tuple:
        argument_count = 1;
    else:
        argument_count  = len(data);
    update_prefix   = 'N' + ':%s' * argument_count;
    try:
        ret = rrd_update(db, update_prefix % data);             # write value(s) to the database
        write_log = True;
    except:
        if write_log:
            write_log_entry('a', ('Fout bij het schrijven naar database %s. ' % db ), logsetting);
            write_log = False;
    return write_log;
