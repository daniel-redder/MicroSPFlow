import network
import secrets
sta_if = network.WLAN(network.STA_IF)
ap_if = network.WLAN(network.AP_IF)

sta_if.active(True)

sta_if.connect(secrets.ssid,secrets.password)
sta_if.isconnected()


ap_if.active(False)