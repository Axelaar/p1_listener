rrdtool create /home/pi/data/gas.rrd --step 3600   \
DS:Gas:COUNTER:10000:0:100000000   \
RRA:MIN:0.5:6:1460            \
RRA:MIN:0.5:24:3650            \
RRA:MIN:0.5:168:1300            \
RRA:AVERAGE:0.5:1:744            \
RRA:AVERAGE:0.5:6:1460            \
RRA:AVERAGE:0.5:24:3650            \
RRA:AVERAGE:0.5:168:1300            \
RRA:MAX:0.5:6:1460            \
RRA:MAX:0.5:24:3650            \
RRA:MAX:0.5:168:1300           
