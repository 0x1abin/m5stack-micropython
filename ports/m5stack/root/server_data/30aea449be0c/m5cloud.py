#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os, machine, ubinascii, ujson, m5
import network, _thread, time, umqtt, uerrno

node_id = ubinascii.hexlify(machine.unique_id())
mqttc = umqtt.MQTTClient(b'M5Core-'+node_id, "mqtt.m5stack.com")
repl_enable = False

topic_out = b'/M5Cloud/'+node_id+'/out'
topic_in  = b'/M5Cloud/'+node_id+'/in'
topic_repl_out = b'/M5Cloud/'+node_id+'/repl/out'
topic_repl_in  = b'/M5Cloud/'+node_id+'/repl/in'
print('topic_out:'+str(topic_out))
print('topic_in:'+str(topic_in))
print('topic_repl_out:'+str(topic_repl_out))
print('topic_repl_in:'+str(topic_repl_in))


def load_config(config):
  try:
    f = open(config)
  except:
    print("open config fail!")
  else:
    c = ujson.loads(f.read())
    ssid = c.get('wifi-ssid')
    password = c.get('wifi-password')
    f.close()


def connect_wifi():
  print("Connecting WiFi..\r\n")
  sta_if = network.WLAN(network.STA_IF); sta_if.active(True);
  # sta_if.scan()                             # Scan for available access points
  sta_if.connect("MasterHax_2.4G", "wittyercheese551") # Connect to an AP
  # sta_if.connect("LabNet", "mytradio") # Connect to an AP
  while (sta_if.isconnected() != True):                      # Check for successful connection
    time.sleep_ms(100)
  print("Connected WiFi\r\n")


def list_file_tree(path = ''):
  try:
      l = os.listdir(path)
  except:
      return path
  else:
      path_list = []
      for i in l:
          path_list.append(list_file_tree(path+'/'+i))
      return path_list


def makedirs_write_file(path, file):
  path_list = path.rstrip('/').split('/')[:-1]
  _path = ''
  if path_list[0] == '':
    _path = '/'
  for i in path_list:
    try:
      _path += '/'+ i
      os.mkdir(_path)
    except:
      pass

  print('(M5Cloud) write file:%s' % (path))
  f = open(path, 'wb')
  f.write(file)
  f.close()
  return_data = {'type':'REP_WRITE_FILE', 'path': path, 'data':''}
  resp_buf = {'status':200, 'data':return_data, 'msg':''}
  mqttc.publish(topic_out, ujson.dumps(resp_buf))


# Received messages from subscriptions will be delivered to this callback
def mqtt_sub_cb(topic, msg):
  # print((topic, msg))
  if topic == topic_in :
      jsondata = ujson.loads(msg)
      cmd = jsondata.get('cmd')
      if cmd == 'CMD_LISTDIR':
        try:
          path = jsondata.get('path')
          liststr = list_file_tree(path)
        except OSError: 
          resp_buf = {'status':405, 'data':'', 'msg':path}
          mqttc.publish(topic_out, ujson.dumps(resp_buf))
        else:
          return_data = {'type':'REP_LISTDIR', 'path': path, 'data': liststr}
          resp_buf = {'status':200, 'data':return_data, 'msg':''}
          mqttc.publish(topic_out, ujson.dumps(resp_buf))

      elif cmd == 'CMD_READ_FILE':
        try:
          path = jsondata.get('path')
          f = open(path, 'rb')
        except OSError: 
          resp_buf = {'status':404, 'data':'', 'msg':path}
          mqttc.publish(topic_out, ujson.dumps(resp_buf))
        else:
          print('(M5Cloud) read file:%s' % path)
          return_data = {'type':'REP_READ_FILE', 'path':path, 'data':f.read()}
          resp_buf = {'status':200, 'data':return_data, 'msg':''}
          mqttc.publish(topic_out, ujson.dumps(resp_buf))
        f.close()

      elif cmd == 'CMD_WRITE_FILE':
        makedirs_write_file(jsondata.get('path'), jsondata.get('data'))

      elif cmd == 'CMD_REPL_SET':
        global repl_enable
        repl_enable = jsondata.get('value')
        print('repl_enable:%d' % (repl_enable))

      elif cmd == 'CMD_RESET':
        machine.reset()
  
  elif topic == topic_repl_in:
    global repl_enable
    if repl_enable:
      m5.termin(msg)


# Test reception e.g. with:
def mqtt_handle():
  mqttc.set_callback(mqtt_sub_cb)
  mqttc.connect()
  print("Connected M5Cloud MQTT Server\r\n")
  mqttc.subscribe(topic_in, qos=1)
  mqttc.subscribe(topic_repl_in)
  while True:
    # Non-blocking wait for message
    mqttc.check_msg()
    global repl_enable
    if repl_enable:
      rambuff = m5.termout_getch()
      if rambuff[0] != 0:
        mqttc.publish(topic_repl_out, rambuff)
    time.sleep_ms(50)
  mqttc.disconnect()


def M5Cloud_handle(params):
  connect_wifi()
  mqtt_handle()


def start():
  _thread.start_new_thread( M5Cloud_handle, ("M5Cloud_handle",))


start()
