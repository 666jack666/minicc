from Tkinter import *
from ttk import *
import socket,traceback,getopt,sys,string,struct,threading
import thread
import time

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

class ChatServer(Frame):

    def __init__(self, root):
        Frame.__init__(self, root)
        self.root = root
        self.initUI()
        self.serverSoc = None
        self.serverStatus = 0
        self.buffsize = 1024
        self.mulServerSoc=None
        self.mulAddr=('255.255.255.255',12346)
        self.serverTcpSoc=None

        self.allClients = {}
        self.counter = 0

    def initUI(self):
        self.root.title("chat server")
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
        serverLabel = Label(ipGroup, text="Set: ")
        self.nameVar = StringVar()
        self.nameVar.set("SVR")
        nameField = Entry(ipGroup, width=10, textvariable=self.nameVar)
        self.serverIPVar = StringVar()
        self.serverIPVar.set("127.0.0.1")
        serverIPField = Entry(ipGroup, width=15, textvariable=self.serverIPVar)
        self.serverPortVar = StringVar()
        self.serverPortVar.set("8090")
        serverPortField = Entry(ipGroup, width=5, textvariable=self.serverPortVar)
        serverSetButton = Button(ipGroup, text="Set", width=10, command=self.handleSetServer)
        serverLabel.grid(row=0, column=0)
        nameField.grid(row=0, column=1)
        serverIPField.grid(row=0, column=2)
        serverPortField.grid(row=0, column=3)
        serverSetButton.grid(row=0, column=4, padx=5)

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
        if self.serverSoc != None:
            self.serverSoc.close()
            self.serverSoc = None
            self.serverStatus = 0

        self.serveraddr = (self.serverIPVar.get().replace(' ', ''), int(self.serverPortVar.get().replace(' ', '')))
        try:
            self.serverSoc=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.serverSoc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.serverSoc.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.mulServerSoc=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
            self.mulServerSoc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.mulServerSoc.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.mulServerSoc.bind((self.serverIPVar.get().replace(' ', ''),int(self.serverPortVar.get().replace(' ', ''))+1))

            self.serverTcpSoc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.serverTcpSoc.bind((self.serverIPVar.get().replace(' ', ''),int(self.serverPortVar.get().replace(' ', ''))+2))
            self.serverTcpSoc.listen(15)
            self.serverSoc.bind(self.serveraddr)

            print "Listen on the port %s......"%self.serverPortVar.get().replace(' ', '')
            self.serverStatus=1
            thread.start_new_thread(self.recvMsg, ())
            thread.start_new_thread(self.recvTcpCon, ())
            #thread.start_new_thread(self.broadcastMsg, ())
            self.name = self.nameVar.get().replace(' ','')
            if self.name == '':
                self.name = "%s:%s" % self.serveraddr

        except:
            traceback.print_exc()
            self.setStatus("Error setting up server")

    def handleSendChat(self):
        if self.serverStatus == 0:
            self.setStatus("Set client address first")
            return
        msg = self.chatVar.get().replace(' ', '')
        if msg == '':
            print "please input msg"
        self.addChat("me", msg)

    def addChat(self, server, data):
        for client in self.allClients.keys():
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
            client.send(signalingtest)
            self.updateMsg("me", str(data))
        #self.mulServerSoc.sendto(msg, self.mulAddr)
        #print "client=%s,msg=%s"%server,msg
    def updateMsg(self,cip,msg):
        self.receivedChats.config(state=NORMAL)
        self.receivedChats.insert("end", cip + ": " + msg + "\n")
        self.receivedChats.config(state=DISABLED)
    def broadcastMsg(self):
        while(1):
            try:
                #print"broadcast"
                self.mulServerSoc.sendto("i am srv", self.mulAddr)
                time.sleep(2)
            except:
                print "error"
                break;
    def recvMsg(self):
        while 1:
            try:
                data, addr = self.serverSoc.recvfrom(self.buffsize)
                print type(data)
                print type(addr)

                if data == 'select':
                    print'right'
                    ipaddr = '127.0.0.1'
                    serial = 111111
                    port = 8092
                    code = 2
                    buffer = struct.pack("!4sIHH", socket.inet_aton(ipaddr), serial, port, code)
                    print addr
                    self.serverSoc.sendto(buffer,addr)
                    self.updateMsg("me", "success")

                self.updateMsg(str(addr),str(data))
                print 'receive data : ', data
                print 'receive data : ', addr
            except:
                traceback.print_exc()
                break;
    def recvTcpCon(self):
        while 1:
            try:
                client, address = self.serverTcpSoc.accept()
                print address
                self.allClients[client] = self.counter
                self.counter += 1
                thread.start_new_thread(self.jonnyS, (client, address))
            except:
                pass
    def setStatus(self, msg):
        print "%s"%msg

    def jonnyS(self,client, address):
        try:
            client.settimeout(500);
            signaling = client.recv(2048);
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
            # **************
            self.updateMsg(str(address), str(data))
            # print struct.unpack("!H4s2I",buf)
            # id, tag, version, count = struct.unpack("!H4s2I",buf);
            # print ("id=%d"%(version))
            # print ("id=%d,tag=%s,version=%d,count=%d"%(id,tag,version,count));
            # client.send('ok')
        except socket.timeout:
            print 'time out'

def main():
    root = Tk()
    app = ChatServer(root)
    root.mainloop()


if __name__ == '__main__':
    main()