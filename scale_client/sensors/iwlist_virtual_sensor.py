import time
import iwlib
from iwlib import iwlist
#from scale_client.core.sensed_event import SensedEvent
from scale_client.sensors.threaded_virtual_sensor import ThreadedVirtualSensor

import logging
log = logging.getLogger(__name__)

class IWListVirtualSensor(ThreadedVirtualSensor):
	def __init__(self, broker, device=None, interval=4, if_name=None, empty_essid=None, max_unknown=10, white_list=None, debug=False):
		super(IWListVirtualSensor, self).__init__(broker, device=device, interval=interval)
		self._interval = interval
		self._if_name = if_name # Interface device name, for example: wlan0
		self._debug_flag = debug

		# Advanced scanning features
		self._empty_essid_flag = empty_essid # If set to False, filter out all APs without an ESSID
		self._max_unknown = max_unknown # Number of APs to report/record, for APs not in white-list
		self._white_list = dict() # List of APs that are always reported
		if white_list is not None and type(white_list) == type([]):
			for white_ap in white_list:
				self._white_list[white_ap] = 9 #XXX: Using as a set, giving random integer values

	def get_type(self):
		return "iwlist_scan"

	def on_start(self):
		try:
			iwlist.scan(self._if_name)
		except TypeError:
			log.error("failed to start because of TypeError")
			return False
		except OSError:
			log.error("failed to start because of OSError")
			return False
		
		super(IWListVirtualSensor, self).on_start()

	def scan(self):
		return iwlist.scan(self._if_name)

	def _get_bssid(self, ap):
		if "Access Point" in ap:
			return ap["Access Point"]
		elif "Cell" in ap:
			return ap["Cell"]
		log.info("BSSID field not found for ESSID: %s" % ap["ESSID"])
		return None
	
	def _do_sensor_read(self):
		log.debug("%s reading sensor data..." % self.get_type())

		ap_list = self.scan()
		timestamp = time.time()
		event_list = []
		for ap in ap_list:
			data = {
					"essid": ap["ESSID"],
					"bssid": self._get_bssid(ap),
					"mode": ap["Mode"].lower(),
					"noise": ap["stats"]["noise"],
					"level": ap["stats"]["level"],
					"quality": ap["stats"]["quality"]
				}
			event = self.make_event_with_raw_data(data)
			event.timestamp = timestamp
			event_list.append(event)
		event_list.sort(key=lambda x: (x.get_raw_data()["quality"], x.get_raw_data()["level"], -x.get_raw_data()["noise"]), reverse=True)

		n_total = len(event_list)
		n_pub = 0
		n_white = 0
		for event in event_list:
			if event is None:
				continue
			if self.policy_check(event):
				if self._is_white(event):
					n_white += 1
				else:
					n_pub += 1
				self.publish(event)
		if self._debug_flag:
			debug_e = self.make_event_with_raw_data((n_total, n_pub, n_white))
			debug_e.data["event"] = "debug_iwlist_scan_count"
			debug_e.priority = 7
			self.publish(debug_e)
	
	def policy_check(self, event):
		ret = True
		data = event.get_raw_data()
		if type(data) != type({}):
			raise TypeError
		if "essid" not in data:
			raise ValueError

		# Check if it is necessary to filter out APs with empty ESSID
		if self._empty_essid_flag is not None and not self._empty_essid_flag: # It is False
			if len(data["essid"].strip()) < 1:
				ret = False

		return ret
	
	def _is_white(self, event):
		data = event.get_raw_data()
		if type(data) != type({}):
			raise TypeError
		if "essid" not in data:
			raise ValueError

		if self._white_list is None:
			return False
		return data["essid"] in self._white_list

