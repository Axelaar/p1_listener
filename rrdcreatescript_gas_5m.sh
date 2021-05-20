rrdtool create /home/pi/data/gas.rrd --step 300   \
DS:Gas:COUNTER:600:0:100000000   \
RRA:MIN:0.5:12:8640            \
RRA:MIN:0.5:72:14600            \
RRA:MIN:0.5:288:9125            \
RRA:AVERAGE:0.5:1:288            \
RRA:AVERAGE:0.5:12:8640            \
RRA:AVERAGE:0.5:72:14600            \
RRA:AVERAGE:0.5:288:9125            \
RRA:MAX:0.5:12:8640            \
RRA:MAX:0.5:72:14600            \
RRA:MAX:0.5:288:9125
