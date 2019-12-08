try:
    import usocket as socket
except:
    import socket

response_404 = """HTTP/1.0 404 NOT FOUND

<h1>404 Not Found</h1>
"""

response_500 = """HTTP/1.0 500 INTERNAL SERVER ERROR

<h1>500 Internal Server Error</h1>
"""

response_template = """HTTP/1.0 200 OK

%s
"""

import machine
import ntptime, utime
from machine import RTC
from time import sleep

pin = machine.Pin(9, machine.Pin.OUT)

rtc = RTC()
try:
    seconds = ntptime.time()
except:
    seconds = 0
rtc.datetime(utime.localtime(seconds))

def time():
    body = """<html>
<body>
<h1>Time</h1>
<p>%s</p>
</body>
</html>
""" % str(rtc.datetime())

    return response_template % body

def light_on():
     pin.value(1)
     body = "You turned a light on!"
     return response_template % body

def light_off():
     pin.value(0)
     body = "You turned a light off!"
     return response_template % body

def blinking_body():
    body = "LED blinking!"
    return response_template % body
    
def blink():
    yield "LED blinking!"
    for i in range(20):
        pin.value(1)
        time.sleep(.5)
        pin.value(0)
        time.sleep(.5)

blink_gen = blink()

def iter_blink():
    resp = blink_gen.__next__()
    return resp
    while True:
        try:
            blink_gen.__next__()
        except StopIteration:
            return resp
            break

def light_blink(n):
    for i in range(n):
        pin.value(1)
        sleep(.2)
        pin.value(0)
        sleep(.2)

def blinking():
    try:
        return "LED blinking!"
    finally:
        light_blink(30)
        
def dummy():
    body = "This is a dummy endpoint"

    return response_template % body

switch_pin = machine.Pin(10, machine.Pin.IN)

def switch():
    body = "{state: " + str(switch_pin.value()) + "}"
    return response_template % body

adc = machine.ADC(0)
led_pin = machine.Pin(13)
max_light = 1024

def light():
    bright = adc.read()
    pwm = machine.PWM(led_pin)
    pwm.frequency(500)
    pwm.duty(int(bright))  # more bright less light in LED
    body = "{value: " + str(bright) + "}"
    body += "\nbrightness:  0% [{}] 100%".format("=" * int(bright/1024 * 20) + " "*(20 - int(bright/1024 * 20)))
    return response_template % body

handlers = {
    'time': time,
    'dummy': dummy,
    'light_on': light_on,
    'light_off': light_off,
    'blinking': blinking,
    'switch': switch,
    'light': light,
}

def main():
    s = socket.socket()
    ai = socket.getaddrinfo("0.0.0.0", 8080)
    addr = ai[0][-1]

    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    s.bind(addr)
    s.listen(5)
    print("Listening, connect your browser to http://<this_host>:8080")

    while True:
        sleep(1)
        res = s.accept()
        client_s = res[0]
        client_addr = res[1]
        req = client_s.recv(4096)
        print("Request:")
        print(req)

        try:
            path = req.decode().split("\r\n")[0].split(" ")[1]
            handler = handlers[path.strip('/').split('/')[0]]
            response = handler()
        except KeyError:
            response = response_404
        except Exception as e:
            response = response_500
            print(str(e))

        client_s.send(b"\r\n".join([line.encode() for line in response.split("\n")]))

        client_s.close()
        print()

main()

# >>> import machine                                                                                          
# >>> pin = machine.Pin(13)                                                                                   
# >>> pwm = machine.PWM(pin)                                                                                  
# >>> pwm                                                                                                     
# PWM(13, freq=100, duty=199)                                                                                                                                                                           
# >>> pwm.duty(0)       # bright                                                                                         
# >>> pwm.duty(1000)    # dark                                                                                   
# >>>          