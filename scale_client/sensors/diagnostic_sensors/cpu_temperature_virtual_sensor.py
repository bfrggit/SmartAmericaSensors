from scale_client.sensors.virtual_sensor import VirtualSensor

import logging
log = logging.getLogger(__name__)

class CPUTemperatureVirtualSensor(VirtualSensor):
	def __init__(self, broker, device=None, interval=30, threshold=60.0):
		super(CPUTemperatureVirtualSensor, self).__init__(broker, device=device, interval=interval)
		self._threshold = threshold
	
	DEFAULT_PRIORITY = 4
	RECORD_PATH = "/sys/class/thermal/thermal_zone0/temp"

	def get_type(self):
		return "cpu_temperature"

	def read_raw(self):
		with open(self.RECORD_PATH) as tf:
			ln = tf.readline()
			rd = int(ln.rstrip()) / 1000.0
			return rd

	def read(self):
		event = super(CPUTemperatureVirtualSensor, self).read()
		event.data["condition"] = self.__get_condition()
		return event
	
	def __get_condition(self):
		return {
				"threshold": {
					"operator": ">",
					"value": self._threshold
				}
			}

	def policy_check(self, event):
		return event.get_raw_data() > self._threshold


