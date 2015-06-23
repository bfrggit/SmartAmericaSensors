from scale_client.event_sinks.event_sink import EventSink

import json
import time
import threading
import logging
log = logging.getLogger(__name__)
#log.setLevel(logging.INFO)


class RFEventSink(EventSink):
	def __init__(self, broker, tty_path=None):
		super(RFEventSink, self).__init__(broker)
		if not tty_path or type(tty_path) != type(""):
			raise TypeError
		self._dev_path = tty_path
		self._dev_name = tty_path.split("/")[-1]
		self._rfca = False
		self._rf_lock = threading.Lock()

	def send(self, encoded_event):
		if not encoded_event:
			return

		msg = encoded_event
		timestamp = time.strftime("%H:%M", time.localtime(time.time()))
		d = None
		self._rf_lock.acquire()
		try:
			d = open(self._dev_path, "w")
			d.write(timestamp + " " + msg + "\r\n")
			d.close()
			log.info("messaged wrote to " + self._dev_name)
		except IOError:
			log.warning("failed writing to " + self._dev_name)
		time.sleep(0.2)
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
		elif et == "debug_gps_location":
			if type(ed) == type({}) and "lat" in ed and "lon" in ed:
				encoded_event = "GPS: " + str(ed["lat"]) + ", " + str(ed["lon"])
			elif ed is None:
				encoded_event = "GPS: Location unavailable."
			else:
				log.warning("unrecognized data type in event object with type: " + et)
		elif et == "debug_location_update":
			if ed:
				encoded_event = "LM: Location available."
			else:
				encoded_event = "LM: Location unavailable."
		else: # Unrecognized event
			log.debug("unrecognized event")
			pass
		return encoded_event

	def check_available(self, event):
		et = event.get_type()
		if et == "rfcomm_connect":
			return True
		return self._rfca
