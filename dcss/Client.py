import crawlConnection as cc


class Client:
    def __init__(self, crawlConnection):
        self.__conn = crawlConnection
        self.__buffer = ""
        if(self.__conn and not self.__conn.validConnection):
            if(self.__conn.connect()):
                self.__conn.crawlLogin()

    def send_command(self, command, addNewLine=False):
        self.buffer = self.conn.selfendCommand(command, addNewLine)
        return self.buffer


def test():
    client = Client(cc.RemoteCC("username", "password"))
    print(client.buffer)
    while True:
        print(client.sendCommand(input()))
