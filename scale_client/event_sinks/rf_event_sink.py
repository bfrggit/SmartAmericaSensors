from scale_client.event_sinks.event_sink import EventSink

import json
import logging
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class RFEventSink(EventSink):
	def __init__(self, broker, tty_path=None):
		super(RFEventSink, self).__init__(broker)
		if not tty_path or type(tty_path) != type(""):
			raise TypeError
		self._dev_path = tty_path
		self._dev_name = tty_path.split("/")[-1]
		self._rfca = False

	def send(self, encoded_event):
		if not encoded_event:
			return

		msg = encoded_event
		d = None
		try:
			d = open(self._dev_path, "w")
			d.write(msg + "\r\n")
			d.close()
			log.info("messaged wrote to " + self._dev_name)
		except IOError:
			log.warning("failed writing to " + self._dev_name)
		log.info(msg)

	def encode_event(self, event):
		et = event.get_type()
		ed = event.get_raw_data()
		log.debug("received event type: " + et)
		encoded_event = None

		if et == "heartbeat":
			encoded_event = "heartbeat"
		elif et == "rfcomm_connect":
			if ed is not None:
				self._rfca = ed
				if self._rfca:
					encoded_event = "DEV: Connected."
					log.debug("available")
				else:
					log.debug("unavailable")
		elif et == "rfcomm_message":
			if type(ed) == type(""):
				encoded_event = "ECHO: " + ed
		else:
			log.debug("unrecognized event")
			pass
		return encoded_event

	def check_available(self, event):
		et = event.get_type()
		if et == "rfcomm_connect":
			return True
		return self._rfca
