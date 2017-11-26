#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2014 Roger Light <roger@atchoo.org>
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Distribution License v1.0
# which accompanies this distribution.
#
# The Eclipse Distribution License is available at
#   http://www.eclipse.org/org/documents/edl-v10.php.
#
# Contributors:
#    Roger Light - initial implementation

# This shows an example of using the publish.single helper function.

# import context  # Ensures paho is in PYTHONPATH
import paho.mqtt.client as mqtt
# import paho.mqtt.publish as publish
# import paho.mqtt.subscribe as subscribe
import sys, os, json, time

m5cloud_host = "mqtt.m5stack.com"
m5cloud_port = 1883
chipid_str = '30aea449be0c'

mqtt_topic_out = '/M5Cloud/'+chipid_str+'/out'
mqtt_topic_in  = '/M5Cloud/'+chipid_str+'/in'
mqtt_topic_repl_out = '/M5Cloud/'+chipid_str+'/repl/out'
mqtt_topic_repl_in  = '/M5Cloud/'+chipid_str+'/repl/in'
print('mqtt_topic_out:'+str(mqtt_topic_out))
print('mqtt_topic_in:'+str(mqtt_topic_in))
print('mqtt_topic_repl_out:'+str(mqtt_topic_repl_out))
print('mqtt_topic_repl_in:'+str(mqtt_topic_repl_in))

try:
    cmd_line = sys.argv[1]
except:
    pass

# topic_in = "/M5Cloud/30aea449be0c/repl/in"
# publish.single(topic_in, command+"\r\n", hostname=m5cloud_host, port=m5cloud_port)
# # publish.single("/M5Cloud/id/in", "print('hello')\r\n", hostname="mqtt.m5stack.com")

# def on_message_print(client, userdata, message):
#     print("%s %s" % (message.topic, message.payload))


# subscribe.subscribe(mqtt_topic_out)
# subscribe.callback(on_message_print, mqtt_topic_repl_out, hostname=m5cloud_host, port=m5cloud_port)

# {
#   "cmd":"CMD_WRITE_FILE",
#   "path":"/main.py",
#   "data": "import m5; m5.print('hello world', 0, 0);"
# }

def publish_node_data(node_id, playload):
    mqttc.publish('/M5Cloud/'+node_id+'/in', playload)


def write_node_file(node_id, local_path, node_path):
    print("local_path:")
    print(local_path)
    f = open(local_path)
    playload = {'cmd':'CMD_WRITE_FILE', 'path':node_path, 'data':f.read()}
    playload = json.dumps(playload)
    print("write node:"+node_id+" file:"+local_path+ " buffer:")
    print(playload)
    publish_node_data(node_id, playload)
    f.close()


def read_node_file_cmd(node_id, node_path):
    playload = {'cmd':'CMD_READ_FILE', 'path':node_path}
    playload = json.dumps(playload)
    publish_node_data(node_id, playload)


def pull_node_file(node_id):
    pass


def push_node_file(node_id):
    local_path = 'server_data/'+node_id+'/'
    file_table = os.listdir(local_path)
    print(file_table)
    for file in file_table:
        # try:
        print(file)
        write_node_file(node_id, local_path+file, file)
        # except:
        #     print('except')
        #     pass
        

def on_connect(mqttc, obj, flags, rc):
    print("rc: " + str(rc))


def on_message(mqttc, obj, msg):
    print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))


def on_publish(mqttc, obj, mid):
    print("mid: " + str(mid))


def on_subscribe(mqttc, obj, mid, granted_qos):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))


def on_log(mqttc, obj, level, string):
    print(string)


# If you want to use a specific client id, use
# mqttc = mqtt.Client("client-id")
# but note that the client id must be unique on the broker. Leaving the client
# id parameter empty will generate a random id for you.
mqttc = mqtt.Client()
mqttc.on_message = on_message
mqttc.on_connect = on_connect
mqttc.on_publish = on_publish
mqttc.on_subscribe = on_subscribe
# Uncomment to enable debug messages
# mqttc.on_log = on_log
mqttc.connect(m5cloud_host, m5cloud_port, 60)
mqttc.subscribe(mqtt_topic_out, 0)
# mqttc.subscribe(mqtt_topic_repl_out, 0)

# f = open('webrepl.py')
# mqttc.publish(mqtt_topic_repl_out, f.read(), qos=2)
if cmd_line == 'put':
    local_file = sys.argv[2]
    node_path = sys.argv[3]
    update_node_file(chipid_str, local_file, node_path)
elif cmd_line == 'push':
    node_id = sys.argv[2]
    push_node_file(node_id)

# mqttc.loop_forever()