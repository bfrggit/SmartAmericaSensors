from time import sleep
from scale_client.core.threaded_application import ThreadedApplication
from scale_client.core.sensed_event import SensedEvent

import logging
log = logging.getLogger(__name__)

class RFListener(ThreadedApplication):
	def __init__(self, broker, tty_path=None):
		super(RFListener, self).__init__(broker)
		if not tty_path or type(tty_path) != type(""):
			raise TypeError
		self._dev_path = tty_path
		self._dev_name = tty_path.split("/")[-1]

	DEFAULT_PRIORITY = 9 
	MESSAGE_PRIORITY = 9
	CONNECT_PRIORITY = 7

	def on_start(self):
		self.run_in_background(self._io_loop)

	def _io_loop(self):
		while True:
			d = None
			try:
				d = open(self._dev_path)
				log.info("connected")
				#self._flag_loc = True
				self.publish(self._debug_connect_event(True))
			except IOError:
				#log.warning("failed")
				#self._flag_loc = False
				sleep(1)
				continue
			while True:
				message = d.readline()
				if message == "": # Disconnected
					d.close()
					log.info("disconnected")
					#self._flag_loc = False
					self.publish(self._debug_connect_event(False))
					sleep(1)
					break
				message = message.rstrip()
				structured_data = {
						"event": "rfcomm_message",
						"value": message
					}
				event = SensedEvent(
						sensor=self._dev_name,
						data=structured_data,
						priority=self.MESSAGE_PRIORITY
					)
				self.publish(event)

	def _debug_connect_event(self, value):
		structured_data = {
				"event": "rfcomm_connect",
				"value": value
			}
		event = SensedEvent(
				sensor=self._dev_name,
				data=structured_data,
				priority=self.CONNECT_PRIORITY
			)
		return event
	
