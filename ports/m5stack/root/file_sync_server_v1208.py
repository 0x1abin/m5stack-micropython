#!/usr/bin/python3
# -*- coding: utf-8 -*-
import paho.mqtt.client as mqtt
import sys, os, json, time

m5cloud_host = 'mqtt.m5stack.com'
m5cloud_port = 1883
webserver_topic_out = '/M5Cloud/webserver/out'
webserver_topic_in = '/M5Cloud/webserver/in'
root_path = os.getcwd()
node = {"node_id":{"send":0,'recv':0,"msgid":0}}
user_path = 'server_data'
try:
    os.mkdir(user_path)
except:
    pass


def webserver_rpc_handle(jsondata):
    try:
        rpc = json.loads(jsondata)
        method = rpc['method']
        node_id = rpc['params'][0]
        msgid = rpc['id']
        node[node_id] = {"msgid":msgid}

        if method == "connect_node":
            connect_node(node_id)
        elif method == "disconnect_node":
            disconnect_node(node_id)
        elif method == "pull_node_file":
            pull_node_file(node_id)
        elif method == "push_node_file":
            push_node_file(node_id)
        elif method == "repl_node_set":
            repl_node_set(node_id, rpc['params'][1])
    except:
        print('webserver_rpc_handle parser!')


def webserver_rpc_result(res, id, params=0):
    payload = {'result':[res], 'id':id}
    payload = json.dumps(payload)
    mqttc.publish(webserver_topic_out, payload, qos=1)


def connect_node(node_id):
    try:
        os.mkdir(user_path + '/' + node_id)
    except:
        pass
    mqtt_topic_out = '/M5Cloud/'+node_id+'/out'
    mqttc.subscribe(mqtt_topic_out, qos=1)
    print('subscribe:%s'%(mqtt_topic_out))


def disconnect_node(node_id):
    mqtt_topic_out = '/M5Cloud/'+node_id+'/out'
    mqttc.unsubscribe(mqtt_topic_out)
    

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
    node[node_id]["send"] += 1
    publish_node_data(node_id, payload)


def read_node_file_list_cmd(node_id, file_list):
    for file_path in file_list:
        if type(file_path) == list:
            read_node_file_list_cmd(node_id, file_path)
        else:
            read_node_file_cmd(node_id, file_path)


def read_node_file(node_id, path, file):
    if path[0] == '/':
        path = user_path + '/' + node_id + path
    else:
        path = user_path + '/' + node_id+'/'+path
    
    path_dir = os.path.split(path)[0]
    file_name = os.path.split(path)[1]
    print('read_node_file:%s' % (path))
    if not os.path.exists(path_dir):
        os.makedirs(path_dir)
    f = open(path, 'w')
    f.write(file)
    f.close()


def write_node_file(node_id, local_path, node_path):
    try:
        MAX_BUFFER = 1024
        file_size = os.path.getsize(local_path)
        part_nums = file_size // MAX_BUFFER + 1
        f = open(local_path, 'rb')
        for p in range(1, part_nums+1):
            part = [p, part_nums]
            payload = {'cmd':'CMD_WRITE_FILE', 'path':node_path, 'part':part, 'data':f.read(MAX_BUFFER).decode('utf-8')}
            payload = json.dumps(payload)
            print("write node:%s, file:%s, part:[%d/%d]" % (node_id, local_path, part[0],part[1]))
            publish_node_data(node_id, payload)
        node[node_id]['send'] += 1
    except (TypeError,ValueError) as e:
        print('ERORR:write_node_file')
        print(e)
    finally:
        f.close()
        


def write_node_file_list(node_id, path):
    try:
        l = os.listdir(path)
    except:
        write_node_file(node_id, path, path)
    else:
        for i in l:
            write_node_file_list(node_id, path+'/'+i)


def pull_node_file(node_id):
    print('pull node:%s' % (node_id))
    node[node_id]["send"] = 0
    node[node_id]["recv"] = 0
    connect_node(node_id)
    payload = {'cmd':'CMD_LISTDIR', 'path':''}
    payload = json.dumps(payload)
    publish_node_data(node_id, payload)


def push_node_file(node_id):
    local_path = 'server_data/'+node_id+'/'
    print('push node:%s file:%s' % (node_id, os.listdir(local_path)))
    node[node_id]["send"] = 0
    node[node_id]["recv"] = 0
    connect_node(node_id)
    os.chdir(local_path)
    write_node_file_list(node_id, '.')
    os.chdir(root_path)


def repl_node_set(node_id, onoff):
    payload = {'cmd':'CMD_REPL_SET', 'value':onoff}
    payload = json.dumps(payload)
    publish_node_data(node_id, payload)


def reset_node_cmd(node_id):
    payload = b'{"cmd":"CMD_RESET"}'
    publish_node_data(node_id, payload)


def on_message(mqttc, obj, msg):
    # print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
    topic = msg.topic.split('/')[1:]
    try:
        if topic[0] == 'M5Cloud' and topic[2] == 'out':
            node_id = topic[1]
            # print('msg form node_id:'+node_id)
            jsonbuf = json.loads(msg.payload)
            if jsonbuf.get('status') == 200:
                jsondata = jsonbuf.get('data')
                rep_type = jsondata.get('type')

                if rep_type == 'REP_READ_FILE':
                    read_node_file(node_id, jsondata.get('path'), jsondata.get('data'))
                    node[node_id]["recv"] += 1
                    if node[node_id]['send'] == node[node_id]['recv']:
                        print('Read done! node_id:%s , files total:%d' % (node_id, node[node_id]['recv']))
                        webserver_rpc_result('ok', node[node_id]['msgid'])

                elif rep_type == 'REP_LISTDIR':
                    read_node_file_list_cmd(node_id, jsondata.get('data'))

                elif rep_type == 'REP_WRITE_FILE':
                    node[node_id]['recv'] += 1
                    if node[node_id]['send'] == node[node_id]['recv']:
                        reset_node_cmd(node_id)
                        print('Write done! node_id:%s , files total:%d' % (node_id, node[node_id]['recv']))
                        webserver_rpc_result('ok', node[node_id]['msgid'])

        elif topic[1] == 'webserver' and topic[2] == 'in':  
            print('web req:')
            print(msg.payload)
            webserver_rpc_handle(msg.payload)
    except:
        print('Json parser fail!')
        print('topic:%s' % (msg.topic))
        print('payload:%s' % (msg.payload))

        pass


def on_connect(mqttc, obj, flags, rc):
    print("Connected with result code "+str(rc))


def on_publish(mqttc, obj, mid):
    print("Publish mid: " + str(mid))


def on_subscribe(mqttc, obj, mid, granted_qos):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))


def on_log(mqttc, obj, level, string):
    print('* MQTT:'+string + ' | '+time.ctime())


def mqtt_loop_handle(param):
    mqttc.loop_forever()


# If you want to use a specific client id, use
# mqttc = mqtt.Client("client-id")
# but note that the client id must be unique on the broker. Leaving the client
# id parameter empty will generate a random id for you.
mqttc = mqtt.Client()
mqttc.on_message = on_message
mqttc.on_connect = on_connect
# mqttc.on_publish = on_publish
# mqttc.on_subscribe = on_subscribe
# Uncomment to enable debug messages
mqttc.on_log = on_log
mqttc.connect(m5cloud_host, m5cloud_port, 60)
mqttc.subscribe(webserver_topic_in, 1)
# mqttc.subscribe(mqtt_topic_out, 1)
# mqttc.subscribe(mqtt_topic_repl_out, 0)


try:
    cmd_line = sys.argv[1]
except:
    pass
else:
    if cmd_line == 'put':
        node_id = sys.argv[2]
        local_path = sys.argv[3]
        node_path = sys.argv[4]
        write_node_file(node_id, local_path, node_path)
    elif cmd_line == 'get':
        node_id = sys.argv[2]
        node_path = sys.argv[3]
        read_node_file_cmd(node_id, node_path)
    elif cmd_line == 'push':
        node_id = sys.argv[2]
        connect_node(node_id)
        push_node_file(node_id)
    elif cmd_line == 'pull':
        node_id = sys.argv[2]
        connect_node(node_id)
        pull_node_file(node_id)
    elif cmd_line == 'deploy':
        print('Start the M5Cloud node files sync server!')
        print('MQTT server: %s:%d' % (m5cloud_host, m5cloud_port))
        print('User data path: %s' % (user_path))


mqttc.loop_forever()
# _thread.start_new_thread(mqtt_loop_handle, ("mqtt_loop_handle", ))

# while True:
#     time.sleep(1)