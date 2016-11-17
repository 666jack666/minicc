from Tkinter import *
from ttk import *
import getopt,socket,sys,string,struct,traceback
import thread


#struct MiniccInfo
#{     unsigned int ipaddr;
#      unsigned int serial:
#      unsigned short port:
#      unsigned short code;
#}

#struct SingnalingHeader
#{     unsigned char version:4
#      unsigned char len:4
#      unsigned char protocol:8
#      unsigned short totallen:16
#      unsigned short checksum:16
#      unsigned int source:32
#      unsigned int destination:32
#}

class ChatClient(Frame):

    def __init__(self, root):
        Frame.__init__(self, root)
        self.root = root
        self.initUI()
        self.clientSoc = None
        self.clientStatus = 0
        self.buffsize = 1024
        self.cHost = '127.0.0.1'
        self.cPort = 12346
        self.serveraddr=None
        self.mulAddr = ('255.255.255.255', 8090)
        self.clientTcpSoc=None
        self.ipaddrstr=None


    def initUI(self):
        self.root.title("chat client")
        ScreenSizeX = self.root.winfo_screenwidth()
        ScreenSizeY = self.root.winfo_screenheight()
        self.FrameSizeX = 800
        self.FrameSizeY = 600
        FramePosX = (ScreenSizeX - self.FrameSizeX) / 2
        FramePosY = (ScreenSizeY - self.FrameSizeY) / 2
        self.root.geometry("%sx%s+%s+%s" % (self.FrameSizeX, self.FrameSizeY, FramePosX, FramePosY))
        self.root.resizable(width=False, height=False)

        padX = 10
        padY = 10
        parentFrame = Frame(self.root)
        parentFrame.grid(padx=padX, pady=padY, stick=E + W + N + S)

        ipGroup = Frame(parentFrame)
        clientLabel = Label(ipGroup, text="Set: ")
        self.nameVar = StringVar()
        self.nameVar.set("CLT")
        nameField = Entry(ipGroup, width=10, textvariable=self.nameVar)
        self.clientIPVar = StringVar()
        self.clientIPVar.set("127.0.0.1")
        clientIPField = Entry(ipGroup, width=15, textvariable=self.clientIPVar)
        self.clientPortVar = StringVar()
        self.clientPortVar.set("8090")
        clientPortField = Entry(ipGroup, width=5, textvariable=self.clientPortVar)
        clientSetButton = Button(ipGroup, text="start connect ...", width=50, command=self.handleSetServer)
        #clientLabel.grid(row=0, column=0)
        #nameField.grid(row=0, column=1)
        #clientIPField.grid(row=0, column=2)
        #clientPortField.grid(row=0, column=3)
        clientSetButton.grid(row=0, column=4, padx=5)

        readChatGroup = Frame(parentFrame)
        self.receivedChats = Text(readChatGroup, bg="white", width=60, height=30, state=DISABLED)
        self.receivedChats.grid(row=0, column=0, sticky=W + N + S, padx=(0, 10))

        writeChatGroup = Frame(parentFrame)
        self.chatVar = StringVar()
        self.chatField = Entry(writeChatGroup, width=90, textvariable=self.chatVar)
        sendChatButton = Button(writeChatGroup, text="Send", width=10, command=self.handleSendChat)
        self.chatField.grid(row=0, column=0, sticky=W + N + S)
        sendChatButton.grid(row=0, column=1, padx=5)

        ipGroup.grid(row=0, column=0)
        readChatGroup.grid(row=1, column=0)
        writeChatGroup.grid(row=2, column=0, pady=10)

    def handleSetServer(self):
        if self.clientSoc != None:
            self.clientSoc.close()
            self.clientSoc = None
            self.clientStatus = 0
        self.serveraddr = (self.clientIPVar.get().replace(' ', ''), int(self.clientPortVar.get().replace(' ', '')))
        try:
            self.clientSoc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.clientSoc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.clientSoc.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.clientSoc.bind((self.cHost, self.cPort))
            self.clientSoc.sendto("select", self.mulAddr)
            self.clientStatus = 1
            print "Looking for replies........"
            thread.start_new_thread(self.recvMsg, ())
            self.name = self.nameVar.get().replace(' ','')
            if self.name == '':
                self.name = "%s:%s" % self.serveraddr
        except:
            self.setStatus("Error setting up server")

    def handleSendChat(self):
        if self.clientStatus == 0:
            self.setStatus("Set client address first")
            return
        msg = self.chatVar.get().replace(' ', '')
        if msg == '':
            print "please input msg"
        self.addChat("me", msg)

    def addChat(self, client, data):

        version = 1
        length = 14
        protocol = 2
        totallen = None
        checksum = 0
        source = '127.0.0.1'
        destination = '127.0.0.1'

        length = struct.calcsize("!BBHH4s4s")

        vers = version << 4
        verlen = vers + length
        datalen = len(data)
        totallen = length + datalen

        signalingtest = struct.pack("!BBHH4s4s" + str(datalen) + "s", verlen, protocol, totallen, checksum,
                                    socket.inet_aton(source), socket.inet_aton(destination), data)
        print  struct.unpack("!BBHH4s4s" + str(datalen) + "s", signalingtest);
        self.clientTcpSoc.send(signalingtest)

        self.updateMsg("me", str(data))
        #self.clientSoc.sendto(msg, self.serveraddr)
        #print "client=%s,msg=%s"%client,msg
    def updateMsg(self,cip,msg):
        self.receivedChats.config(state=NORMAL)
        self.receivedChats.insert("end", cip + ": " + msg + "\n")
        self.receivedChats.config(state=DISABLED)
    def recvMsg(self):
        while 1:
            try:
                print "recvmsg"
                minicc = self.clientSoc.recv(self.buffsize)
                print minicc
                ipaddr, serial, port, code = struct.unpack("!4sIHH", minicc)
                print("%s,%d,%d,%d", socket.inet_ntoa(ipaddr), serial, port, code)

                self.ipaddrstr=socket.inet_ntoa(ipaddr)

                self.clientTcpSoc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.clientTcpSoc.connect((socket.inet_ntoa(ipaddr), port))
                print "client"
                thread.start_new_thread(self.recvTcpMsg, ())

                self.updateMsg(socket.inet_ntoa(ipaddr), "connect")
                print 'receive data : ', minicc
                print 'receive data : ', socket.inet_ntoa(ipaddr)
            except:
                traceback.print_exc()
                break;
    def recvTcpMsg(self):
        while 1:
            try:
                signaling = self.clientTcpSoc.recv(2048);
                # ***************
                start = 0
                stop = struct.calcsize("!BBHH4s4s")
                verlen, protocol, totallen, checksum, source, destination = struct.unpack("!BBHH4s4s",
                                                                                          signaling[start:stop])
                version = verlen >> 4
                len = verlen & 0xF
                data = struct.unpack(str(totallen - len) + "s", signaling[len:totallen])
                print("%c,%c,%c,%d,%d,%s,%s", version, len, protocol, totallen, checksum, socket.inet_ntoa(source),
                      socket.inet_ntoa(destination))

                self.updateMsg(self.ipaddrstr, str(data))
            except:
                print "error"
                break;
    def setStatus(self, msg):
        print "%s"%msg


def main():
    root = Tk()
    app = ChatClient(root)
    root.mainloop()

if __name__ == '__main__':
    main()