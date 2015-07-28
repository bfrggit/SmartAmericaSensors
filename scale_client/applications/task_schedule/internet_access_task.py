from task_schedule import TaskItem
from scale_client.core.sensed_event import SensedEvent

class InternetAccessTask(TaskItem):
	def __init__(self):
		TaskItem.__init__(self)

	def on_start(self):
		evtls = []
		evt_0 = SensedEvent(
				sensor="task",
				priority=5,
				data={"event": "debug_prompt", "value": "HOLD and wait for Internet access."}
			)
		evt_1 = SensedEvent(
				sensor="task",
				priority=4,
				data={"event": "debug_internet_access_query", "value": None}
			)
		evtls.append(evt_0)
		evtls.append(evt_1)
		return evtls
	
	def on_complete(self):
		evtls = []
		evt_0 = SensedEvent(
				sensor="task",
				priority=8,
				data={"event": "debug_text", "value": "Received Internet access."}
			)
		evtls.append(evt_0)
		return evtls
	
	def listener_check(self, event):
		et = event.get_type()
		ed = event.get_raw_data()

		if et != "internet_access":
			return False
		if ed != True:
			return False
		return True

