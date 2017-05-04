import crawlConnection as cc

class Client:
	def __init__(self, crawlConnection):
		self.conn = crawlConnection
		self.buffer = ""
		if(self.conn and not self.conn.validConnection):
			if(self.conn.connect()):
				self.conn.crawlLogin()
			else:
				raise StandardError("Could not connect provided crawlConnection")
	
	def sendCommand(self, command, addNewLine=False):
		self.buffer = self.conn.sendCommand(command, addNewLine)
		return self.buffer


def test():
	client = Client(cc.RemoteCC("username", "password"))
	print(client.buffer)
	while True:
		print(client.sendCommand(input()))