# -*- coding: utf-8 -*-
##############################################################################
# Configuration file for TTRadiusServer
##############################################################################
#if __name__ == '__main__': print "It's not a script!!"
##############################################################################
# DISCONNECT REQUEST (POD) OPTIONS:
##############################################################################
#-----POD Section
# ANIS to send POD:
PODSendFor=["ru9990611"]
# POD after request:
PODRequest = ["Accounting", "Authentication"]
# POD timeout. Will be used for all users:
PODTimeout=10
##############################################################################
# AUTHENTICATION OPTIONS:
##############################################################################
# The list of the users for Authentication
AuthUsers=["ru9990611"]
# This attributes will be added into the responce
# for accepter authetication and for rejected authentication
# example:
#   CustomAuthAcceptAttributes = {
#            "Mark" : {"Cisco-AVPAir":"h323-ivr-in=color:blue",
#                      "xpgk-request-type": "1"
#                    },
#            "Anna" : {"Cisco-AVPAir":"h323-ivr-in=day:monday"}
#        }
#   will add attributes "Asco-AVPair" with value "h323-ivr-in=color:blue"
#   and "xpgk-request-type" with walue "1" for Mark. For Anna will be added
#   attribute "Cisco-AVPAir" with value "h323-ivr-in=day:monday".
# NOTE: For External Routing you can specify mandatory attributest here as you
#       wish.
CustomAuthAcceptAttributes = {
    "ru9990611" : {"Cisco-AVPAir":"h323-ivr-in=color:blue", "xpgk-request-type": "1"},
    "Anna" : {"Cisco-AVPAir":"h323-ivr-in=day:monday"}
}
CustomAuthRejectAttributes={}
##############################################################################
# ACCOUNTING OPTIONS:
##############################################################################
# The list of the users for Accounting
# For format of the options please see "AUTHENTICATION OPTIONS" section
AccUsers=["ru9990611"]
CustomAccountingAttributes={}
##############################################################################
# SERVER OPTIONS:
##############################################################################
server_authport=9812
server_acctport=9813
server_ip = "192.168.128.61"
# Pass phrase for this radius server
server_secret = "123"
# The list of IP addresses of client for this Radius server
remote_ips = [  "192.168.131.12",
                "192.168.129.50",
                "192.168.129.192",
                "192.168.130.71",
                "192.168.131.5",
                "192.168.130.148",
                "192.168.130.110",
                "192.168.130.150",
                "192.168.131.38"
                ]

# logging options. "screen" or "file" options available
#loggingTo = ["file", "screen"]
loggingTo = ["screen"]
logFileName = "radius_log.txt"
configSyncTimeout = 10
