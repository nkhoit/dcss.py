import connection as con
import fake_terminal as ft


class Client:
    def __init__(self, crawlConnection):
        self.conn = crawlConnection
        self.screen = ft.FakeTerminal()
        if(self.conn and not self.conn.validConnection):
            if(self.conn.connect()):
                self.screen.input(self.conn.crawl_login())

    def send_command(self, command, addNewLine=False):
        s = self.conn.send_command(command, addNewLine)
        self.screen.input(s)
        return s

def test(username, pw):
    client = Client(con.RemoteCC(username, pw))
    if not client.conn.validConnection:
        return
    f = open("testFT.txt", "w")
    print("Begin input...")
    while True:
        i = input()
        f.write("new input:" + i + "\n")
        s = client.send_command(i)
        f.write("new text:" + s + "\n")
        f.write("new screen:\n" + str(client.screen) + "\n")
        print(str(client.screen))

def test2(username, pw):
    return Client(con.RemoteCC(username, pw))
