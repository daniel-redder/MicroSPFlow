"""
Author: Daniel Redder
executes on edge device. Produces p_e, p_c, l

micropython compatible except for MQTT utility
https://github.com/micropython/micropython/issues/5929
ussl problems
"""
import datetime
import secrets
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from processor import pTest, getTestNodes
from multiprocessing import Event
import json

server_crt = "root-CA.crt"
local_crt = "esp32.cert.pem"

private_key_file = "esp32.private.key"

mqtt_client_id = "esp32"
mqtt_port = 8883

mqtt_host = secrets.endp

mqtt = AWSIoTMQTTClient(mqtt_client_id)
mqtt.configureEndpoint(mqtt_host, mqtt_port)
mqtt.configureCredentials(server_crt, private_key_file, local_crt)

# from https://github.com/aws/aws-iot-device-sdk-python
mqtt.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
mqtt.configureDrainingFrequency(2)  # Draining: 2 Hz
mqtt.configureConnectDisconnectTimeout(10)  # 10 sec
mqtt.configureMQTTOperationTimeout(5)  # 5 sec

response_catcher = Event()
completion_catcher = Event()
response_latency = None

def responseCatch(client, userdata, message):
    global response_catcher
    print(message.payload)
    response_catcher.set()


def fullCatch(client, userdata, message):
    global response_latency
    response_latency = message.payload
    print(response_latency)
    global completion_catcher
    completion_catcher.set()


def profile():

    p_e_b = datetime.datetime.now()
    nodeCount = pTest()
    p_e_a = datetime.datetime.now()

    p_e = (p_e_a - p_e_b) / nodeCount

    #I do not include connection time in p_c profiling
    mqtt.connect()

    l_b = datetime.datetime.now()
    mqtt.publish("esp32/profile",str(getTestNodes()),0)

    mqtt.subscribe("esp32/profileCallback", 1, callback = responseCatch)
    mqtt.subscribe("esp32/result",1,callback = fullCatch)

    global response_catcher
    response_catcher.wait(100)

    l_a = datetime.datetime.now()

    l = (l_a - l_b) / 2

    global completion_catcher
    completion_catcher.wait(100)

    #p_c.microseconds/1000
    global response_latency
    p_c = json.loads(response_latency)["p_c"]


    mqtt.unsubscribe("esp32/profileCallback")
    mqtt.unsubscribe("esp32/result")
    mqtt.disconnect()



    return p_e.microseconds/1000, p_c, l.microseconds/1000


print(profile())