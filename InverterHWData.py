#!/usr/bin/python3

import sys
import socket
import binascii
import requests
import libscrc
import os
import configparser

def padhex(s):
    return '0x' + s[2:].zfill(4)

def hex_zfill(intval):
    hexvalue=hex(intval)
    return '0x' + str(hexvalue)[2:].zfill(4)

def send_to_domoticz(device, value, configParser):
    domoticz_url = configParser.get('Domoticz', 'domoticz_url')
    domoticz_username = configParser.get('Domoticz', 'domoticz_username')
    domoticz_password = configParser.get('Domoticz', 'domoticz_password')

    # Prepare authentication payload
    auth_payload = {
        'username': domoticz_username,
        'password': domoticz_password
    }
    # Prepare data payload
    data_payload = {
        'type': 'command',
        'param': 'udevice',
        'idx': configParser.get('Domoticz', device),
        'nvalue': '0',
        'svalue': str(value)
    }
    # Combine authentication payload and data payload
    payload = {**auth_payload, **data_payload}
    # Send data to Domoticz if IDX is not '0'
    if configParser.get('Domoticz', device) != '0':
        print(configParser.get('Domoticz', device))
        response = requests.get(domoticz_url, params=payload)
        # Check if the request was successful
        if response.status_code == 200:
            print('Data sent to Domoticz successfully.')
        else:
            print('Failed to send data to Domoticz.')

# CONFIG
configParser = configparser.RawConfigParser()
configFilePath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.cfg')
configParser.read(configFilePath)

inverter_ip=configParser.get('SofarInverter', 'inverter_ip')
inverter_port=int(configParser.get('SofarInverter', 'inverter_port'))
inverter_sn=int(configParser.get('SofarInverter', 'inverter_sn'))
verbose=configParser.get('SofarInverter', 'verbose')
# END CONFIG
loop = ['0x041A', '0x0420', '0x0480', '0x04BC', '0x0580','0x05B3', '0x680', '0x069B']
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
        if hexpos == "0x041A": 
            value = round(int(str(responsereg), 16) * 1, 1)
            print("Temperatura radiatora 1:", value, "°C")
            send_to_domoticz('temperature_radiator_1_idx', value, configParser)

        if hexpos == "0x0420": 
            value = round(int(str(responsereg), 16) * 1, 1)
            if configParser.get('Domoticz', 'temperature_module_1_idx') != '0':print("Temperatura modułu 1:", value, "°C")
            send_to_domoticz('temperature_module_1_idx', value, configParser)

        if hexpos == "0x0484": 
            value = round(int(str(responsereg), 16) * 0.01, 2)
            print("Częstotliwość sieci:", value, "Hz")
            send_to_domoticz('frequency_idx', value, configParser)

        if hexpos == "0x0485": 
            value = round(int(str(responsereg), 16) * 0.01, 2)
            print("Całkowita moc czynna (dodatnia dla zasilania, ujemna dla zużycia):", value, "kW")
            send_to_domoticz('total_active_power_idx', value*1000, configParser)

        if hexpos == "0x0486": 
            value = round(int(str(responsereg), 16) * 0.01, 2)
            print("Całkowita moc bierząca (dodatnia dla pojemności, ujemna dla indukcyjności):", value, "kVAr")
            send_to_domoticz('total_reactive_power_idx', value*1000, configParser)

        if hexpos == "0x0487": 
            value = round(int(str(responsereg), 16) * 0.01, 2)
            print("Całkowita moc pozorna:", value, "kVA")
            send_to_domoticz('total_apparent_power_idx', value*1000, configParser)

        if hexpos == "0x0488": 
            value = round(int(str(responsereg), 16) * 0.01, 2)
            print("Całkowita moc czynna w PCC (dodatnia dla sprzedaży, ujemna dla zakupu):", value, "kW")
            send_to_domoticz('total_active_power_pcc_idx', value*1000, configParser)

        if hexpos == "0x0489": 
            value = round(int(str(responsereg), 16) * 0.01, 2)
            print("Całkowita moc bierząca w PCC (dodatnia dla pojemności, ujemna dla indukcyjności):", value, "kVAr")
            send_to_domoticz('total_reactive_power_pcc_idx', value*1000, configParser)

        if hexpos == "0x048A": 
            value = round(int(str(responsereg), 16) * 0.01, 2)
            print("Całkowita moc pozorna w PCC:", value, "kVA")
            send_to_domoticz('total_apparent_power_pcc_idx', value*1000, configParser)

        if hexpos == "0x04AF": 
            value = round(int(str(responsereg), 16) * 0.01, 2)
            print("Całkowite obciążenie systemu:", value, "kW")
            send_to_domoticz('total_system_load_idx', value*1000, configParser)

        if hexpos == "0x048D": 
            value = round(int(str(responsereg), 16) * 0.1, 1)
            print("Napięcie sieci - faza R:", value, "V")
            send_to_domoticz('voltage_phase_r_idx', value, configParser)

        if hexpos == "0x048E": 
            value = round(int(str(responsereg), 16) * 0.01, 1)
            print("Prąd wyjściowy - faza R:", value, "A")
            send_to_domoticz('current_phase_r_idx', value, configParser)

        if hexpos == "0x0498": 
            value = round(int(str(responsereg), 16) * 0.1, 1)
            print("Napięcie sieci - faza S:", value, "V")
            send_to_domoticz('voltage_phase_s_idx', value, configParser)

        if hexpos == "0x0499": 
            value = round(int(str(responsereg), 16) * 0.01, 1)
            print("Prąd wyjściowy - faza S:", value, "A")
            send_to_domoticz('current_phase_s_idx', value, configParser)

        if hexpos == "0x04A3": 
            value = round(int(str(responsereg), 16) * 0.1, 1)
            print("Napięcie sieci - faza T:", value, "V")
            send_to_domoticz('voltage_phase_t_idx', value, configParser)

        if hexpos == "0x04A4": 
            value = round(int(str(responsereg), 16) * 0.01, 1)
            print("Prąd wyjściowy - faza T:", value, "A")
            send_to_domoticz('current_phase_t_idx', value, configParser)

        if hexpos == "0x0584": 
            value = round(int(str(responsereg), 16) * 0.1, 1)
            print("Napięcie na stringu PV1:", value, "V")
            send_to_domoticz('voltage_pv1_idx', value, configParser)

        if hexpos == "0x0585": 
            value = round(int(str(responsereg), 16) * 0.01, 1)
            print("Prąd na stringu PV1:", value, "A")
            send_to_domoticz('current_pv1_idx', value, configParser)

        if hexpos == "0x0586": 
            value = round(int(str(responsereg), 16) * 0.01, 1)
            print("Moc na stringu PV1:", value, "kW")
            send_to_domoticz('power_pv1_idx', value*1000, configParser)

        if hexpos == "0x0587": 
            value = round(int(str(responsereg), 16) * 0.1, 1)
            print("Napięcie na stringu PV2:", value, "V")
            send_to_domoticz('voltage_pv2_idx', value, configParser)

        if hexpos == "0x0588": 
            value = round(int(str(responsereg), 16) * 0.01, 1)
            print("Prąd na stringu PV2:", value, "A")
            send_to_domoticz('current_pv2_idx', value, configParser)

        if hexpos == "0x0589": 
            value = round(int(str(responsereg), 16) * 0.01, 1)
            print("Moc na stringu PV2:", value, "kW")
            send_to_domoticz('power_pv2_idx', value*1000, configParser)

        if hexpos == "0x0685": 
            value = round(int(str(responsereg), 16) * 0.01, 1)
            print("Produkcja fotowoltaiczna dzisiaj:", value, "kW")
            send_to_domoticz('production_idx', value*1000, configParser)

        if hexpos == "0x0687": 
            value = round(int(str(responsereg), 16) * 0.1, 1)
            print("Całkowita produkcja fotowoltaiczna:", value, "kW")
            send_to_domoticz('total_production_idx', value*1000, configParser)
        a+=1