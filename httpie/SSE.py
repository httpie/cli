from __future__ import print_function
import httplib

class SSE:
	conn = httplib.HTTPConnection("localhost")
	conn.request("GET", "/sse.php")
	response = conn.getresponse()
	
	def printSseRespose(self):
		while True:
			data = self.response.fp.readline()
			print(data)

sse = SSE()
sse.printSseRespose();
