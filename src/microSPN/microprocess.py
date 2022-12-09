from umqtt.simple import MQTTClient as mqt
import secrets


certificate_file = "root-CA.crt"
local_crt = "esp32.cert.pem"

private_key_file = "esp32.private.key"

mqtt_client_id = "esp32"
mqtt_port = 8883
mqtt_topic = "esp32/publish"
mqtt_host = secrets.endp
mqtt_client = None

with open(private_key_file, "r") as f:
    private_key = f.read()


with open(local_crt,"r") as f:
    certificate = f.read()

#with open(certificate_file,"r") as f:
#    server_cert = f.read()


mqtt_client = mqt(client_id=mqtt_client_id, server=mqtt_host, port=mqtt_port, keepalive=5000,
                  ssl=True, ssl_params={"cert":certificate, "key":private_key,"ca_certs":certificate_file, "server_side":False}) 
#"ca_certs":server_cert

mqtt_client.connect()
mqtt_client.publish(mqtt_topic,"test message")