from scale_client.sensors.threaded_virtual_sensor import ThreadedVirtualSensor

from urllib2 import urlopen
import json
import time
import logging
log = logging.getLogger(__name__)

class GeoIPVirtualSensor(ThreadedVirtualSensor):
	"""
	This virtual sensor connects to Internet,
	determines the public IP address of current system,
	and find the latitude and longitude of the corresponding IP address.

	It doesn't need to be accurate so far.
	"""
	GEO_IP_LOOKUP_URL = "http://ip-api.com/json"

	def __init__(self, broker, device=None, interval=60, exp=600, mock_ip=None, **kwargs):
		super(GeoIPVirtualSensor, self).__init__(broker, device=device, interval=interval, **kwargs)
		self._exp = exp
		self._lookup_url = GeoIPVirtualSensor.GEO_IP_LOOKUP_URL
		if mock_ip is not None:
			if type(mock_ip) != type("") and type(mock_ip) != type(u""):
				raise TypeError
			self._lookup_url += "/" + mock_ip

	DEFAULT_PRIORITY = 9

	def get_type(self):
		return "geo_ip"

	def read_raw(self):
		try:
			ret = urlopen(self._lookup_url).read().strip()
			obj = json.loads(ret)
		except Exception:
			return None
		if type(obj) != type({}):
			return None
		if not "lat" in obj or not "lon" in obj or not "query" in obj:
			return None
		raw = {
				"lat": obj["lat"],
				"lon": obj["lon"],
				"ip": obj["query"],
				"exp": time.time() + self._exp
			} # Expire in 10 minutes
		return raw

	def policy_check(self, data):
		raw = data.get_raw_data()
		if raw is None or type(raw) != type({}):
			return False
		return True
