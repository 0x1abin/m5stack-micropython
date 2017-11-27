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
import sys, os, json, time, _thread

m5cloud_host = "mqtt.m5stack.com"
m5cloud_port = 1883
chipid_str = '30aea449be0c'
user_path = 'server_data/'

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

def list_file_tree(path):
    try:
        l = os.listdir(path)
    except:
        return path
    else:
        path_list = []
        for i in l:
            path_list.append(list_file_tree(path+'/'+i))
        return path_list



def publish_node_data(node_id, payload):
    mqttc.publish('/M5Cloud/'+node_id+'/in', payload, qos=1)
    pass


def read_node_file_cmd(node_id, file_path):
    payload = {'cmd':'CMD_READ_FILE', 'path':file_path}
    payload = json.dumps(payload)
    publish_node_data(node_id, payload)


def read_node_file_list_cmd(node_id, file_list):
    for file_path in file_list:
        if type(file_path) == str:
            read_node_file_cmd(node_id, file_path)
        elif type(file_path) == list:
            read_node_file_list_cmd(node_id, file_path)


def read_node_file(node_id, path, file):
    if path[0] == '/':
        path = user_path + node_id + path
    else:
        path = user_path + node_id+'/'+path
    
    path_dir = os.path.split(path)[0]
    file_name = os.path.split(path)[1]
    print('read_node_file:')
    print(path)
    if not os.path.exists(path_dir):
        os.makedirs(path_dir)
    f = open(path, 'w')
    print('file:')
    print(file)
    f.write(file)
    f.close()


def pull_node_file(node_id):
    payload = {'cmd':'CMD_LISTDIR', 'path':''}
    payload = json.dumps(payload)
    publish_node_data(node_id, payload)


def write_node_file(node_id, local_path, node_path):
    print(local_path)
    try:
        # f = open(user_path + node_id + '/' + local_path)
        f = open(local_path)
        payload = {'cmd':'CMD_WRITE_FILE', 'path':node_path, 'data':f.read()}
        payload = json.dumps(payload)
        print("write node:"+node_id+" file:"+local_path+ " buffer:")
        # print(payload)
        publish_node_data(node_id, payload)
        f.close()
    except:
        pass


def write_node_file_list(node_id, path):
    try:
        l = os.listdir(path)
    except:
        write_node_file(node_id, path, path)
        pass
    else:
        for i in l:
            write_node_file_list(node_id, path+'/'+i)
        pass


def push_node_file(node_id):
    local_path = 'server_data/'+node_id+'/'
    os.chdir(local_path)
    write_node_file_list(node_id, '.')
    os.chdir('./../../')



def on_message(mqttc, obj, msg):
    print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
    topic = msg.topic.split('/')

    if topic[1] == 'M5Cloud':
        node_id = topic[2]
        print('msg form node_id:'+node_id)
        try:
            jsonbuf = json.loads(msg.payload)
            if jsonbuf.get('status') == 200:
                jsondata = jsonbuf.get('data')
                rep_type = jsondata.get('type')

                if rep_type == 'REP_READ_FILE':
                    read_node_file(node_id, jsondata.get('path'), jsondata.get('data'))

                elif rep_type == 'REP_LISTDIR':
                    read_node_file_list_cmd(node_id, jsondata.get('data'))
                    pass

                elif rep_type == 'REP_WRITE_FILE':
                    pass
        except:
            print('Json parser fail!')
            pass


def on_connect(mqttc, obj, flags, rc):
    print("rc: " + str(rc))


def on_publish(mqttc, obj, mid):
    print("mid: " + str(mid))


def on_subscribe(mqttc, obj, mid, granted_qos):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))


def on_log(mqttc, obj, level, string):
    print(string)


def mqtt_loop_handle(param):
    mqttc.loop_forever()


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

if cmd_line == 'put':
    local_file = sys.argv[2]
    node_path = sys.argv[3]
    update_node_file(chipid_str, local_file, node_path)
elif cmd_line == 'get':
    node_id = sys.argv[2]
    node_path = sys.argv[3]
    read_node_file_cmd(node_id, node_path)
elif cmd_line == 'push':
    node_id = sys.argv[2]
    push_node_file(node_id)
elif cmd_line == 'pull':
    node_id = sys.argv[2]
    pull_node_file(node_id)
elif cmd_line == 'test':
    print(sys.argv[2])
    print(list_file_tree(sys.argv[2]))

mqttc.loop_forever()
# _thread.start_new_thread(mqtt_loop_handle, ("mqtt_loop_handle", ))

# while True:
#     time.sleep(1)