import psutil
from scale_client.sensors.threaded_virtual_sensor import ThreadedVirtualSensor

import logging
log = logging.getLogger(__name__)

class CPUUtilizationVirtualSensor(ThreadedVirtualSensor):
	def __init__(self, broker, device=None, interval=5, threshold=90.0):
		super(CPUUtilizationVirtualSensor, self).__init__(broker, device=device, interval=interval)
		self._threshold = threshold

	def get_type(self):
		return "cpu_utilization"

	def read_raw(self):
		return round(psutil.cpu_percent(interval=1), 2)

	def read(self):
		event = super(CPUUtilizationVirtualSensor, self).read()
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


