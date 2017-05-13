import paramiko
import time
import pexpect
import datetime

SPLITTER = '`~`'
COMMAND = 'BOT_CMD:'
UTF8 = 'utf-8'


class AbstractCrawlConnection:

    def __init__(self):
        self.isWaitingForResponse = False
        self.delay = 0.5
        self.validConnection = False
        self.lastOutput = ''

    def connect(self):
        return False

    def crawlLogin(self):
        pass

    def disconnect(self):
        pass

    def get_output(self):
        pass

    def send_command(self):
        pass

    def quit(self):
        self.sendCommand(chr(17), False)
        self.sendCommand('yes', True)


class LocalCC(AbstractCrawlConnection):

    def __init__(self):
        super().__init__()
        self.process = None
        self.logfile = None
        self.delay = 0.25

    def connect(self):
        self.logfile = open(
                'crawlbot_' + datetime.datetime.now().strftime(
                    "%Y-%m-%d_%H-%M-%S") + ".clg", "w")
        self.process = pexpect.spawn(
                "crawl",
                timeout=self.delay,
                logfile=self.logfile.buffer)
        self.validConnection = self.process.isalive()
        if(self.validConnection):
                self.getOutput()
        return self.validConnection

    def crawl_login(self):
        # in this case no login is required
        # just select race/class
        self.sendCommand('\r', False)
        self.sendCommand('n', False)
        self.sendCommand('a', False)
        return self.sendCommand('c', False)

    def disconnect(self):
        self.process.terminate()
        self.validConnection = False

    def get_output(self):
        done = False
        onceMore = True
        output = ''
        while(not done):
            match = self.process.expect(['\\x1b\[40m', pexpect.TIMEOUT])
            if(match == 0):
                buf = self.process.before
                if(isinstance(buf, bytes)):
                    buf = buf.decode()
                output += buf
                if(not onceMore):
                    onceMore = True
            elif(match == 1):
                    if(not onceMore):
                            done = True
                    else:
                            onceMore = False
        self.lastOutput = output
        return output

    def send_command(self, command, addNewline):
        if(command):
            self.isWaitingForResponse = True
            logStringself = SPLITTER + COMMAND + command
            self.buffer.write(logStringself.encode(UTF8))
            self.process.send(command)

        if(addNewline):
            self.isWaitingForResponse = True
            self.process.sendline("\r")
        time.sleep(self.delay)

        return self.getOutput()


class RemoteCC(AbstractCrawlConnection):

    def __init__(self, crawlLoginName, crawlLoginPassword):
        super().__init__()
        self.connectionString = "crawl.akrasiac.org"
        self.sshUsername = "joshua"
        self.sshPassword = "joshua"
        self.username = crawlLoginName
        self.password = crawlLoginPassword
        self.sshClient = None
        self.sshChannel = None
        self.bufferSize = 4096

    def connect(self):
        self.sshClient = paramiko.SSHClient()
        self.sshClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.sshClient.connect(
                self.connectionString,
                username=self.sshUsername,
                password=self.sshPassword)
        self.sshChannel = self.sshClient.invoke_shell()
        self.validConnection = True

        return True

    def crawl_login(self):
        # navigate the crawl login commands
        self.sendCommand('L', False)
        self.sendCommand(self.username, True)
        self.sendCommand(self.password, True)
        # select trunk branch
        self.sendCommand('T', False)
        return self.sendCommand('P', False)

    def disconnect(self):
        if self.sshClient:
            self.sshClient.close()
        self.validConnection = False

    def get_output(self):
        output = ''
        while(self.sshChannel.recv_ready()):
                if(self.isWaitingForResponse):
                        self.isWaitingForResponse = False
                buffer = self.sshChannel.recv(self.bufferSize)
                if(len(buffer) != 0):
                        output += buffer.decode(UTF8)
        return output

    def send_command(self, command, addNewline):
        if(command):
            self.isWaitingForResponse = True
            self.sshChannel.send(command)
            time.sleep(self.delay)

        if(addNewline):
            self.isWaitingForResponse = True
            self.getOutput()
            self.sshChannel.send('\n')
            time.sleep(self.delay)

        return self.getOutput()
