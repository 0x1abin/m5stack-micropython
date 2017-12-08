import network,socket,ure,time,json,gc,machine,ubinascii,m5

wlan_ap = network.WLAN(network.AP_IF)
wlan_sta = network.WLAN(network.STA_IF)

# setup for ssid 
node_id = ubinascii.hexlify(machine.unique_id())
ssid_name= b"M5Stack-"+node_id[-6:]
ssid_password = ""
scanlist = []
text_h = 0

server_socket = None

def do_connect(ntwrk_ssid, netwrk_pass):
	sta_if = network.WLAN(network.STA_IF)
	sta_if.active(True)
	if not sta_if.isconnected():
		print('try to connect : SSID:'+ntwrk_ssid+' PASSWD:'+netwrk_pass+' network...')
		m5.print('try to connect: \r\nSSID:'+ntwrk_ssid+' \t\nPASSWD:'+netwrk_pass, 0, 16)
		sta_if.active(True)
		sta_if.connect(ntwrk_ssid, netwrk_pass)
		a=0
		while not sta_if.isconnected() | (a > 99) :
			time.sleep(0.1)
			a+=1
			print('.', end='')
		if sta_if.isconnected():
			print('\nConnected. Network config:', sta_if.ifconfig())
			m5.print("Connected. \r\nNetwork config:\r\n"+sta_if.ifconfig()[0]+', '+sta_if.ifconfig()[3], 0, 16*4)
			return (True)
		else : 
			print('\nProblem. Not Connected to :'+ntwrk_ssid)
			m5.print('Problem. Not Connected to :'+ntwrk_ssid, 0, 16*4)
			return (False)

def send_response(client, payload, status_code=200):
	client.sendall("HTTP/1.0 {} OK\r\n".format(status_code))
	client.sendall("Content-Type: text/html\r\n")
	client.sendall("Content-Length: {}\r\n".format(len(payload)))
	client.sendall("\r\n")
	
	if len(payload) > 0:
		client.sendall(payload)

def handle_root(client):
	global wlan_sta
	response_header = """
		<html><meta name="viewport" content="width=device-width,height=device-height,initial-scale=1,minimum-scale=1,maximum-scale=1,user-scalable=no">
		<style>p{margin:10px 0}h1,h2{text-align:center;margin:35px 0}h2{margin:20px 0!important}form{margin-top:30px}tr td{text-align:right}tr select,tr input{width:200px;height:30px;padding-left:10px;outline:0;border-radius:3px;border:1px solid lightgrey}input[type=submit]{width:300px;height:38px;color:#fff;background-color:#2196F1;border:none;font-size:20px;border-radius:3px;margin-top:20px}</style>
		<h1><img src="data:image/png;base64,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" alt=""></h1>
		<h2 style="color:#333"><p style="font-weight:100;font-size:32px">WiFi Setup</p></h2>
		<form action="configure" method="post">
		<table style="margin-left:auto;margin-right:auto">
		<tbody><tr><td>SSID:</td><td style="text-align:center"><select id="ssid" name="ssid">
	"""

	wlan_sta.active(True)

	response_variable = ""
	# for ssid, *_ in wlan_sta.scan():
	for ssid, *_ in scanlist:
		response_variable += '<option value="{0}">{0}</option>'.format(ssid.decode("utf-8"))
	
	response_footer = """
		</select></td></tr>
		<tr><td>Password:</td>
		<td><input name="password" type="password"></td></tr></tbody>
		</table>
		<p style="text-align:center"><input type="submit" value="Configure"></p>
		</form>
		</html>
	"""

	client.sendall("HTTP/1.0 {} OK\r\n".format(200))
	client.sendall("Content-Type: text/html\r\n")
	client.sendall("Content-Length: {}\r\n".format(len(response_header)+len(response_variable)+len(response_footer) ))
	client.sendall("\r\n")

	client.sendall(response_header)
	client.sendall(response_variable)
	client.sendall(response_footer)

	# send_response(client, response_header + response_variable + response_footer)
	gc.collect()

def handle_configure(client, request):
	match = ure.search("ssid=([^&]*)&password=(.*)", request)

	if match is None:
		send_response(client, "Parameters not found", status_code=400)
		return (False)
	# version 1.9 compatibility
	try:
		ssid = match.group(1).decode("utf-8").replace("%3F","?").replace("%21","!")
		password = match.group(2).decode("utf-8").replace("%3F","?").replace("%21","!")
	except:
		ssid = match.group(1).replace("%3F","?").replace("%21","!")
		password = match.group(2).replace("%3F","?").replace("%21","!")
	
	
	if len(ssid) == 0:
		send_response(client, "SSID must be provided", status_code=400)
		return (False)

	if do_connect(ssid, password):
		response_footer = """
		<html>
		<center><br><br>
		<h1 style="color: #5e9ca0; text-align: center;"><span style="color: #000000;">:) YES, WiFi Successed Connected """+ssid+"""</span></h1>
		<br><br>"""
		send_response(client, response_footer)
		try:
			wifidata = {}
			wifidata['ssid'] = ssid
			wifidata['password'] = password

			fo = open("config.json","r")
			cfg = fo.read()
			fo.close()

			fo = open("config.json","w")
			cfg = json.loads(cfg)
			cfg['wifi'] = wifidata
			fo.write(json.dumps(cfg))
			fo.close()
		except:
			fo = open("config.json","w")
			cfg = {}
			cfg['wifi'] = wifidata
			fo.write(json.dumps(cfg))
			fo.close()

		return (True)
	else:
		response_footer = """
		<html>
		<center>
		<h1 style="color: #5e9ca0; text-align: center;"><span style="color: #000000;">Wi-Fi Not Configured to """+ssid+"""</span></h1>
		<br><br>
		<form>
			<input type="button" value="Go back!" onclick="history.back()"></input>
		</form></center></html>
		"""
		send_response(client, response_footer )
		return (False)

def handle_not_found(client, url):
	send_response(client, "Path not found: {}".format(url), status_code=404)

def stop():
	global server_socket

	if server_socket:
		server_socket.close()

def webstart(port=80):
	addr = socket.getaddrinfo('0.0.0.0', port)[0][-1]

	global server_socket
	global wlan_sta
	global wlan_ap
	global ssid_name
	global ssid_password
	stop()
	
	wlan_sta.active(True)
	wlan_ap.active(True)
	
	# wlan_ap.config(essid=ssid_name,password=ssid_password)
	wlan_ap.config(essid=ssid_name)
	global scanlist
	scanlist = wlan_sta.scan()
	
	server_socket = socket.socket()
	server_socket.bind(addr)
	server_socket.listen(1)
	
	# print('Connect to Wifi ssid :'+ssid_name+' , Default pass: '+ssid_password)
	print(b'Connect to Wifi ssid:'+ssid_name)
	print('And connect to esp via your web browser (like 192.168.4.1)')
	print('listening on', addr)
	m5.print(b'Connect to Wifi ssid:'+ssid_name, 0, 16*6)
	m5.print('via your web browser: 192.168.4.1', 0, 16*7)
	m5.print('listening on'+str(addr), 0, 16*7)
	
	while True:
		
		if wlan_sta.isconnected():
			client.close
			return (True)
		
		gc.collect()
		client, addr = server_socket.accept()
		client.settimeout(5.0)
		
		print('client connected from', addr)

		request = b""
		try:
			while not "\r\n\r\n" in request:
				request += client.recv(512)
		except OSError:
			print('client.recv OSError!')
			pass
        
		# print("Request is: {}".format(request))
		print("Request is:")
		print(request)
		if "HTTP" not in request:
			# skip invalid requests
			client.close()
			continue
		
		# version 1.9 compatibility
		try:
			url = ure.search("(?:GET|POST) /(.*?)(?:\\?.*?)? HTTP", request).group(1).decode("utf-8").rstrip("/")
		except:
			url = ure.search("(?:GET|POST) /(.*?)(?:\\?.*?)? HTTP", request).group(1).rstrip("/")
		print("URL is {}".format(url))

		if url == "":
			handle_root(client)
		elif url == "configure":
			handle_configure(client, request)
		else:
			handle_not_found(client, url)
  
		client.close()


def check_connection():			
	global wlan_sta
	# Firstly check is there any connection 
	if wlan_sta.isconnected():
		return (True)
	try:
		# connection of ESP to WiFi takes time 
		# wait 3 sec. and try again. 
		time.sleep(1)
		if not wlan_sta.isconnected():
			try:
				f = open("config.json")
				jdata = json.loads(f.read())
				ssid = jdata['wifi']['ssid']
				passwd = jdata['wifi']['password']
				f.close()
			except:
				print('config.json file parser fail!')
			else:
				if do_connect(ssid, passwd):
					return (True)

			if not wlan_sta.isconnected():
				wlan_sta.disconnect()
				if webstart():
					return (True)
		else:
			return (True)
		
	except OSError:
		# Web server for connection manager
		if webstart():
			return (True)
	
	return (False)
	

def start():
	if check_connection():
		# Main Code is here
		global wlan_ap
		wlan_ap.active(False)
		print("ESP WiFi connected OK")
		m5.print("ESP WiFi connected OK",0, 16*10)
		# to import your code;
		# import sample_mqtt.py
	else:
		print ("There is something wrong")

start()
gc.collect()