from task_schedule import TaskItem
from scale_client.core.sensed_event import SensedEvent

class NoTask(TaskItem):
	def __init__(self):
		TaskItem.__init__(self)
	
	def on_start(self):
		evtls = []
		return evtls
	
	def on_complete(self):
		evtls = []
		evt_0 = SensedEvent(
				sensor="task",
				priority=8,
				data={"event": "debug_text", "value": "No task completed."}
			)
		evtls.append(evt_0)
		return evtls
	
	def listener_check(self, event):
		return True

