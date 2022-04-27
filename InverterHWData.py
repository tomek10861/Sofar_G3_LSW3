#!/usr/bin/python3

import sys
import socket
import binascii
import re
import libscrc
import json
import os
import configparser

def padhex(s):
    return '0x' + s[2:].zfill(4)

def hex_zfill(intval):
    hexvalue=hex(intval)
    return '0x' + str(hexvalue)[2:].zfill(4)

os.chdir(os.path.dirname(sys.argv[0]))

# CONFIG
configParser = configparser.RawConfigParser()
configFilePath = r'./config.cfg'
configParser.read(configFilePath)

inverter_ip=configParser.get('SofarInverter', 'inverter_ip')
inverter_port=int(configParser.get('SofarInverter', 'inverter_port'))
inverter_sn=int(configParser.get('SofarInverter', 'inverter_sn'))
verbose=configParser.get('SofarInverter', 'verbose')
# END CONFIG
loop = ['0x0480', '0x04BC', '0x0580','0x05B3']
while loop:
    
    pfin=int(loop.pop(-1),0)
    pini=int(loop.pop(-1),0)
    # Data logger frame begin
    start = binascii.unhexlify('A5') # Logger Start code
    length=binascii.unhexlify('1700') # Logger frame DataLength
    controlcode= binascii.unhexlify('1045') # Logger ControlCode
    serial=binascii.unhexlify('0000') # Serial
    datafield = binascii.unhexlify('020000000000000000000000000000') # com.igen.localmode.dy.instruction.send.SendDataField
    # Modbus request begin
    pos_ini=str(hex_zfill(pini)[2:])
    pos_fin=str(hex_zfill(pfin-pini+1)[2:])
    businessfield= binascii.unhexlify('0003' + pos_ini + pos_fin) # Modbus data to count crc
    if verbose=="1": print('Modbus request: 0103 ' + pos_ini + " " + pos_fin +" "+str(padhex(hex(libscrc.modbus(businessfield)))[4:6])+str(padhex(hex(libscrc.modbus(businessfield)))[2:4]))
    crc=binascii.unhexlify(str(padhex(hex(libscrc.modbus(businessfield)))[4:6])+str(padhex(hex(libscrc.modbus(businessfield)))[2:4])) # CRC16modbus
    # Modbus request end
    checksum=binascii.unhexlify('00') #checksum F2
    endCode = binascii.unhexlify('15')# Logger End code
    inverter_sn2 = bytearray.fromhex(hex(inverter_sn)[8:10] + hex(inverter_sn)[6:8] + hex(inverter_sn)[4:6] + hex(inverter_sn)[2:4])
    frame = bytearray(start + length + controlcode + serial + inverter_sn2 + datafield + businessfield + crc + checksum + endCode)
    if verbose=="1":
        print("Hex string to send: A5 1700 1045 0000 " + hex(inverter_sn)[8:10] + hex(inverter_sn)[6:8] + hex(inverter_sn)[4:6] + hex(inverter_sn)[2:4] + " 020000000000000000000000000000 " + "0104" + pos_ini + pos_fin + str(hex(libscrc.modbus(businessfield))[3:5]) + str(hex(libscrc.modbus(businessfield))[2:3].zfill(2)) + " 00 15")
    if verbose=="1": print("Data sent: ", frame);
    # Data logger frame end

    checksum = 0
    frame_bytes = bytearray(frame)
    for i in range(1, len(frame_bytes) - 2, 1):
        checksum += frame_bytes[i] & 255
    frame_bytes[len(frame_bytes) - 2] = int((checksum & 255))

    # OPEN SOCKET
    for res in socket.getaddrinfo(inverter_ip, inverter_port, socket.AF_INET, socket.SOCK_STREAM):
                     family, socktype, proto, canonname, sockadress = res
                     try:
                      clientSocket= socket.socket(family,socktype,proto);
                      clientSocket.settimeout(15);
                      clientSocket.connect(sockadress);
                     except socket.error as msg:
                      print("Could not open socket - inverter/logger turned off");
                      if prometheus=="1": prometheus_file.close();
                      sys.exit(1)

    # SEND DATA
    clientSocket.sendall(frame_bytes);

    ok=False;
    while (not ok):
     try:
      data = clientSocket.recv(1024);
      ok=True
      try:
       data
      except:
       print("No data - Exit")
       sys.exit(1) #Exit, no data
     except socket.timeout as msg:
      print("Connection timeout - inverter and/or gateway is off");
      sys.exit(1) #Exit

    # PARSE RESPONSE (start position 56, end position 60)
    if verbose=="1": print("Data received: ", data);
    i=pfin-pini # Number of registers
    a=0 # Loop counter
    response=str(''.join(hex(ord(chr(x)))[2:].zfill(2) for x in bytearray(data))) #+'  '+re.sub('[^\x20-\x7f]', '', '')));
    if verbose=="1":
        hexstr=str(' '.join(hex(ord(chr(x)))[2:].zfill(2) for x in bytearray(data)))
        print("Hex string received:",hexstr.upper())
    while a<=i:
     p1=56+(a*4)
     p2=60+(a*4)
     responsereg=response[p1:p2]
     # print(p1, p2, responsereg)
     hexpos=str("0x") + str(hex(a+pini)[2:].zfill(4)).upper()
     if verbose=="1": print("Register:",hexpos+" , value: hex:" +str(responsereg) + "dev:"+str(int(str(responsereg),16)*0.01));
     if(str(hexpos) == "0x048D"): print("R:"+str(int(str(responsereg),16)*0.1) + "V")
     if(str(hexpos) == "0x048E"): print("R:"+str(int(str(responsereg),16)*0.01) + "A")
     if(str(hexpos) == "0x0498"): print("S:"+str(int(str(responsereg),16)*0.1) + "V")
     if(str(hexpos) == "0x0499"): print("S:"+str(int(str(responsereg),16)*0.01) + "A")
     if(str(hexpos) == "0x04A3"): print("T:"+str(int(str(responsereg),16)*0.1) + "V")
     if(str(hexpos) == "0x04A4"): print("T:"+str(int(str(responsereg),16)*0.01) + "A")
     if(str(hexpos) == "0x0584"): print("P1:"+str(int(str(responsereg),16)*0.1) + "V")
     if(str(hexpos) == "0x0585"): print("P1:"+str(int(str(responsereg),16)*0.01) + "A")
     if(str(hexpos) == "0x0586"): print("P1:"+str(int(str(responsereg),16)*0.01) + "kW")
     a+=1