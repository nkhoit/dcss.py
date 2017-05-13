import CrawlConnection as cc


class Client:
    def __init__(self, crawlConnection):
        self.__conn = crawlConnection
        self.__buffer = ""
        if(self.__conn and not self.__conn.validConnection):
            if(self.__conn.connect()):
                self.__conn.crawl_login()

    def send_command(self, command, addNewLine=False):
        self.buffer = self.conn.send_command(command, addNewLine)
        return self.buffer


def test():
    client = Client(cc.RemoteCC("username", "password"))
    print(client.buffer)
    while True:
        print(client.send_command(input()))
