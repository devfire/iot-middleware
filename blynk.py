import blynklib
import random

# blynk auth token
BLYNK_AUTH = 'qVzQ9p19MoOzZ1xVX2jCLWnS7xe1N7_e'

# initialize Blynk
blynk = blynklib.Blynk(BLYNK_AUTH)

READ_PRINT_MSG = "[READ_VIRTUAL_PIN_EVENT] Pin: V{}"
WRITE_EVENT_PRINT_MSG = "[WRITE_VIRTUAL_PIN_EVENT] Pin: V{} Value: '{}'"

'''
# register handler for virtual pin V4 write event
@blynk.handle_event('write V4')
def write_virtual_pin_handler(pin, value):
    print(WRITE_EVENT_PRINT_MSG.format(pin, value))
'''

# register handler for virtual pin V11 reading
@blynk.handle_event('read V1')
def read_handler(vpin):
    value = random.randint(0, 1024)
    print(READ_PRINT_MSG.format(pin))
    blynk.virtual_write(vpin, value)

###########################################################
# infinite loop that waits for event
###########################################################
while True:
    blynk.run()