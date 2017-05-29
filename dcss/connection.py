import paramiko
import time
import pexpect
import datetime
import logging

log = logging.getLogger(__name__)

SPLITTER = '`~`'
COMMAND = 'BOT_CMD:'
UTF8 = 'utf-8'

class LocalConnection():

    def __init__(self):
        super().__init__()
        self.isWaitingForResponse = False
        self.process = None
        self.delay = 0.25
        self.validConnection = False
        self.lastOutput = ''

    def connect(self):
        self.process = pexpect.spawn(
                "crawl",
                timeout=self.delay)
        self.validConnection = self.process.isalive()
        log.info("LocalConnection connected:" + str(self.validConnection))
        return self.validConnection

    def crawl_login(self):
        # in this case no login is required
        log.info("LocalConnection logged in")
        return self.get_output()

    def disconnect(self):
        self.process.terminate()
        self.validConnection = False
        log.info("LocalConnection disconnecting")

    def get_output(self):
        done = False
        onceMore = True
        output = ''
        while not done:
            match = self.process.expect(['\\x1b\[40m', pexpect.TIMEOUT])
            if match == 0:
                buf = self.process.before
                if isinstance(buf, bytes):
                    buf = buf.decode()
                output += buf
                onceMore = True
            elif match == 1:
                if not onceMore:
                    done = True
                else:
                    onceMore = False
        self.lastOutput = output
        log.debug("LocalConnection received: " + repr(self.lastOutput))
        return output

    def send_command(self, command, addNewline):
        log.debug("LocalConnection sending command: " + str(command))
        if(command):
            self.isWaitingForResponse = True
            self.process.send(command)

        if(addNewline):
            self.isWaitingForResponse = True
            self.process.sendline("\r")
        time.sleep(self.delay)

        return self.get_output()


class RemoteConnection():

    def __init__(self, crawlLoginName, crawlLoginPassword):
        super().__init__()
        self.isWaitingForResponse = False
        self.connectionString = "crawl.akrasiac.org"
        self.sshUsername = "joshua"
        self.sshPassword = "joshua"
        self.delay = 0.5
        self.username = crawlLoginName
        self.password = crawlLoginPassword
        self.sshClient = None
        self.sshChannel = None
        self.bufferSize = 4096
        self.validConnection = False
        self.lastOutput = ''

    def connect(self):
        self.sshClient = paramiko.SSHClient()
        self.sshClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.sshClient.connect(
                self.connectionString,
                username=self.sshUsername,
                password=self.sshPassword)
        self.sshChannel = self.sshClient.invoke_shell()
        #TODO:figure a way to verify connecting was successful
        self.validConnection = True
        log.info("RemoteConnection connected: " + str(self.validConnection))
        return self.validConnection

    def crawl_login(self):
        # navigate the crawl login commands
        self.send_command('L', False)
        self.send_command(self.username, True)
        self.send_command(self.password, True)
        # select trunk branch
        self.send_command('T', False)
        result = self.send_command('P', False)
        log.info("RemoteConnection logged in")
        return result

    def disconnect(self):
        if self.sshClient:
            self.sshClient.close()
        self.validConnection = False
        log.info("RemoteConnection disconnected")

    def get_output(self):
        output = ''
        while(self.sshChannel.recv_ready()):
            if(self.isWaitingForResponse):
                self.isWaitingForResponse = False
            buffer = self.sshChannel.recv(self.bufferSize)
            if(len(buffer) != 0):
                output += buffer.decode(UTF8)
        self.lastOutput = output
        log.debug("RemoteConnection received: " + repr(self.lastOutput))
        return output

    def send_command(self, command, addNewline):
        log.debug("RemoteConnection sending command: " + str(command))
        if(command):
            self.isWaitingForResponse = True
            self.sshChannel.send(command)
            time.sleep(self.delay)

        if(addNewline):
            self.isWaitingForResponse = True
            self.get_output()
            self.sshChannel.send('\n')
            time.sleep(self.delay)

        return self.get_output()
