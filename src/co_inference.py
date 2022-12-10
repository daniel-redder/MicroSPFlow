"""
Author: Daniel Redder
runs con-inference on target device
"""
import json
from processor import processor
from multiprocessing import Event
import datetime
import secrets
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient


partition_file = "stats/desktop.json"

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

mqtt.connect()

global response_catcher
response_catcher = Event()
global response
response = None

def responseCatch(client, userdata, message):
    global response_catcher
    global response
    response = float(json.loads(message.payload)["result"])
    print(message.payload)
    message.delete()
    response_catcher.set()


mqtt.subscribe("esp32/result", 1, callback = responseCatch)



#ignores specific histogram bounds because there is always a bucket from 0-1 and the exact type of joint/marginal inference is irrelevent
def build_test_set(scope):
    test_set = [{"marginal":{f"V{x}":0 for x in scope}, "data":{f"V{x}":.8 for x in scope}}]

    full_marg = {f"V{x}":1 for x in scope}
    full_marg["V1"] = 0
    full_data = {f"V{x}":None for x in scope}
    full_data["V1"] = .8
    test_set.append({"marginal":full_marg,"data":full_data})

    return test_set


with open(partition_file,"r") as f:
    spn = json.load(f)
    spn = spn["hold"]


process_set = []

unfolded_spn = []

for process in spn:
    for l in process:
        unfolded_spn.append(l)



for process in unfolded_spn:

    cloud_process = {"spn":process["cloud"],"data":None,"scope":process["scope"],"marginal":None,"rootWeights":process["rootWeights"][1]}
    edge_process = {"spn":process["edge"],"data":None,"scope":process["scope"],"marginal":None,"rootWeights":process["rootWeights"][0]}

    test_set = build_test_set(process["scope"])
    print("beginning test")
    #print(test_set[0])

    joint_marginal = []
    for test in test_set:

        cloud_process["data"], cloud_process["marginal"] = test["data"], test["marginal"]
        edge_process["data"], edge_process["marginal"] = test["data"], test["marginal"]

        l_p = datetime.datetime.now()
        mqtt.publish("esp32/process", str(cloud_process), 0)
        print("-- process published")


        edge_result=processor(edge_process["spn"],edge_process["data"],edge_process["marginal"],edge_process["rootWeights"])

        print("--finished edge partition")

        l_edge = datetime.datetime.now()

        response_catcher.wait(100)
        response_catcher.clear()

        result = edge_result + response

        l_d = datetime.datetime.now()

        joint_marginal.append({"fullLatency":l_d-l_p,"edgeLatency":l_edge-l_p,"latencyish":l_d-l_p-(l_edge-l_p)})

    print("finished joint_marg pair")
    process_set.append({"id":process['id'],"data":joint_marginal})


process_set = {"hold":process_set}

mqtt.unsubscribe("esp32/result")
mqtt.disconnect()

print("saving results to stats/results.json")
with open("stats/results.json","w+") as f:
    json.dump(process_set)