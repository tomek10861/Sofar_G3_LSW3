# SOFAR Inverter G3 + LSW-3/LSE
Small utility to read data from SOFAR K-TLX G3 inverters through the Solarman (LSW-3/LSE) datalogger. 

*Thanks to @jlopez77 https://github.com/jlopez77 for logger/MODBUS protocol code.*
*Thanks to @MichaluxPL https://github.com/MichaluxPL

# Required python modules
To run, script requires following python modules:
```
libscrc
paho-mqtt
influxdb
```

# Configuration

Edit the config.cfg and enter the following data:
```
[SofarInverter]
inverter_ip=X.X.X.X             # data logger IP
inverter_port=8899              # data logger port
inverter_sn=XXXXXXXXXX          # data logger S/N
verbose=0                       # Set to 1 for additional info to be presented (registers, binary packets etc.)
