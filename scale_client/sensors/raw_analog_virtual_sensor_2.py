from __future__ import print_function

from scale_client.sensors.analog_virtual_sensor import AnalogVirtualSensor
from scale_client.core.sensed_event import SensedEvent


class RawAnalogVirtualSensor(AnalogVirtualSensor):
    def __init__(self, broker, device=None, interval=1, analog_port=None, custom_type=None):
        super(RawAnalogVirtualSensor, self).__init__(broker, device=device, interval=interval, analog_port=analog_port)

        self._custom_type = custom_type

    DEFAULT_PRIORITY = 9

    def get_type(self):
        if type(self._custom_type) == type(""):
            return self._custom_type
        return "raw_analog"

    def policy_check(self, data):
        return True
