Smart meters in compliance with DSMR or ESMR standards are fitted with a P1-port.  Using a serial converter cable this port can be used to listen to the broadcasts made by the meter.  The data can then be processed by (in this case) Python for further handling.  The Python script in this repository is currently set up to forward specific data as an IP-telegram and/or a WebSocket message, and can write to a file or a database using RRD-tool.

<i>Documentation is being created, but not published yet.  Look in the development branch of this repository to see the current status.</i>
