import sys
import argparse
import logging
import time, datetime
from bs4 import BeautifulSoup

sys.path.insert(0,'../')
from ThingPlugApi import ThingPlug 

THINGPLUG_HOST = 'onem2m.sktiot.com'
THINGPLUG_PORT = 9443
THINGPLUG_APPEUI = 'ThingPlug'
MQTT_CLIENT_ID = 'bridge'
SUBS_PREFIX = 'thingplug_'
CONTAINER = 'LoRa'

def mqtt_on_message_cb(client, userdata, msg):
    # logging.info(msg.topic)
    # logging.info(msg.payload)
    xml_root = BeautifulSoup(msg.payload,'html.parser')
    data_payload = getattr(xml_root.find('pc').find('cin').find('con'), 'string', None)
    lt_time = getattr(xml_root.find('pc').find('cin').find('lt'), 'string', None)

    current_time = str(datetime.datetime.now())
    output_data = current_time + ',' + data_payload + ',' + lt_time + '\r\n'
    print output_data,
    
    if enable_log > 0:
        f = open('subscription_mqtt.log','a')
        f.write(output_data)
        f.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'ThingPlug Login Example')
    
    parser.add_argument('-u', '--user_id', type=str, help='ThingPlug User ID', required=True)
    parser.add_argument('-p', '--user_pw', type=str, help='ThingPlug User Password', required=True)

    parser.add_argument('-ni', '--node_id', type=str, help='ThingPlug Node ID', required=False)
    parser.add_argument('-ct', '--container', type=str, help='ThingPlug Container Name(Default:LoRa)', required=False)
    parser.add_argument('-th', '--thingplug_host', type=str, help='ThingPlug Host IP(Default:onem2m.sktiot.com)', required=False)
    parser.add_argument('-tp', '--thingplug_port', type=int, help='ThingPlug Port(Default:9443)', required=False)
    parser.add_argument('-ae', '--app_eui', type=str, help='ThingPlug APP EUI(Default:ThingPlug)', required=False)

    parser.add_argument('-ci', '--mqtt_client_id', type=str, help='ThingPlug MQTT Client ID(Deafult:bridge)', required=False)
    parser.add_argument('-el', '--enable_log', type=int, help='', required=False)

    args = parser.parse_args()
    
    if args.container      != None:    CONTAINER = args.container
    if args.thingplug_host != None:    THINGPLUG_HOST = args.thingplug_host
    if args.thingplug_port != None:    THINGPLUG_PORT = args.thingplug_port
    if args.mqtt_client_id != None:    MQTT_CLIENT_ID = args.mqtt_client_id
    if args.app_eui != None:           THINGPLUG_APPEUI = args.app_eui

    global enable_log
    enable_log = 0
    if args.enable_log     != None:    enable_log = 1
        
    
    thingplug = ThingPlug.ThingPlug(THINGPLUG_HOST,THINGPLUG_PORT)
    thingplug.login(args.user_id, args.user_pw)
    
    thingplug.setAppEui(THINGPLUG_APPEUI)
    thingplug.getDeviceList()

    mqtt_client_id = thingplug.getUserId() + '_' + MQTT_CLIENT_ID 
    thingplug.setMqttClientId(mqtt_client_id)
    thingplug.mqttConnect()
    thingplug.mqttSetOnMessage(mqtt_on_message_cb)
    

    if args.node_id == None:
        status,node_cnt,node_list = thingplug.getDeviceList()
    
        if node_cnt == None:
            logging.warning('Node list is empty')
            sys.exit()
    
        for i in range(int(node_cnt)):
            subs_name = SUBS_PREFIX + node_list[i]
            if thingplug.retrieveSubscription(node_list[i], subs_name, CONTAINER) == True:
                thingplug.deleteSubscription(node_list[i], subs_name, CONTAINER)
             
            thingplug.createSubscription(node_list[i], subs_name, CONTAINER, mqtt_client_id)
    else:
        subs_name = SUBS_PREFIX + args.node_id
        if thingplug.retrieveSubscription(args.node_id, subs_name, CONTAINER) == True:
            thingplug.deleteSubscription(args.node_id, subs_name, CONTAINER)
        
        thingplug.createSubscription(args.node_id, subs_name, CONTAINER, mqtt_client_id)
    
    thingplug.mqttLoopForever()

    print 'abcdef'