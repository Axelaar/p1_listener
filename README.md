<h1>p1_listener</h1>
Smart meters in compliance with DSMR or ESMR standards are fitted with a P1-port.  Using a serial converter cable this port can be used to listen to the broadcasts initiated by the meter.  The data can then be processed by (in this case) Python for further handling.  The Python script in this repository is currently set up to forward specific data as an IP-telegram and/or a WebSocket message, and can write to a file or a database using RRD-tool.
<h1>Requirements</h1>
<ul>
  <li>Raspberry Pi<br>
  Any Raspberry Pi should do, I used models zero, 2B, 3B and 4.</li>
  <li>Connector cable P1 – USB (I used the P1 Converter Cable v2 from http://www.smartmeterdashboard.nl/webshop)</li>
  <li>Python3 with modules as described below</li>
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
  <li>Add the library to read the serial port using Python:</li>
  <pre><code>sudo apt install python3-serial</code></pre>
</ul>
<h4>Install PIP (if necessary)</h4>
If you installed Raspberry Pi OS Lite then it lacks the pip tool.  Install it now:
<pre><code>sudo apt install python3-pip -y</code></pre>
<h4>Install the python timezone library</h4>
<pre><code>pip3 install pytz</code></pre>
<h4>Install and configure the round robin database</h4>
This section will be added later.
<h4>Install Apache Web Server, Websockets (Autobahn, Twisted)</h4>
This section will be added later.
