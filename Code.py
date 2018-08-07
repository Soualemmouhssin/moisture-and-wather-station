import socket
import network
import time
import machine	
import os
import ujson
import ure

ap = network.WLAN(network.AP_IF)

try :
	f = open("config.txt", "r")
	CONFIG = ujson.loads(f.read())
	f.close() 
except :
	print('error config file note found or of bad format')

CONTENT = b"""\
HTTP/1.0 200 OK

<!doctype html>
<html>
    <head>
        <title>Config system Portal</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta charset="utf8">
    </head>
    <body>
        <h2 class="title">Configure Network Settings</h2>
        <form action="/network">
            Network Name: <input class="input" type="text" name="ssid">
            Password: <input class="input" type="text" name="password">
            <input type="submit" value="Submit">
        </form>
    </body>
</html>
"""

class DNSQuery:
  def __init__(self, data):
    self.data=data
    self.domain=''
    m = data[2] 
    tipo = (m >> 3) & 15   #
    if tipo == 0:                  
      ini=12
      lon=data[ini]
      while lon != 0:
        self.domain+=data[ini+1:ini+lon+1].decode("utf-8") +'.'
        ini+=lon+1
        lon=data[ini] 

  def Request(self, ip):
    packet=b''
    print("Response {} == {}".format(self.domain, ip))
    if self.domain:
      packet+=self.data[:2] + b"\x81\x80"
      packet+=self.data[4:6] + self.data[4:6] + b'\x00\x00\x00\x00'  
      packet+=self.data[12:]                                        
      packet+= b'\xc0\x0c'                                             
      packet+= b'\x00\x01\x00\x01\x00\x00\x00\x3c\x00\x04'             
      packet+=bytes(map(int,ip.split('.')))
    return packet

def Captive():
	if True :
		ip=ap.ifconfig()[0]
		print('DNS Server: dom.query. 60 IN A {:s}'.format(ip))

		udps = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		udps.setblocking(False)
		udps.bind(('',53))
		newconfig = ure.compile("network\?ssid=(.*?)&password=(.*?)\sHTTP")
		# Web Server
		s = socket.socket()
		ai = socket.getaddrinfo(ip, 80)
		print("Web Server: Bind address info:", ai)
		addr = ai[0][-1]

		s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		s.bind(addr)
		s.listen(1)
		s.settimeout(2)
		print("Web Server: Listening http://{}:80/".format(ip))
		
		newconfig = ure.compile("network\?ssid=(.*?)&password=(.*?)\sHTTP")
		try:
			while 1:
				try:
					data, addr = udps.recvfrom(4096)
					p=DNSQuery(data)
					udps.sendto(p.Request(ip), addr)
				except:
					pass
				# Web loop
				try:
					res = s.accept()
					client_sock = res[0]
					client_addr = res[1]
					req = client_sock.recv(4096)
					
					client_sock.send(CONTENT)
					client_sock.close()
					
					search_result = newconfig.search(req)
					if search_result:
						newSSID = search_result.group(1)
						newPASS = search_result.group(2)
						print("new SSID" , newSSID)
						print("new PASS" , newPASS)
						CONFIG['SSID'] = newSSID
						CONFIG['PASS'] = newPASS
						f = open("config.txt", "w")
						ujson.dump(CONFIG,f)
						f.close()
						print (configs) 
						time.sleep (20)
						if connect(CONFIG['SSID'], CONFIG['PASS']):
							print ("ssid and password match")
							ap.active(False)
							return

				except:
					pass
				
				time.sleep_ms(300)
		except KeyboardInterrupt:
			print('Closing')
		udps.close()

def onMessage(topic, msg):
	print("Topic: %s, Message: %s" % (topic, msg))
	relay = machine.Pin(16, machine.Pin.OUT)
	if (str(topic)=="b'threshold'") :
			CONFIG['threshold'] = int(msg) 
			print('new threshold value') 
			print(CONFIG['threshold'])
	if (str(topic)=="b'control'") :
		if (CONFIG['mode'] == 0) :
			if (msg == b"1"):
				relay.value(1)
				print ('turning ON')
			elif msg == b"0":
				print ('turning OFF')
				relay.value(0)
	if (str(topic)=="b'mode'") :
		if msg == b"1":
			CONFIG['mode'] = 1 
			print ('setting automatic mode')
		elif msg == b"0":
			CONFIG['mode'] = 0 
			print ('setting manual mode')
	
def connect(SSID, PASS):
	sta_if = network.WLAN(network.STA_IF)
	sta_if.active(True)
	attempts  =  0 
	sta_if.connect(SSID, PASS)
	if not sta_if.isconnected():
		print('connecting to network...', SSID)
		while attempts < 5 :
			if sta_if.isconnected():
				return True
			attempts =  attempts + 1 
			time.sleep(2)
		print (' not connected')
		sta_if.active(True)
		return False
	return True
	
def main():
	DHT_Sensor = True 
	MQTT_Service = True 	
	if not connect(CONFIG['SSID'], CONFIG['PASS']) :
		print('portal mode') 
		ap.active(True) 
		ap.config(essid="config", password="mypassword", authmode=4) #authmode=1 == no pass
		Captive() 
	if True :
		try :
			d = dht.DHT22(machine.Pin(4))
			DHT_Sensor = True 
		except :
			DHT_Sensor = False 
			print ("sensor not connected")
		try : 
			MQTT_Service = True 
			client = MQTTClient(CONFIG['CLIENT_ID'], CONFIG['MQTT_BROKER'], user=CONFIG['USER'], password=CONFIG['PASSWORD'], port=CONFIG['PORT'])
			client.set_callback(onMessage)
			client.connect()
			client.subscribe(CONFIG['TOPIC'])
			client.subscribe(CONFIG['TOPIC2'])
			client.subscribe(CONFIG['TOPIC3'])
			
		except : 
			print ("reconfigure Your MQTT Server or check  Internet connection") 
			MQTT_Service = False 
		# Attach call back handler to be called on receiving messages

		B= machine.ADC(0)
		sensor = B.read()
		relay = machine.Pin(16, machine.Pin.OUT)
		TOPIC='moisture_value' 
		TOPIC2='temperature_value' 
		TOPIC3='hunidity_value' 
		try:
			while True:
				sensor = B.read()
				if not DHT_Sensor : 
					try :
						d = dht.DHT22(machine.Pin(4))
						DHT_Sensor = True 
					except : 
						pass
				else :
					d.measure()
					print('Temperature value equal : {}'.format(d.temperature()))
					print('Humidity value equal : {}'.format(d.humidity()))
				if MQTT_Service :
					client.check_msg()
					client.publish(TOPIC,str(sensor))
					if DHT_Sensor : 
						client.publish(TOPIC2,str(d.temperature()))
						client.publish(TOPIC3,str(d.humidity()))
					
				print('moisture value equal : {}'.format(sensor))
			
				if (CONFIG['mode']==1) :
					time.sleep(2)
					if(sensor>CONFIG['threshold']):
						print('HIGH moisture value')
						relay.value(0)
					else:
						print('LOW moisture value')
						relay.value(1)
					
		finally:
			if MQTT_Service : 
				client.disconnect()  	
if __name__ == '__main__':
	main()
