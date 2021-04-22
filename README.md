<h1>p1_listener</h1>
Smart meters in compliance with DSMR or ESMR standards are fitted with a P1-port.  Using a serial converter cable this port can be used to listen to the broadcasts made by the meter.  The data can then be processed by (in this case) Python for further handling.  The Python script in this repository is currently set up to forward specific data as an IP-telegram and/or a WebSocket message, and can write to a file or a databese using RRD-tool.
<h1>Requirements</h1>
<ul>
  <li>Raspberry Pi<br>
  Any Raspberry Pi should do, I used models zero, 2B, 3B and 4.</li>
  <li>Connector cable P1 – USB (I used the P1 Converter Cable v2 from http://www.smartmeterdashboard.nl/webshop)</li>
  <li>Python3 with modules as described below</li>
</ul>
<h1>Setting up the Raspberry Pi</h1>
<h4>Make sure the latest updates are installed:</h4>
<ul>
  <li>sudo apt update
  <li>sudo apt full-upgrade -y
  <li>sudo apt clean
  <li>sudo reboot
</ul>
<h4>Set timezone to UTC</h4>
Set the timezone  to UTC to avoid missing data or gaps in data when changing from or to Daylight Saving time.
<ul>
  <li>sudo raspi-config<br>
    Select ‘Localisation Options’<br>
    (use the up/down cursor to select a row, then the right cursor to highlight ‘select’, then press <enter>)<br>
    Select ‘Timezone’<br>
    Select ‘None of the above’<br>
    Select ‘UTC’<br>
    Exit with ‘OK’ and ‘Finish’ <b>or</b> jump to the next chapter and continue with the configuration tool.</li>
</ul>
