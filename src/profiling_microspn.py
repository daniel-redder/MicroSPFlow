"""
Author: Daniel Redder
executes on edge device. Produces p_e, p_c, l

micropython compatible except for MQTT utility
https://github.com/micropython/micropython/issues/5929
ussl problems
"""
import time
import secrets
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from processor import pTest, getTestNodes
from multiprocessing import Event

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
latency = None
response_latency = None

def responseCatch(client, userdata, message):
    global latency
    latency = message.payload
    global response_catcher
    response_catcher.set()


def fullCatch(client, userdata, message):
    global response_latency
    response_latency = message.payload
    global completion_catcher
    completion_catcher.set()


def profile():

    p_e_b = time.time()
    nodeCount = pTest()
    p_e_a = time.time()

    p_e = (p_e_a - p_e_b) / nodeCount

    #I do not include connection time in p_c profiling
    mqtt.connect()

    l_b = time.time()
    mqtt.publish("esp32/profile",str(getTestNodes()),0)

    mqtt.subscribe("esp32/profileCallback", 1, callback = responseCatch)
    mqtt.subscribe("esp32/profile_results",1,callback = fullCatch)

    global response_catcher
    response_catcher.wait(100)

    l_a = time.time()

    l = (l_a - l_b) / 2

    global completion_catcher
    completion_catcher.wait(100)
    mqtt.unsubscribe("esp32/profileCallback")
    mqtt.unsubscribe("esp32/profile_results")
    mqtt.disconnect()

    p_c_a = time.time()

    p_c = (p_c_a - l_b) - 2*l

    return p_e, p_c, l


