#!/usr/bin/env python
#       ttrs.py
#
#       Copyright 2010 Denis Deryabin <denis.deryabin@gmail.com>
#
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.
doc="""
##############################################################################
# Tester's Tools Radius server
# Author: Denis Deryabin <denis.deryabin@gmail.com>
##############################################################################
"""
print(doc)
##############################################################################
# Import section:
##############################################################################
import sys
import time
import Queue
import threading
from pyrad import dictionary
from pyrad import packet
from pyrad import server
from pyrad import client
##############################################################################
# Server configuration:
##############################################################################
class genericConfiguration:
    supportedOptions = {
        # Option : Default value
        "PODRequest" : ["Accounting", "Authentication"],
        "PODTimeout" : 10,
        "AuthUsers"  : ["ru9990611"],
        "AccUsers"   : ["ru9990611"],
        "PODSendFor" : ["ru9990611"],
        "CustomAuthAcceptAttributes" : {},
        "CustomAuthRejectAttributes" : {},
        "CustomAccountingAttributes" : {},
        "server_authport" : 9812,
        "server_acctport" : 9813,
        "server_ip"       : "192.168.128.61",
        "server_secret"   : "123",
        "remote_ips"      : [],
        "loggingTo"       : ["screen"],#["file", "screen"],
        "logFileName"     : "radius_log.txt",
        "configSyncTimeout" : 10
    }
    def __init__(self):
        # Setup default options
        for opt, val in self.supportedOptions.items():
            log("Set default value for option:'%s' = '%s'" % (opt, val), self)
            setattr(self, opt, val)
        # Create synchronization thread
        syncThr = threading.Thread(target=self.repeater)
        syncThr.start()

    def synchronizeOptions(self):
        try:
            import config
            reload(config)
            for opt in dir(config):
                if opt not in self.supportedOptions:
                    if opt not in ["__builtins__",
                                   "__doc__",
                                   "__file__",
                                   "__name__",
                                   "__package__"]:
                        log("Unsupported option: %s, skip it." % opt, self)
                    continue
                selfOptionValue = getattr(self, opt, None)
                val = getattr(config,opt, None)
                if selfOptionValue != val:
                    log("Update option:%s with value '%s'" % (opt, val), self)
                    setattr(self, opt,val)
        except ImportError, e:
            log ("[ERROR] Unable load configuration file! Error message is '%s'" % (e), self)
            sys.exit(1)
        #except:
        #    log ("[ERROR] Unable synchronize all options! Error message is '%s'", self)
        #    sys.exit(1)

    def repeater(self):
        while True:
            self.synchronizeOptions()
            log("Configuration synchronized.", self)
            time.sleep(self.configSyncTimeout)

##############################################################################
# Code section:
##############################################################################

class logger():
    def __init__(self, dst=["screen"], filename=""):
        self.fout = None
        self.dst = dst
        if "file" in dst:
            try:
                self.fout = open(filename, "a")
            except:
                self.fout = None
                out("ERROR: Can't open file for logging.")
    def updateSetup(self, dst=["screen"], filename=""):
        self.fout = None
        self.dst = dst
        if "file" in dst:
            try:
                if self.fout:
                    self.fout.close()
            except:
                out("ERROR: Unable close old log file.")
            try:
                self.fout = open(filename, "a")
            except:
                self.fout = None
                out("ERROR: Can't open file for logging.")
    def out(self, str):
        str = "[%s]: %s" % (time.time(), str)
        if "file" in self.dst:
            self.fout.write(str+"\n")
        if "screen" in self.dst:
            print(str)
    def __call__(self, str, who=None):
        self.out("[%s] %s"%(who.__class__.__name__, str))

    def logFormatPacket(self, pkt, who=None):
        res = "\n"
        for k,v in pkt.items():
            for i in v:
                res += "\t%s:%s\n" % (str(pkt._DecodeKey(k)),str(i))
        self.out("[%s] %s"%(who.__class__.__name__, res))
#=============================================================================
# Radius Server class
#=============================================================================
class radiusServer(server.Server):
    accCounter = 0
    authCounter = 0
    KikedCalls = {}
    callsForPod = {} # {confId:{startTime:""},}
    podQueue = Queue.Queue()

    def startThreading(self):
        self.createThread()

    def createThread(self):
        # create thread
        thr = threading.Thread(target=self.podProcessor)
        thr.start()

    def podProcessor(self):
        call = None
        while True:
            try:
                # Wait for data
                call = self.podQueue.get_nowait()
            except Queue.Empty:
                # sleep
                time.sleep(0.2)
                continue
            #print "Receive call from queue:%s"%str(call["confid"])
            if (time.time()-call["startTime"]) > config.PODTimeout:
                # Timeout occured
                # Send POD for this call
                reply = self.CreateReplyPacket(call["packet"])
                reply.code = packet.DisconnectRequest
                reply["h323-conf-id"] = "%s" % call["confid"]
                log("Send POD for confId:[%s]; %s calls in PODs queue."% (call["confid"],len(self.podQueue)), self)
                self.SendReplyPacket(call["packet"].fd, reply)
                # tack complete
                self.podQueue.task_done()
            else:
                # It's not time for death of this call
                # put call back to the queue
                self.podQueue.put(call)
            # sleep
            time.sleep(0.2)

    def _HandleAuthPacket(self, pkt):
        self.authCounter=self.authCounter+1
        log("Received Auth request #%s" % self.authCounter, self)
        log("KikedCalls storage length: %s" % len(self.KikedCalls), self)
        log("Request:", self)
        log.logFormatPacket(reply)
        server.Server._HandleAuthPacket(self, pkt)
        UserName = pkt.get("User-Name", "None")[0]
        ConfId = pkt.get("h323-conf-id",[None])[0]
        reply=self.CreateReplyPacket(pkt)
        if UserName in config.AuthUsers:
            # Add custom attribute into response for this user
            for attr,val in config.CustomAuthAcceptAttributes.get(UserName,{}).items():
                reply[attr] = str(val)
            reply.code=packet.AccessAccept
            log("Send AccessAccept.", self)
        else:
            # Add custom attribute into response for this user
            for attr,val in config.CustomAuthRejectAttributes.get(UserName,{}).items():
                reply[attr] = str(val)
            reply.code=packet.AccessReject
            log("Send AccessReject.", self)

        log("Response:", self)
        log.logFormatPacket(reply)
        self.SendReplyPacket(pkt.fd, reply);

        if (UserName in config.PODSendFor) and ("Authentication" in config.PODRequest):
            log("Put call into podQueue.", self)
            self.podQueue.put({"startTime":time.time(),
                               "packet":pkt,
                               "confid":ConfId
                               })

    def _HandleAcctPacket(self, pkt):
        self.accCounter = self.accCounter+1
        log("Received Acc request #%s" % self.accCounter, self)
        log("Request:", self)
        log.logFormatPacket(reply)
        server.Server._HandleAcctPacket(self, pkt)
        UserName = pkt.get("User-Name", "None")[0]
        ConfId = pkt.get("h323-conf-id",[None])[0]
        reply=self.CreateReplyPacket(pkt)
        # Add custom attribute into response for this user
        for attr,val in config.CustomAccountingAttributes.get(UserName,{}).items():
            reply[attr] = str(val)
        log("Response:", self)
        log.logFormatPacket(reply)
        self.SendReplyPacket(pkt.fd, reply);
        if (UserName in config.PODSendFor) and ("Accounting" in config.PODRequest):
            log("Put call into podQueue.", self)
            self.podQueue.put({"startTime":time.time(),
                               "packet":pkt,
                               "confid":ConfId
                               })

    def _onPacket(self, pkt):
        log( "Incoming packet.", self)
        return pkt

#=============================================================================
# Main()
#=============================================================================
#class TestRadius:
#    Task
#    def __init__(self):
#        pass
#    def main(self):
#        pass
def main():
    try:
        log("Create server instance")
        s = radiusServer(dict=dictionary.Dictionary("dictionaries/dictionary", "dictionaries/dictionary.cisco", "dictionaries/dictionary.mera"), authport=config.server_authport, acctport=config.server_acctport)
        for remoteServer in config.remote_ips:
            log("Server IP:%s\tadd client IP:%s, secret:%s" %(config.server_ip, remoteServer, config.server_secret))
            s.hosts[remoteServer] = server.RemoteHost(remoteServer, config.server_secret, config.server_ip)
        s.BindToAddress("")
        log("Strart threading")
        s.startThreading()
        log("Run server")
        s.Run()
    except KeyboardInterrupt:
        print "KeyboardInterrupt!"
        sys.exit(1)
    except:
        print "Unexpected error!"
        sys.exit(1)

if __name__ == "__main__":
    log = logger()
    config = genericConfiguration()
    log.updateSetup(config.loggingTo, config.logFileName)
    main()
