from scale_client.event_sinks.event_sink import EventSink

import json
import time
import threading
import logging
log = logging.getLogger(__name__)
#log.setLevel(logging.INFO)


class RFEventSink(EventSink):
	def __init__(self, broker, tty_path=None, sleep=0):
		super(RFEventSink, self).__init__(broker)
		if not tty_path or type(tty_path) != type(""):
			raise TypeError
		self._dev_path = tty_path
		self._dev_name = tty_path.split("/")[-1]
		self._sleep = sleep
		self._rfca = False
		self._rf_lock = threading.Lock()

	def send(self, encoded_event_2):
		if not encoded_event_2 or not type(encoded_event_2) == type(()) or len(encoded_event_2) != 2:
			return

		time_x, encoded_event = encoded_event_2
		time_f = time.time()
		timestamp = time.strftime("%H:%M:%S", time.localtime(time_f))
		time_diff = " "
		if time_x is not None:
			time_diff = " %+d " % round((time_x - time_f) * 1000)

		msg = encoded_event
		d = None
		self._rf_lock.acquire()
		try:
			d = open(self._dev_path, "r+")
			d.write(timestamp + time_diff + msg + " \r\n")
			d.close()
			log.info("messaged wrote to " + self._dev_name)
		except IOError:
			log.warning("failed writing to " + self._dev_name)
		time.sleep(self._sleep)
		self._rf_lock.release()
		#log.info(msg)

	MODE_STR = {
		0: "NO DATA",
		1: "NO FIX",
		2: "2D FIX",
		3: "3D FIX"
	}

	def encode_event(self, event):
		et = event.get_type()
		ed = event.get_raw_data()
		log.debug("received event type: " + et)
		encoded_event = None
		timestamp = None
		if hasattr(event, "timestamp") and (type(event.timestamp) == type(9.0) or type(event.timestamp) == type(9)):
			timestamp = event.timestamp

		if et == "heartbeat":
			encoded_event = "HB"
		elif et == "rfcomm_connect":
			if ed is not None:
				self._rfca = ed
				if self._rfca:
					encoded_event = "DEV: Connected."
					log.debug("rfcomm device available")
				else:
					log.debug("rfcomm device unavailable")
		elif et == "rfcomm_message":
			if type(ed) == type(""):
				encoded_event = "ECHO: " + ed
			else:
				log.warning("unrecognized data type in event object with type: " + et)
		elif et == "debug_gps_mode":
			if type(ed) == type(9):
				encoded_event = "GPS: Mode " + str(ed) + " "
				if ed in self.MODE_STR:
					encoded_event += self.MODE_STR[ed]
				else:
					encoded_event += "UNKNOWN" # Should not happen
			else:
				log.warning("unrecognized data type in event object with type: " + et)
		elif et == "debug_gps_location" or et == "debug_gps_jump":
			if type(ed) == type({}) and "lat" in ed and "lon" in ed:
				encoded_event = "GPS: " + "%.4f" % ed["lat"] + ", " + "%.4f" % ed["lon"]
				if et == "debug_gps_jump":
					encoded_event += " (?)"
			elif ed is None:
				encoded_event = "GPS: Location unavailable."
			else:
				log.warning("unrecognized data type in event object with type: " + et)
		elif et == "debug_location_update":
			if ed:
				encoded_event = "LM: Location available."
			else:
				encoded_event = "LM: Location unavailable."
		elif et == "debug_location_expire":
			if type(ed) == type(""):
				encoded_event = "LM: Location expired (" + ed + ")"
			else:
				log.warning("unrecognized data type in event object with type: " + et)
		elif et == "debug_text":
			if type(ed) == type(""):
				encoded_event = "TEXT: " + ed
			else:
				log.warning("unrecognized data type in event object with type: " + et)
		elif et == "debug_iwlist_scan_count":
			warning_flag = True
			if type(ed) == type(()):
				if len(ed) == 2 and type(ed[0]) == type(ed[1]) and type(ed[1]) == type(9):
					encoded_event = "IWLIST: %d, %d" % ed
					warning_flag = False
				elif len(ed) == 3 and type(ed[0]) == type(ed[1]) and type(ed[1]) == type(ed[2]) and type(ed[2]) == type(9):
					if ed[2] == 0:
						encoded_event = "IWLIST: %d, %d" % ed[0:2]
						warning_flag = False
					elif ed[2] > 0:
						encoded_event = "IWLIST: %d, %d (%d)" % (ed[0], ed[1] + ed[2], ed[2])
						warning_flag = False
			if warning_flag:
				log.warning("unrecognized data type in event object with type: " + et)
		elif et == "debug_cmd_bad_format":
			encoded_event = "CMD: Bad format."
		elif et == "debug_geofence_reset":
			encoded_event = "GF: Target reset."
		elif et == "debug_geofence_set" or et == "debug_geofence_set_failure":
			if type(ed) == type(""):
				encoded_event = "GF: Target "
				if et == "debug_geofence_set_failure":
					encoded_event += "cannot set: "
				else:
					encoded_event += "set: "
				encoded_event += ed
			else:
				log.warning("unrecognized data type in event object with type: " + et)
		elif et == "geofence_trigger":
			if type(ed) == type(""):
				encoded_event = "GF: Target %s triggered." % ed
			else:
				log.warning("unrecognized data type in event object with type: " + et)
		else: # Unrecognized event
			log.debug("unrecognized event")
			pass

		encoded_event_2 = None

		if encoded_event is not None:
			encoded_event_2 = (timestamp, encoded_event)
		return encoded_event_2

	def check_available(self, event):
		et = event.get_type()
		if et == "rfcomm_connect":
			return True
		return self._rfca
