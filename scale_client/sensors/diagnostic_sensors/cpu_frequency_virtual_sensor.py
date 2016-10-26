from scale_client.sensors.virtual_sensor import VirtualSensor

import logging
log = logging.getLogger(__name__)

class CPUFrequencyVirtualSensor(VirtualSensor):
	def __init__(self, broker, device=None, interval=30):
		super(CPUFrequencyVirtualSensor, self).__init__(broker, device=device, interval=interval)
	
	DEFAULT_PRIORITY = 7
	RECORD_PATH = "/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_cur_freq"

	def get_type(self):
		return "cpu_frequency"

	def read_raw(self):
		with open(self.RECORD_PATH) as tf:
			ln = tf.readline()
			rd = int(ln.rstrip()) / 1000.0
			return rd

	def policy_check(self, event):
		return True

"""
	def read(self):
		event = super(CPUFrequencyVirtualSensor, self).read()
		event.data["condition"] = self.__get_condition()
		return event
"""

