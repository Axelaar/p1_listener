<h1>p1_listener</h1>
Smart meters in compliance with DSMR or ESMR standards are fitted with a P1-port.  Using a serial converter cable this port can be used to listen to the broadcasts initiated by the meter.  The data can then be processed by (in this case) Python for further handling.  The Python script in this repository is currently set up to forward specific data as an IP-telegram and/or a WebSocket message, and can write to a file or a database using RRD-tool.
<h1>Requirements</h1>
<ul>
  <li>Raspberry Pi<br>
  Any Raspberry Pi should do, I used models zero, 2B, 3B and 4.</li>
  <li>Connector cable P1 – USB (I used the P1 Converter Cable v2 from http://www.smartmeterdashboard.nl/webshop)</li>
  <li>Python3.5+ with modules as described below</li>
</ul>
<h1>Setting up the Raspberry Pi</h1>
<h4>Make sure the latest updates are installed:</h4>
<pre><code>sudo apt update
sudo apt full-upgrade -y
sudo apt clean
sudo reboot</code></pre>
<h4>Set timezone to UTC</h4>
Set the timezone  to UTC to avoid missing data or gaps in data when changing to or from Daylight Saving time.
<pre><code>sudo raspi-config</code></pre><ul>
  <li>Select ‘Localisation Options’<br>
    (use the up/down cursor to select a row, then the right cursor to highlight ‘select’, then press &ltenter&gt)<br>
    Select ‘Timezone’<br>
    Select ‘None of the above’<br>
    Select ‘UTC’<br>
    Exit with ‘OK’ and ‘Finish’.</li>
</ul>
<h4>Create directories for organizing files</h4>
The directory <i>graphs</i> is used with RRDtool, <i>websocketdata</i> is only used when WebSockets are used.
<pre><code>mkdir {dsmr, graphs, local_lib, logs, websocketdata}</code></pre>
<h4>Configure for Smart Meter data reception</h4>
<ul>
  <li>Install the serial tool ‘cu minicom’:</li>
  <pre><code>sudo apt install cu minicom -y</code></pre>
  <li>Verify that the communication is successful:</li>
  <ul>
    <li>For meters up to and including version 3:</li>
    <pre><code>cu -l /dev/ttyUSB0 -s 9600 --parity=even</code></pre>
    <li>For meter versions 4 and 5:</li>
    <pre><code>cu -l /dev/ttyUSB0 -s 115200 --parity=none</code></pre>
  </ul>
  <li>To exit type:  &ltenter&gt~.<br>
  (so: the enter key, then the tilde followed by the dot)<br>
  Note: there is a slight delay in disconnecting after hitting this key combination.</li>
  <li>The result should be a repeating series of data sets similar to this:
<pre><code>/XMX5LGBBLA4402915485

1-3:0.2.8(50)
0-0:1.0.0(200310123610W)
0-0:96.1.1(4530303435303034303436393339353137)
1-0:1.8.1(001164.722*kWh)
1-0:1.8.2(000965.026*kWh)
1-0:2.8.1(000252.398*kWh)
1-0:2.8.2(000589.121*kWh)
0-0:96.14.0(0002)
1-0:1.7.0(00.087*kW)
1-0:2.7.0(00.000*kW)
0-0:96.7.21(00002)
0-0:96.7.9(00000)
1-0:99.97.0(0)(0-0:96.7.19)
1-0:32.32.0(00001)
1-0:32.36.0(00000)
0-0:96.13.0()
1-0:32.7.0(231.0*V)
1-0:31.7.0(000*A)
1-0:21.7.0(00.087*kW)
1-0:22.7.0(00.000*kW)
0-1:24.1.0(003)
0-1:96.1.0(4730303332353635353438333236323137)
0-1:24.2.1(200310123504W)(01621.615*m3)
!750D</code></pre></li>

  <li>Add the library to read the serial port using Python:</li>
  <pre><code>sudo apt install python3-serial</code></pre>
</ul>
<h4>Install PIP (if necessary)</h4>
If you installed Raspberry Pi OS Lite then it lacks the pip tool.  Install it now:
<pre><code>sudo apt install python3-pip -y</code></pre>
<h4>Install the python timezone library</h4>
<pre><code>pip3 install pytz</code></pre>
<h4>Optional: Install and configure the round robin database</h4>
This section will be added later.
<h4>Optional: Install Apache Web Server, Websockets (Autobahn, Twisted)</h4>
This section will be added later.
<h4>Set up a symlink to enable testing of the library modules</h4>
When testing a ‘local_lib’ library module from another directory, the module under certain circumstances requires a symlink to point to the correct folder location.  Set up this symlink:
<pre><code>ln -s /home/pi/local_lib/ /home/pi/local_lib/</code></pre>
<h1>Create the helper files</h1>
The p1_listener script relies on a telegram definition file.  This file can be created in two steps, using two scripts:
<ul>
  <li>Script p1_telegram_discovery.py tries to read the USB0 serial port and capture a single telegram.
    This telegram is written to a file: /home/pi/dsmr/standard_telegram.txt.</li>
  <li>Script dsmr_definition.py is used to generate the defition of each line of the telegram, so that
      the p1_listener script 'knows' where to find the information of each OBIS (= Object Identification System) code.
      Comment out or uncomment the object_list lines in the this script so that only the lines with the OBIS codes that
    are needed by the p1-listener script will be handled.</li> 
 </ul>
<h1>Install the local library files</h1>
p1_listener uses local libraries that can also be used by other scripts.  These library files are expected to be in directory /home/pi/local_lib/.  Library file  'custom_functions.py' contains required libraries.  Depending on which output methods are used, one or more of the following library files are needed:
<ul>
  <li>IP_transmit.py</li>
  <li>update_rrd.py</li>
  <li>ws_transmit.py</li>
</ul>
