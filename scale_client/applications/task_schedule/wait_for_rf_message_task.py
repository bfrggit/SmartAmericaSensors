from task_schedule import TaskItem
from scale_client.core.sensed_event import SensedEvent

class WaitForRFMessageTask(TaskItem):
	def __init__(self, text):
		TaskItem.__init__(self)

		if type(text) != type(""):
			raise TypeError
		self._text = text
	
	def on_start(self):
		evtls = []
		evt_0 = SensedEvent(
				sensor="task",
				priority=8,
				data={"event": "debug_text", "value": "Waiting: %s" % self._text}
			)
		evtls.append(evt_0)
		return evtls
	
	def on_complete(self):
		evtls = []
		evt_0 = SensedEvent(
				sensor="task",
				priority=8,
				data={"event": "debug_text", "value": "Received: %s" % self._text}
			)
		evtls.append(evt_0)
		return evtls
	
	def listener_check(self, event):
		et = event.get_type()
		ed = event.get_raw_data()
		
		if et != "rfcomm_message":
			return False
		if ed != self._text:
			return False
		return True

