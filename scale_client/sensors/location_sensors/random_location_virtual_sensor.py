from scale_client.sensors.location_sensors.fake_location_virtual_sensor import FakeLocationVirtualSensor

import time
import random
#import copy
import logging
log = logging.getLogger(__name__)

class RandomLocationVirtualSensor(FakeLocationVirtualSensor):
	def __init__(self, broker, device=None, interval=1, exp=2, lat_mean=0.0, lon_mean=0.0, alt_mean=0.0, lat_var=0.0, lon_var=0.0, alt_var=0.0, fail_time=0, alt_fail_time=0, fail_p=0.0, alt_fail_p=0.0):
		super(RandomLocationVirtualSensor, self).__init__(broker, device=device, interval=interval, exp=exp, lat=lat_mean, lon=lon_mean, alt=alt_mean)
		self._lat_var = lat_var
		self._lon_var = lon_var
		self._alt_var = alt_var
		self._fail_time = fail_time
		self._alt_fail_time = alt_fail_time
		self._fail_p = fail_p
		self._alt_fail_p = alt_fail_p
		self._fixed_time = None
		self._alt_fixed_time = None
		random.seed()

	def get_type(self):
		return "fake_location"

	def read_raw(self):
		raw = None
		if self._fixed_time is None:
			self._fixed_time = time.time() + self._fail_time
			self._alt_fixed_time = None
		elif self._fixed_time > time.time():
			self._alt_fixed_time = None
		else: # Fixed
			raw = super(RandomLocationVirtualSensor, self).read_raw()
			raw["lat"] += random.uniform(-self._lat_var, self._lat_var)
			raw["lon"] += random.uniform(-self._lon_var, self._lon_var)
			if self._alt_fixed_time is None:
				self._alt_fixed_time = time.time() + self._alt_fail_time
				raw["alt"] = float("nan")
			elif self._alt_fixed_time > time.time():
				raw["alt"] = float("nan")
			else: # Altitude fixed
				raw["alt"] += random.uniform(-self._alt_var, self._alt_var)
				if random.random() < self._alt_fail_p:
					self._alt_fixed_time = None
			if random.random() < self._fail_p:
				self._fixed_time = None
		return raw

	def policy_check(self, data):
		raw = data.get_raw_data()
		if type(raw) != type({}):
			return False
		return True
