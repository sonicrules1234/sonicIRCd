#!/usr/bin/env python

# Copyright (c) 2010, Westly Ward
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the sonicIRCd Team nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY Westly Ward ''AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL Westly Ward BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import world, socket, conf, thread, traceback, select, time, fnmatch, shelve, hashlib, random

class sonicIRCd :
    def __init__(self) :
        self.loggedin = False
        self.nshelp = {}
        self.nshelp["ghost"] = """***** \x02NickServ\x02 *****

Help for \x02GHOST\x02:

This command is useful when you are not in control of your nick; it disconnects the nick from the server, allowing you to regain control of it.

When someone changes nicks to your nick, you may disconnect them, or if you hadn't pinged out of the server yet (the official term of a 'ghost'), you may disconnect it.

A ghost is created when the connection between you and the server is closed on your end, but not the server's end.  For this reason for pings.

If a client doesn't ping out, the connection has not closed on the server's end. Server's try to prevent this by sending ping every so often. If you don't respond (ghosts don't respond), it will be disconnected.

    SYNTAX: /msg NickServ GHOST <nick> <password>

    EXAMPLE: /msg NickServ GHOST foo foobar"""
        self.nshelp["group"] = """***** \x02NickServ\x02 *****

Help for \x02GROUP\x02:

This command adds your current nick to your previously registered account.

Only if the nick has not been taken, can you group it.

By grouping a nick to your account, you are giving that nick the same settings and privileges as your original nick.

To group a nick, you must log in to your existing nick first.  You must then /nick to the nick you want to group, and then use the GROUP command.

    SYNTAX: /msg NickServ GROUP

    \x02NOTE:\x02 The limit for grouped nicks per account is currently 10!"""
        self.nshelp["register"] = """***** \x02NickServ\x02 *****

Help for \x02REGISTER\x02:

This command registers your current nick with the NickServ database. Using this on your nick will allow you to receive access in the form of privileges.
Please be sure to remember your password, as it's your only way into accessing the privileges the nick holds.

    SYNTAX: /msg NickServ REGISTER <password> <email>

    EXAMPLE: /msg Nickserv REGISTER hunter2 foo@example.com

    \x02NOTE:\x02 Passwords are case-sensitive. It is recommended to write down your passsword somewhere or use some other method to keep record of it."""
        
        self.nshelp["identify"] = """***** \x02NickServ\x02 *****

Help for \x02IDENTIFY\x02:

This allows you to log into a nick you have previously registered. By logging into a nick, you are granted any privileges it may or may not have.
This command identifies you to ALL SERVICES.

    SYNTAX: /msg NickServ IDENTIFY <password>

    EXAMPLE: /msg NickServ IDENTIFY hunter2

    \x02NOTE:\x02 You may replace IDENTIFY with ID if wanted."""
        self.nshelp["help"] = """*****  \x02NickServ\x02  *****

Nickserv is a service that allows IRC users to \x02register\x02 a nick, so that only they have access to it and any privileges attached to it.
Some commands Nickserv offers are:

    \x02REGISTER\x02       This gives a person full control of the selected nick, but be sure to remember your password!!!
    \x02IDENTIFY\x02       This (corresponding to REGISTER) allows a person to log in as a previously registered nick, and gain any privileges it may have.

For more help on a specific NickServ command, type: /msg NickServ HELP <command>"""

        self.nshelp["info"] = """***** \x02NickServ\x02 *****

Help for \x02IDENTIFY\x02:

This command gives information about a specific user's account such as account name and registration date.

    SYNTAX: /msg NickServ INFO <nick>"""
        self.oshelp = {}
        self.oshelp["vhost"] = "/msg OperServ VHOST <nick> <vhost>"
        self.oshelp["help"] = "Available commands are:\n" + "\n".join(self.oshelp.keys())
        self.cshelp = {}
        self.cshelp["register"] = """*****  \x02ChanServ\x02  *****

Help for \x02REGISTER\x02:

This command can only be used on an unregistered channel, or else it does absolutely nothing!  

Registering a channel gives you the title of "Founder", in which you are in control of how it runs, etc.

The process of registering a channel is very quick and simple, so do not worry.

    SYNTAX: /msg ChanServ REGISTER <channel>

    EXAMPLE: /msg ChanServ REGISTER #foo

    \x02NOTE:\x02 In order to register a channel, you must be in that channel and have ops."""
        self.cshelp["access"] = """*****  \x02ChanServ\x02  *****

Help for \x02ACCESS\x02:

This command is used to grant specific users privileges in a channel from which can be activated through other Chanserv commands.

Access is distributed through flags, with each letter resembling a specific privilege.

When assigning users flags, inserting a "+" before the list of flags indicates giving, where a "-" indicates taking them away.

Another function of ACCESS is being able to see which users have which flags in a certain channel, which can be seen through the LIST subcommand.

The following is a list of currently supported flags and what privleges they give:

    +o = Allows users to op/deop through ChanServ
    +O = Allows for auto opping (Getting opped when you join a channel)
    +v = Allows users to voice/devoice through ChanServ
    +V = Allows for auto voicing (Getting voiced when you join a channel)
    +h = Allows giving/taking half-ops through ChanServ
    +H = Allows for auto half-ops (Getting half-opped when you join a channel)
    +q = Allows changing of users access flags

    SYNTAX: /msg ChanServ ACCESS <channel> LIST|SET [mode] [mask]

    EXAMPLE: /msg ChanServ ACCESS #foo LIST
    EXAMPLE: /msg ChanServ ACCESS #foo SET +O foobar
    EXAMPLE: /msg ChanServ ACCESS #foo SET -O foobar
    EXAMPLE: /msg ChanServ ACCESS #foo SET -h+v foobar

    \x02NOTE\x02: Using ACCESS privileges can only be done while identified, execpt if the privilege in the access list is given to * ."""
        self.cshelp["mode"] = """*****  \x02ChanServ\x02  *****

Help for \x02MODE\x02:

This command is used to implement flags given via ChanServ access.

By using these commands, you are manipulating ChanServ to give/take away user modes.

    SYNTAX: /msg ChanServ MODE <channel> <mode> <nick>

    EXAMPLE: /msg ChanServ MODE #foo +o foobar

    \x02NOTE:\x02 You MUST have sufficient access in the channel to use this command!"""
        self.cshelp["help"] = """*****  \x02ChanServ\x02  *****

ChanServ is a service allowing a user to control a channel after registering it. By registering a channel, you have full access to it, its settings, and other users' access in it.

Here are some of ChanServ's commands with corresponding briefings:

    \x02REGISTER\x02       This quick and easy command gives the person who uses it, foundership of the channel, unless already registered... which then, it will do nothing.

    \x02ACCESS\x02       This command allows access, in the form of channel privileges, to be given or shows a list of the people with access and their privileges on the specified channel.

    \x02MODE\x02       This allows those with access to give/take modes on a channel.

For more help on a specific ChanServ command, type: /msg ChanServ HELP <command>"""
        self.oper = False
        self.operlevel = 0
        self.loggedinas = False
    def onConnect(self, sock, address) :
        self.sock = sock
        self.buffer = ""
        self.remoteport = address[1]
        self.address = address[0]
        self.ip = address[0]
        self.status = ["connected"]
        try :
            self.address = socket.gethostbyaddr(self.address)[0]
        except : pass
        try : self.say("Connection established to %s (%s)" % (self.address, self.ip), "OperServ", conf.service_channel)         
        except : pass
        x = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try :
            x.settimeout(3)
            x.connect((self.ip, 113))
            if self.ssl :
                x.send("%s, %s\n" % (str(self.remoteport), str(conf.sslport)))
            else :
                x.send("%s, %s\n" % (str(self.remoteport), str(conf.port)))
            y = select.select([x], [], [], 3)
            if y[0] != [] :
                z = x.recv(4096)
            else : z = ""
            if z != "" :
                line = z.replace("\r", "").split("\n")[0]
                self.identduser= line.split(":")[3].strip()
                self.identd = True
            else : self.identd = False
            x.close()
        except : self.identd = False
        world.connections[self.sock] = {"host":self.address}
        world.conlist.append(self.sock)
    def parseData(self, data) :
        if data.lower().startswith("post") :
            self.sock.close()
        if conf.debug :
            print "[IN %s] %s" % (self.address, data)
        words = data.split(" ")
        if words[0] == "user" and words[2] == '""' and words[3] == '""' :
            conf.bannedips.append(self.ip)
            
            for client in world.channels[conf.service_channel]["nicks"].keys() :
                self.msg2_send(world.nicks[client]["connection"], "PRIVMSG %s :IP %s has been auto-banned." % (conf.service_channel, self.ip), world.nicks["OperServ"]["longname"])
            self.sock.close()
        lines = data.replace("\r", "").split("\n")
        lines[0] = self.buffer + lines[0]
        self.buffer = lines[-1]
        info = {}
        for line in lines[:-1] :
            info["raw"] = line
            info["words"] = line.split(" ")
            if "user" not in self.status :
                if info["words"][0].upper() == "NICK" :
                    self.on_NICK(info)
                if info["words"][0].upper() == "USER" :
                    self.on_USER(info)
                if info["words"][0].upper() == "PASS" :
                    self.on_PASS(info)
            elif info["words"][0].upper() == "NICK" :
                self.on_NICK(info)
            elif info["words"][0].upper() == "JOIN" :
                self.on_JOIN(info)
            elif info["words"][0].upper() == "PRIVMSG" :
                self.on_PRIVMSG(info)
            elif info["raw"].startswith("PING LAG") :
                self.on_PING_LAG(info)
            elif info["words"][0].upper() == "QUIT" :
                self.on_QUIT(info)
            elif info["words"][0].upper() == "PART" :
                self.on_PART(info)
            elif info["words"][0].upper() == "MODE" :
                self.on_MODE(info)
            elif info["words"][0].upper() == "KICK" :
                self.on_KICK(info)
            elif info["words"][0].upper() == "PING" :
                self.on_PING(info)
            elif info["words"][0].upper() == "NOTICE" :
                self.on_NOTICE(info)
            elif info["words"][0].upper() == "TOPIC" :
                self.on_TOPIC(info)
            elif info["words"][0].upper() == "LIST" :
                self.on_LIST(info)
            elif info["words"][0].upper() == "WHOIS" :
                self.on_WHOIS(info)
            elif info["words"][0].upper() == "INVITE" :
                self.on_INVITE(info)
            elif info["words"][0].upper() == "WHO" :
                self.on_WHO(info)
            elif info["words"][0].upper() in ["NS", "NICKSERV"] :
                self.nickserv(" ".join(info["words"][1:]))
            elif info["words"][0].upper() in ["CS", "CHANSERV"] :
                self.chanserv(" ".join(info["words"][1:]))
            elif info["words"][0].upper() in ["OS", "OPERSERV"] :
                self.operserv(" ".join(info["words"][1:]))            
            elif info["words"][0].upper() == "NAMES" :
                self.on_NAMES(info)
            elif info["words"][0].upper() == "OPER" :
                self.on_OPER(info)
            elif info["words"][0].upper() == "MKPASSWD" :
                self.on_MKPASSWD(info)
            elif info["words"][0].upper() == "VERSION" :
                self.on_VERSION(info)
            elif info["words"][0].upper() == "ISON" :
                pass
            elif info["words"][0].upper() == "KLINE" :
                self.on_KLINE(info)
            elif info["raw"] == "" :
                pass #this is to ignore blank lines, for weird clients
            elif info["words"][0].upper() == "REHASH" :
                if self.isoper() :
                    reload(conf)
                    return "Rehash"
            else : self.msg_send(self.sock, "421 %s %s :Unknown command" % (self.getnick(), info["words"][0]))
        return "No rehash"

    def on_KLINE(self, info) :
        if self.minlevel(4) :
            if nick not in world.services :
                ip = world.instances[world.nicks[self.gettrans(info["words"][1])]["connection"]].ip
                conf.bannedips.append(ip)
                for nick in world.nicks.keys()[:] :
                    if nick not in world.services : 
                        if world.instances[world.nicks[nick]["connection"]].ip == ip :
                            world.nicks[nick]["connection"].close()

    def on_VERSION(self, info) :
        self.msg_send(self.sock, "351 %s sonicIRCd-.0.1 %s :" % (self.getnick(), conf.network_hostname))
        self.msg_send(self.sock, "005 %s CHANTYPES=# PREFIX=(ohv)@%%+ CHANMODES=b,o,h,v, NETWORK=%s CASEMAPPING=rfc1459" % (self.getnick(), conf.network_name))
    def on_MKPASSWD(self, info) :
        if self.minlen(info, 2) :
            self.notice(hashlib.sha512(info["words"][1]).hexdigest(), "OperServ", self.getnick())

    def say(self, message, nick, channel) :
        for client in world.channels[channel]["nicks"].keys() :
            if client != nick :
                self.msg2_send(world.nicks[client]["connection"], "PRIVMSG %s :%s" % (channel, message), world.nicks[nick]["longname"])

    def isoper(self) :
        if self.oper :
            return True
        else : return False

    def minlevel(self, minlev) :
        if self.isoper() :
            if self.operlevel >= minlev :
                return True
            else : return False
        else : return False

    def oshelper(self, words) :
        if len(words) == 1 :
            self.notice(self.oshelp["help"], "OperServ", self.getnick())
        elif len(words) > 1 :
            if self.oshelp.has_key(words[1]) :
                self.notice(self.oshelp[words[1]], "OperServ", self.getnick())
            else :
                self.notice("No such command " + words[1], "OperServ", self.getnick())


    def operserv(self, message) :
        words = message.split(" ")
        if words[0].lower() == "help" :
            self.oshelper(words)
        elif words[0].lower() == "vhost" :
            self.osvhost(words)

    def on_OPER(self, info) :
        if self.minlen(info, 3) :
            if conf.opers.has_key(info["words"][1]) :
                if fnmatch.fnmatch(self.address, conf.opers[info["words"][1]]["hostname"]) :
                    if hashlib.sha512(info["words"][2]).hexdigest() == conf.opers[info["words"][1]]["password"] :
                        self.oper = True
                        self.operlevel = conf.opers[info["words"][1]]["level"]
                        self.notice("You are now an oper.", "OperServ", self.getnick())
                    else : self.notice("Invalid password.", "OperServ", self.getnick())
                else : self.notice("Invalid hostname", "OperServ", self.getnick())
            else : self.notice("No such oper nick", "OperServ", self.getnick())

    def on_NAMES(self, info) :
        if self.minlen(info, 2) :
            channel = self.transchan(info["words"][1])
            self.msg_send(self.sock, "353 %s = %s :%s" % (self.getnick(), channel, self.getnames(channel)))
            self.msg_send(self.sock, "366 %s %s :End of /NAMES list." % (self.getnick(), channel))
    def on_WHO(self, info) :
        allmodes = ["y", "q", "F", "a", "o", "h", "v"]
        modesymbols = {"y":"!", "h":"%", "o":"@", "v":"+", "F":"~", "q":"~", "a":"&"}

        if len(info["words"]) == 1 :
            for nick in world.nicks.keys() :
                if world.nicks[nick]["channels"] != [] :
                    channel = random.choice(world.nicks[nick]["channels"])
                    modelist = ["H"]
                    for mode in allmodes :
                        if mode in world.channels[channel]["nicks"][nick] :
                            modelist.append(modesymbols[mode])
                    modes = "".join(modelist)
                    self.msg_send(self.sock, "352 %s %s %s %s %s %s %s %s %s" % (self.getnick(), channel, world.nicks[nick]["ident"], world.nicks[nick]["host"], conf.network_hostname, nick, modes, "0", world.nicks[nick]["realname"]))
        elif len(info["words"]) == 2 :
            channel = self.transchan(info["words"][1])
            for nick in world.channels[channel]["nicks"].keys() :
                modelist = ["H"]
                for mode in allmodes :
                    if mode in world.channels[channel]["nicks"][nick] :
                        modelist.append(modesymbols[mode])
                modes = "".join(modelist)
                self.msg_send(self.sock, "352 %s %s %s %s %s %s %s %s %s" % (self.getnick(), channel, world.nicks[nick]["ident"], world.nicks[nick]["host"], conf.network_hostname, nick, modes, "0", world.nicks[nick]["realname"]))
        self.msg_send(self.sock, "315 %s :End of /WHO list" % (self.getnick()))

    def on_INVITE(self, info) :
        if self.minlen(info, 3) :
            nick = self.gettrans(info["words"][1])
            channel = self.transchan(info["words"][2])
            if self.meets_req(self.getnick(), channel, ["h", "o"]) :
                self.msg_send(self.sock, "341 %s %s %s" % (self.getnick(), nick, channel))
                for client in world.channels[channel]["nicks"].keys() :
                    if self.meets_req(client, channel, ["h", "o"]) :
                        self.msg_send(world.nicks[client]["connection"], "NOTICE %s :%s invited %s into the channel" % (channel, self.getnick(), nick))
                self.msg2_send(world.nicks[nick]["connection"], "INVITE %s :%s" % (nick, channel), world.nicks[self.getnick()]["longname"])
            elif "g" in world.channels[channel]["flags"] :
                if channel in world.channels.keys() :
                    if self.getnick() in world.channels[channel]["nicks"].keys() :
                        self.msg_send(self.sock, "341 %s %s %s" % (self.getnick(), nick, channel))
                        for client in world.channels[channel]["nicks"].keys() :
                            if self.meets_req(client, channel, ["h", "o"]) :
                                self.msg_send(world.nicks[client]["connection"], "NOTICE %s :%s invited %s into the channel" % (channel, self.getnick(), nick))
                        self.msg2_send(world.nicks[nick]["connection"], "INVITE %s :%s" % (nick, channel), world.nicks[self.getnick()]["longname"])
    def on_WHOIS(self, info) :
        if self.minlen(info, 2) :
            nick = self.gettrans(info["words"][1])
            if nick in world.nicks.keys() and nick not in world.services :
                self.msg_send(self.sock, "311 %s %s %s %s * :%s" % (self.getnick(), nick, world.nicks[nick]["ident"], world.nicks[nick]["host"], world.nicks[nick]["realname"]))
                self.msg_send(self.sock, "319 %s %s :%s" % (self.getnick(), nick, self.getchans(nick)))
                self.msg_send(self.sock, "312 %s %s %s :%s" % (self.getnick(), nick, conf.network_hostname, conf.network_website))
                if world.instances[world.nicks[nick]["connection"]].ssl :
                    self.msg_send(self.sock, "671 %s %s SSL :is using a secure connection" % (self.getnick(), nick))
                if self.nickloggedin(nick) :
                    self.msg_send(self.sock, "320 %s %s :is identified to services" % (self.getnick(), nick))
                    self.msg_send(self.sock, "320 %s %s :is signed on as account %s" % (self.getnick(), nick, self.getaccountname(nick)))
                self.msg_send(self.sock, "318 %s %s :End of /WHOIS list." % (self.getnick(), nick))
            else : self.msg_send(self.sock, "401 %s %s :No such nick/channel" % (self.getnick(), nick))

    def isloggedin(self) :
        if self.loggedin :
            if self.loggedinas == self.getaccountname(self.getnick()) :
                return True
        return False
    
    def nickloggedin(self, nick) :
        if world.instances[world.nicks[nick]["connection"]].loggedin :
            if world.instances[world.nicks[nick]["connection"]].loggedinas == self.getaccountname(nick) :
                return True
        return False

    def chanserv(self, message) :
        words = message.split(" ")
        try : 
            if words[0].lower() == "register" :
                self.csregister(words)
            elif words[0].lower() == "access" :
                self.csaccess(words)
            elif words[0].lower() == "help" :
                self.cshelper(words)
            elif words[0] == "mode" :
                self.csmode(words)
        except :
            traceback.print_exc()
            self.notice("Error.", "ChanServ", self.getnick())
    def cshelper(self, words) :
        if len(words) == 1 :
            self.notice(self.cshelp["help"], "ChanServ", self.getnick())
        elif len(words) > 1 :
            if self.cshelp.has_key(words[1]) :
                self.notice(self.cshelp[words[1]], "ChanServ", self.getnick())
            else :
                self.notice("No such command " + words[1], "ChanServ", self.getnick())

    def csmode(self, words) :
        if len(words) == 4 :
            if self.isloggedin() :
                channel = self.transchan(words[1])
                if words[2].startswith("+") :
                    onoff = True
                else : onoff = False
                modeletter = words[2][1]
                recvr = self.gettrans(words[3])
                if world.chandb.has_key(channel):
                    access = self.csaccessmatch(self.getnick(), channel)
                    if access[0] :
                        if modeletter == "v" and "V" in access[1] :
                            proceed = True
                        elif modeletter == "h" and "H" in access[1] :
                            proceed = True
                        elif modeletter == "o" and "O" in access[1] :
                            proceed = True
                        else : proceed = False
                        if proceed :
                            if onoff :
                                self.chanservsetmode(recvr, channel, True, modeletter)
                            else :
                                self.chanservsetmode(recvr, channel, False, modeletter)
                        else : self.notice("Access denied", "ChanServ", self.getnick())
                    else : self.notice("Access denied", "ChanServ", self.getnick())
                else : self.notice("That channel is not registered. To register it, type: " + self.cshelp["register"], "ChanServ", self.getnick())
            else : self.notice("You need to be logged in to use that command", "ChanServ", self.getnick())
        else : self.notice("Error, please see /msg ChanServ HELP MODE", "ChanServ", self.getnick())
        
    def csaccess(self, words) :
        if len(words) > 4 :
            channel = self.transchan(words[1])
            if self.isloggedin() :
                if channel in world.chandb.keys() :
                    accessmatch = self.csaccessmatch(self.getnick(), channel)
                    if accessmatch[0] :
                        totalprivs = accessmatch[1]
                        print totalprivs
                        if "q" in totalprivs :
                            if words[2].lower() == "set" :
                                account = self.getaccountname(words[4])
                                if account == False :
                                    account = words[4]
                                if not world.chandb[channel]["access"].has_key(account) :
                                    world.chandb[channel]["access"][account] = []
                                    world.chandb.sync()
                                for letter in words[3]:
                                    if letter == "+" : modetype = True
                                    elif letter == "-" : modetype = False
                                    else :
                                        if modetype :
                                            if letter not in world.chandb[channel]["access"][account] :
                                                world.chandb[channel]["access"][account].append(letter)
                                                world.chandb.sync()
                                        elif not modetype :
                                            if letter in world.chandb[channel]["access"][sel] :
                                                world.chandb[channel]["access"][account].remove(letter)
                                                world.chandb.sync()
                                self.notice("Mode %s set successfully." % (words[3]), "ChanServ", self.getnick())
                                if world.chandb[channel]["access"][account] == [] :
                                    del world.chandb[channel]["access"][account]
                                    world.chandb.sync()
                            else : self.notice("Error, please see /msg ChanServ HELP ACCESS", "ChanServ", self.getnick())
                        else : self.notice("Access denied", "ChanServ", self.getnick())
                    else : self.notice("Access denied", "ChanServ", self.getnick())
                else : self.notice("That channel is not registered", "ChanServ", self.getnick())
            else : self.notice("You need to be logged in to use that command", "ChanServ", self.getnick())
        elif len(words) == 3 :
            channel = self.transchan(words[1])
            if words[2].lower() == "list" :
                if channel in world.chandb.keys() :
                    self.notice("\n".join(["%s : %s" % (user, "+" + "".join(world.chandb[channel]["access"][user])) for user in world.chandb[channel]["access"].keys()]), "ChanServ", self.getnick())
                else : self.notice("That channel is not registered", "ChanServ", self.getnick())
            else : self.notice("Error, please see /msg ChanServ HELP ACCESS", "ChanServ", self.getnick())
        else : self.notice("Error, please see /msg ChanServ HELP ACCESS", "ChanServ", self.getnick())
    def csaccessmatch(self, nick, channel) :
        access = []
        user = self.getaccountname(nick)
        if not user : user = nick
        for person in world.chandb[channel]["access"].keys() :
            if world.instances[world.nicks[user]["connection"]].isloggedin() :
                if fnmatch.fnmatch(world.nicks[nick]["longname"].lower(), person.lower()) :
                    access.append(person)
                elif fnmatch.fnmatch(nick.lower(), person.lower()) :
                    access.append(person)
                elif fnmatch.fnmatch(user.lower(), person.lower()) :
                    access.append(person)
            elif person == "*" :
                access.append(person)
        totalprivs = []
        for privlist in access :
            totalprivs += world.chandb[channel]["access"][privlist]            
        if len(access) > 0 :
            return [True, totalprivs]
        else : return [False]

    def csregister(self, words) :
        if len(words) > 1 :
            channel = self.transchan(words[1])
            if not world.chandb.has_key(channel) :
                if self.meets_req(self.getnick(), channel, "o") :
                    if self.isloggedin() :
                        founder = self.getnick()
                        world.chandb[channel] = {"founder":founder, "access":{self.getnick():["q", "v", "h", "o"]}}
                        world.chandb.sync()
                        self.notice("Channel registered successfully", "ChanServ", self.getnick())
                    else : self.notice("You need to be logged in to use that command", "ChanServ", self.getnick())
                else : self.notice("You need to have at least ops in that channel to register it", "ChanServ", self.getnick())
            else : self.notice("That channel is already registered", "ChanServ", self.getnick())
        else : self.notice("Error, please see /msg ChanServ HELP REGISTER", "ChanServ", self.getnick())



    def gettrans(self, nick) :
        if nick.lower() in world.casetrans.keys() :
            return world.casetrans[nick.lower()]
        elif self.transchan2(nick) in world.channels.keys() :
            return self.transchan2(nick)
        else : return nick

    def gettrans2(self, nick) :
        if nick.lower() in world.casetrans.keys() :
            return world.casetrans[nick.lower()]
        else : return nick

    def getaccountname(self, nick) :
        if world.userdb.has_key(self.regtrans(nick)) :
            return world.userdb[self.regtrans(nick)]["account"]
        else : return False
    def isgrouped(self, nick) :
        if world.userdb.has_key(nick) :
            if world.userdb[nick].keys() == ["account"] :
                return True
        return False

    def getchans(self, nick) :
        modes = ["y", "q", "F", "a", "o", "h", "v"]
        modesymbols = {"y":"!", "h":"%", "o":"@", "v":"+", "F":"~", "q":"~", "a":"&"}
        chanlist = []
        for channel in world.nicks[nick]["channels"] :
            symbols = []
            for mode in modes :
                if mode in world.channels[channel]["nicks"][nick] :
                    symbols.append(modesymbols[mode])
            chanlist.append("".join(symbols) + channel)
        return " ".join(chanlist)
    def on_TOPIC(self, info) :
        if self.minlen(info, 3) :
            if ":" in info["words"][2] :
                topic = " ".join(info["words"][2:])[1:]
            else : topic = " ".join(info["words"][2:])
            channel = self.transchan(info["words"][1])
            if self.meets_req(self.getnick(), channel, ["o"]) or "t" not in world.channels[channel]["flags"] :
                world.channels[channel]["topic"]["author"] = self.getnick()
                world.channels[channel]["topic"]["creation"] = str(int(time.time()))
                world.channels[channel]["topic"]["topic"] = topic
                for client in world.channels[channel]["nicks"] :
                    self.msg2_send(world.nicks[client]["connection"], "TOPIC %s :%s" % (channel, topic), world.nicks[self.getnick()]["longname"])

    def on_LIST(self, info) :
        self.msg_send(self.sock, "321 %s Channel :Users Name" % (self.getnick()))
        for channel in world.channels.keys() :
            self.msg_send(self.sock, "322 %s %s %s :%s" % (self.getnick(), channel, str(len(world.channels[channel]["nicks"].keys())), world.channels[channel]["topic"]["topic"]))
        self.msg_send(self.sock, "323 %s :End of /LIST" % (self.getnick()))

    def meets_req(self, nick, channel, modes) :
        if channel in world.channels.keys() :
            if nick in world.channels[channel]["nicks"].keys() :
                for mode in modes :
                    if mode in world.channels[channel]["nicks"][nick] :
                        return True
            else : self.msg_send(self.sock, "401 %s %s :No such nick/channel" % (self.getnick(), nick))                    
        else : self.msg_send(self.sock, "401 %s %s :No such nick/channel" % (self.getnick(), channel))
        return False

    def on_PING(self, info) :
        if self.minlen(info, 2) : self.msg_send(self.sock, "PONG %s" % (info["words"][1]))

    def on_KICK(self, info) :
        if self.minlen(info, 3) :
            channel = self.transchan(info["words"][1])
            recvr = self.gettrans(info["words"][2])
            if len(info["words"]) > 3 :
                    
                if ":" in info["words"][3] :
                    info["words"][3] = info["words"][3][1:]
                reason = " ".join(info["words"][3:])
            else : reason = ""
            if channel in world.channels.keys() :
                if self.meets_req(self.getnick(), channel, ["h", "o"]) and recvr in world.channels[channel]["nicks"].keys() :
                    self.kick(channel, self.getnick(), recvr, reason)
                    if len(world.channels[channel]["nicks"]) == 0 : del world.channels[channel]
    def kick(self, channel, kicker, recvr, reason) :
        for client in world.channels[channel]["nicks"].keys() :
            self.msg2_send(world.nicks[client]["connection"], "KICK %s %s :%s" % (channel, recvr, reason), world.nicks[kicker]["longname"])
        del world.channels[channel]["nicks"][recvr]
        world.nicks[recvr]["channels"].remove(channel)
    def on_MODE(self, info) :
        if len(info["words"]) >= 4 :
            channel = self.transchan(info["words"][1])
            if info["words"][2].startswith("+") :
                onoff = True
            else : onoff = False
            modeletter = info["words"][2]
            recvrs = [self.gettrans(word.replace(":", "")) for word in info["words"][3:]]
            if channel in world.channels.keys() :
                if "o" in world.channels[channel]["nicks"][self.getnick()] :
                    recvr = 0
                    for letter in modeletter:
                        if letter == "+" : modetype = True
                        elif letter == "-" : modetype = False
                        else :
                            if self.meets_req(self.getnick(), channel, "o") and (letter == "b" or recvrs[recvr] in world.channels[channel]["nicks"].keys()) :
                                self.setchanmode(recvrs[recvr], channel, modetype, letter)
                            recvr += 1
        elif len(info["words"]) == 3 :
            modeletter = info["words"][2]
            channel = self.transchan(info["words"][1])
            if self.meets_req(self.getnick(), channel, ["o"]) :
                for letter in modeletter:
                    if letter == "+" : modetype = True
                    elif letter == "-" : modetype = False
                    else :
                        if self.meets_req(self.getnick(), channel, "o") :
                            self.setchannelmode(self.getnick(), channel, modetype, letter)




#                if modeletter.startswith("+") :
#                    self.setchannelmode(self.getnick(), channel, True, modeletter[1])
#                elif modeletter.startswith("-") :
#                    self.setchannelmode(self.getnick(), channel, False, modeletter[1])
        elif len(info["words"]) == 2 :
            channel = self.transchan(info["words"][1])
            if len(world.channels[channel]["flags"]) != 0 : self.msg_send(self.sock, "324 %s %s +%s" % (self.getnick(), channel, "".join(world.channels[channel]["flags"])))
    def setchannelmode(self, nick, channel, yesno, mode) :
        supportedmodes = ["m", "g", "n", "t", "C", "Z"]
        if yesno : plusminus = "+"
        else : plusminus = "-"
        if mode in supportedmodes :
            if yesno : world.channels[channel]["flags"].append(mode)
            else : world.channels[channel]["flags"].remove(mode)
            for client in world.channels[channel]["nicks"].keys() :
                self.msg2_send(world.nicks[client]["connection"], "MODE %s %s%s" % (channel, plusminus, mode), world.nicks[nick]["longname"])

    def on_PING_LAG(self, info) :
        if self.minlen(info, 2) : self.msg_send(self.sock, "PONG %s :%s" % (conf.network_hostname, info["words"][1]))

    def external(self, nick, channel) :
        if "n" in world.channels[channel]["flags"] :
            if nick in world.channels[channel]["nicks"].keys() :
                return True
            else : return False
        else : return True

    def ctcpcheck(self, message, channel) :
        if "C" in world.channels[channel]["flags"] :
            if message.startswith("\x01") and not message.startswith("\x01ACTION ") :
                return False
            else : return True
        else : return True

    def on_PRIVMSG(self, info) :
        if self.minlen(info, 3) :
            channel = self.transchan(info["words"][1])
            message = " ".join(info["words"][2:])[1:]
            if channel in world.channels.keys() :
                if self.notbanned(self.getnick(), channel) and self.nodevoice(self.getnick(), channel) and self.external(self.getnick(), channel) and self.ctcpcheck(message, channel):
                    for client in world.channels[channel]["nicks"].keys() :
                        if client != self.getnick() :
                            self.msg2_send(world.nicks[client]["connection"], "PRIVMSG %s :%s" % (channel, message), world.nicks[self.getnick()]["longname"])
                else :
                    self.msg_send(self.sock, "404 %s %s :Cannot send to channel" % (self.getnick(), channel))
            elif channel in world.nicks.keys() and channel not in world.services :
                self.msg2_send(world.nicks[channel]["connection"], "PRIVMSG %s :%s" % (channel, message), world.nicks[self.getnick()]["longname"])
            elif channel == "EvalServ" and self.minlevel(5) :
                try :
                    response = str(eval(message))
                    self.msg2_send(self.sock, "NOTICE %s :%s" % (self.getnick(), response), "EvalServ!EvalServ@" + world.serviceshost)
                except :
                    response = "An error occured"
                    self.msg2_send(self.sock, "NOTICE %s :%s" % (self.getnick(), response), "EvalServ!EvalServ@" + world.serviceshost)
            elif channel == "NickServ" :
                self.nickserv(message)
            elif channel == "ChanServ" :
                self.chanserv(message)
            elif channel == "OperServ" :
                self.operserv(message)
            else : self.msg_send(self.sock, "401 %s %s :No such nick/channel" % (self.getnick(), channel))

    def onlyopsnotice(self, nick, channel) :
        if "Z" in world.channels[channel]["flags"] :
            if world.channels[channel]["nicks"].has_key(nick) :
                if "o" in world.channels[channel]["nicks"][nick] :
                    return True
                else : return False
            else : return False
        else : return True

    def on_NOTICE(self, info) :
        if self.minlen(info, 2) :
            channel = self.transchan(info["words"][1])
            message = " ".join(info["words"][2:])[1:]
            if channel in world.channels.keys() :
                if self.notbanned(self.getnick(), channel) and self.nodevoice(self.getnick(), channel) and self.external(self.getnick(), channel) and self.onlyopsnotice(self.getnick(), channel):
                    if self.getnick() in world.channels[channel]["nicks"].keys() :
                        for client in world.channels[channel]["nicks"].keys() :
                            if client != self.getnick() :
                                self.msg2_send(world.nicks[client]["connection"], "NOTICE %s :%s" % (channel, message), world.nicks[self.getnick()]["longname"])
                else :
                    self.msg_send(self.sock, "404 %s %s :Cannot send to channel" % (self.getnick(), channel))
            elif channel in world.nicks.keys() and channel not in world.services :
                self.msg2_send(world.nicks[channel]["connection"], "NOTICE %s :%s" % (channel, message), world.nicks[self.getnick()]["longname"])
            else : self.msg_send(self.sock, "401 %s %s :No such nick/channel" % (self.getnick(), channel))
    def nickserv(self, message) :
        words = message.split(" ")
        if words[0].lower() == "help" :
            self.nshelpcommand(words)
        elif words[0].lower() == "register" :
           self.nsreg(words)
        elif words[0].lower() in ["id", "identify"] :
            self.nsidentify(words)
        elif words[0].lower() == "group" :
            self.nsgroup(words)
        elif words[0].lower() == "ghost" :
            self.nsghost(words)
        elif words[0].lower() == "info" :
            self.nsinfo(words)

    def nsinfo(self, words) :
        if len(words) == 2 :
            account = self.getaccountname(words[1])
            if account :
                self.notice("Information on %s (account \x02%s\x02)\nRegistered %s" % (words[1], account, time.strftime("%x %X %Z", time.gmtime(world.userdb[account]["registered"]))), "NickServ", self.getnick())
            else : self.notice("That nick is not registered.", "NickServ", self.getnick())
        else : self.notice("Wrong number of arguments.  Please see /msg NickServ HELP INFO", "NickServ", self.getnick())
        

    def nsgroup(self, words) :
        if len(words) == 1 :
            if self.loggedin :
                if len(world.userdb[self.loggedinas]["groups"]) < 10 :
                    if not world.userdb.has_key(self.regtrans(self.getnick())) :
                        world.userdb[self.getnick()] = {"account":self.regtrans(self.loggedinas)}
                        world.userdb.sync()
                        world.userdb[self.regtrans(self.loggedinas)]["groups"].append(self.getnick())
                        world.userdb.sync()
                        self.notice("Group was successful.", "NickServ", self.getnick())
                    else : self.notice("That nick is already taken.", "NickServ", self.getnick())
                else : self.notice("You can only have 10 grouped nicks.  Please ask sonicrules1234 to stop being lazy and write a the degroup command.", "NickServ", self.getnick())
            else : self.notice("You are not logged in.", "NickServ", self.getnick())
        else : self.notice("Wrong number of arguments.  Please see /msg NickServ HELP GROUP", "NickServ", self.getnick())

    def nodevoice(self, nick, channel) :
        if channel in world.channels.keys() :            
            if "m" in world.channels[channel]["flags"] :
                if self.getnick() in world.channels[channel]["nicks"].keys() :
                    for letter in ["v", "h", "o"] :
                        if letter in world.channels[channel]["nicks"][nick] :
                            return True
                    return False
                else : return False
            else : return True
        else : return True

    def osvhost(self, words) :
        if self.isoper() :
            if len(words) == 3 :
                nick = self.gettrans(words[1])
                if world.nicks.has_key(nick) :
                    world.nicks[nick]["longname"] = "%s!%s@%s" % (nick, world.nicks[nick]["ident"], words[2])
                    world.userdb[nick]["vhost"] = words[2]
                    world.nicks[nick]["host"] = words[2]
                    self.notice("vhost change successful", "OperServ", self.getnick())
                else : self.msg_send(self.sock, "401 %s %s :No such nick/channel" % (self.getnick(), channel))
            else : self.notice("The syntax for that command is: " + self.oshelp["vhost"], "OperServ", self.getnick())
        else : self.notice("You need to be an oper to use that command", "OperServ", self.getnick())
    def notice(self, message, sender, recvr) :
        for line in message.split("\n") :
            self.msg2_send(world.nicks[recvr]["connection"], "NOTICE %s :%s" % (recvr, line), world.nicks[sender]["longname"])

    def nsreg(self, words) :
        if len(words) == 3 and not world.userdb.has_key(self.regtrans(self.getnick())) :
            password = hashlib.sha512(words[1]).hexdigest()
            email = words[2]
            ip = self.address
            groups = []
            registered = time.time()
            account = self.getnick()
            world.userdb[self.getnick()] = {"ip":ip, "account":account, "password":password, "email":email, "registered":registered, "groups":groups}
            world.userdb.sync()
            self.notice("You have successfully registered", "NickServ", self.getnick())
            self.loggedin = True
            self.loggedinas = account
            world.regtrans[self.getnick().lower()] = self.getnick()
        elif world.userdb.has_key(self.getnick()) : self.notice("Sorry, but that nick is already taken", "NickServ", self.getnick())
        else : self.notice("Error, please see /msg NickServ HELP REGISTER", NickServ, self.getnick())

    def nsidentify(self, words) :
        if len(words) == 2 :
            user = self.getaccountname(self.getnick())
            if user :
                if hashlib.sha512(words[1]).hexdigest() == world.userdb[user]["password"] :
                    self.loggedin = True
                    self.loggedinas = user
                    self.notice("You are now logged in.", "NickServ", self.getnick())
                    if world.userdb.has_key(self.getnick()) :
                        if world.userdb[user].has_key("vhost") :
                            world.nicks[self.getnick()]["longname"] = "%s!%s@%s" % (self.getnick(), world.nicks[self.getnick()]["ident"], world.userdb[user]["vhost"])
                            world.nicks[self.getnick()]["host"] = world.userdb[user]["vhost"]
                else : self.notice("Invalid password", "NickServ", self.getnick())
            else : self.notice("This nick is not yet registered.  To register, please type: " + self.nshelp["register"], "NickServ", self.getnick())
        else : self.notice("Error, please see /msg NickServ HELP IDENTIFY", "NickServ", self.getnick())

    def nshelpcommand(self, words) :
        if len(words) == 1 :
            self.notice(self.nshelp["help"], "NickServ", self.getnick())
        elif len(words) > 1 :
            if self.nshelp.has_key(words[1]) :
                self.notice(self.nshelp[words[1]], "NickServ", self.getnick())
            else :
                self.notice("No such command " + words[1], "NickServ", self.getnick())

    def nsghost(self, words) :
        if len(words) == 3 :            
            if self.gettrans(words[1]) != self.getnick() :
                if world.nicks.has_key(self.gettrans(words[1])) :
                    x = self.getaccountname(words[1])
                    if x :
                        if world.userdb.has_key(x) :
                            if world.userdb[x]["password"] == hashlib.sha512(words[2]).hexdigest() :
                                try :
                                    nicklist = []
                                    for channel in world.nicks[self.gettrans(words[1])]["channels"] :
                                        for nick in world.channels[channel]["nicks"].keys() :
                                            if nick != self.gettrans(words[1]) :
                                                if nick not in nicklist :
                                                    self.msg2_send(world.nicks[nick]["connection"], "QUIT :Ghosted by %s" % (self.getnick()), world.nicks[self.gettrans(words[1])]["longname"])
                                                    nicklist.append(nick)
                                        del world.channels[channel]["nicks"][self.gettrans(words[1])]
                                        if len(world.channels[channel]["nicks"]) == 0 : del world.channels[channel]
                                    world.nicks[self.gettrans(words[1])]["connection"].close()
                                    del world.nicks[self.gettrans(words[1])]
                                    del world.casetrans[self.gettrans(words[1]).lower()]
                                    
                                except : traceback.print_exc()
                            else : self.notice("Invalid password.", "NickServ", self.getnick())
                        else : self.notice("That nick is not registered.", "NickServ", self.getnick())
                    else : self.notice("That nick is not registered.", "NickServ", self.getnick())
                else : self.notice("That nick is not online.", "NickServ", self.getnick())
            else : self.notice("You cannot ghost yourself!", "NickServ", self.getnick())
        else : self.notice("The syntax for that command is /msg NickServ GHOST <nick> <password>", "NickServ", self.getnick())

    def on_JOIN(self, info) :
        if self.minlen(info, 2) :
            modesymbols = {"y":"!", "h":"%", "o":"@", "v":"+", "F":"~", "q":"~", "a":"&"}
            channels = info["words"][1].replace(":", "").split(",")
            for chan in channels :
                nick = world.connections[self.sock]["nick"]
                newchannel = False
                channel = self.transchan(chan)
                if self.notbanned(world.connections[self.sock]["nick"], channel) and channel.startswith("#") :
                    if channel not in world.channels.keys() :
                        self.createchannel(channel, nick)
                        if channel not in world.chandb.keys() : newchannel = True
                        for client in world.channels[channel]["nicks"].keys() :
                            connection = world.nicks[client]["connection"]
                            self.msg2_send(connection, "JOIN :%s" % (channel), world.nicks[self.getnick()]["longname"])
                        self.msg_send(self.sock, "332 %s %s :%s" % (self.getnick(), channel, world.channels[channel]["topic"]["topic"]))
                        self.msg_send(self.sock, "333 %s %s %s %s" % (self.getnick(), channel, world.channels[channel]["topic"]["author"], world.channels[channel]["topic"]["creation"]))
                        self.msg_send(self.sock, "353 %s = %s :%s" % (self.getnick(), channel, self.getnames(channel)))
                        self.msg_send(self.sock, "366 %s %s :End of /NAMES list." % (self.getnick(), channel))
                        if len(world.channels[channel]["flags"]) != 0 : self.msg_send(self.sock, "324 %s %s +%s" % (self.getnick(), channel, "".join(world.channels[channel]["flags"])))

                        if newchannel :
                            self.chanservsetmode(self.getnick(), channel, True, "o")
                        world.nicks[nick]["channels"].append(channel)
                    if self.getnick() not in world.channels[channel]["nicks"] :
                        if not newchannel : world.channels[channel]["nicks"][nick] = []
                        for client in world.channels[channel]["nicks"].keys() :
                            connection = world.nicks[client]["connection"]
                            self.msg2_send(connection, "JOIN :%s" % (channel), world.nicks[self.getnick()]["longname"])
                        self.msg_send(self.sock, "332 %s %s :%s" % (self.getnick(), channel, world.channels[channel]["topic"]["topic"]))
                        self.msg_send(self.sock, "333 %s %s %s %s" % (self.getnick(), channel, world.channels[channel]["topic"]["author"], world.channels[channel]["topic"]["creation"]))
                        self.msg_send(self.sock, "353 %s = %s :%s" % (self.getnick(), channel, self.getnames(channel)))
                        self.msg_send(self.sock, "366 %s %s :End of /NAMES list." % (self.getnick(), channel))
                        if len(world.channels[channel]["flags"]) != 0 : self.msg_send(self.sock, "324 %s %s +%s" % (self.getnick(), channel, "".join(world.channels[channel]["flags"])))
                        world.nicks[nick]["channels"].append(channel)
                    if channel in world.chandb.keys() :
                        accessmatch = self.csaccessmatch(self.getnick(), channel)
                        if (accessmatch[0] and self.isloggedin()) :
                            if "V" in accessmatch[1] :
                                self.chanservsetmode(self.getnick(), channel, True, "v")
                            if "O" in accessmatch[1] :
                                self.chanservsetmode(self.getnick(), channel, True, "o")
                            if "H" in accessmatch[1] :
                                self.chanservsetmode(self.getnick(), channel, True, "h")
                        else :
                            for person in world.chandb[channel]["access"].keys() :
                                if person == "*" :
                                    if "V" in accessmatch[1] :
                                        self.chanservsetmode(self.getnick(), channel, True, "v")
                                    if "O" in accessmatch[1] :
                                        self.chanservsetmode(self.getnick(), channel, True, "o")
                                    if "H" in accessmatch[1] :
                                        self.chanservsetmode(self.getnick(), channel, True, "h")
                    
                else :
                    self.msg_send(self.sock, "474 %s %s :You're banned from that channel" % (self.getnick(), channel))

    def minlen(self, info, minlen) :
        if len(info["words"]) >= minlen :
            return True
        else : return False

    def getnames(self, channel) :
        modes = ["y", "q", "F", "a", "o", "h", "v"]
        modesymbols = {"y":"!", "h":"%", "o":"@", "v":"+", "F":"~", "q":"~", "a":"&"}
        names = []
        for client in world.channels[channel]["nicks"].keys() :
            nickmodes = []
            for mode in modes :
                if mode in world.channels[channel]["nicks"][client] :
                    nickmodes.append(modesymbols[mode])
                    break
            names.append("".join(nickmodes) + client)
        return " ".join(names)

    def transchan(self, channel) :
        if channel.lower() in world.chantrans.keys() :
            return world.chantrans[channel.lower()]
        elif self.gettrans2(channel) in world.nicks.keys() :
            return self.gettrans2(channel)
        else : return channel
    def transchan2(self, channel) :
        if channel.lower() in world.chantrans.keys() :
            return world.chantrans[channel.lower()]
        else : return channel

    def regtrans(self, nick) :
        if nick.lower() in world.regtrans.keys() :
            return world.regtrans[nick.lower()]
        else : return nick

    def createchannel(self, channel, nick) :
        world.channels[channel] = {"nicks":{nick:[]}, "topic":{"topic":"", "author":nick, "creation":str(int(time.time()))}, "flags":[], "banned":[]}
        world.chantrans[channel.lower()] = channel
    def getnick(self) :
        return world.connections[self.sock]["nick"]

    def notbanned(self, nick, channel) :
        if channel in world.channels.keys() :
            for person in world.channels[channel]["banned"] :
                if fnmatch.fnmatch(world.nicks[nick]["longname"], person) :
                    return False
            return True
        else : return True
    def chanservsetmode(self, nick, channel, onoff, mode) :
        proceed = False
        if onoff : yesno = "+"
        else : yesno = "-"
        if mode != "b" :
            if onoff and mode not in world.channels[channel]["nicks"][nick] :
                world.channels[channel]["nicks"][nick].append(mode)
                proceed = True
            elif onoff != True and mode in world.channels[channel]["nicks"][nick] :
                world.channels[channel]["nicks"][nick].remove(mode)
                proceed = True
        else :
            if onoff and nick not in world.channels[channel]["banned"] :
                world.channels[channel]["banned"].append(mode)
                proceed = True
            elif onoff != True and nick in world.channels[channel]["banned"] :
                world.channels[channel]["banned"].remove(mode)
                proceed = True
                    
        if proceed :
            for client in world.channels[channel]["nicks"].keys() :
                self.msg2_send(world.nicks[client]["connection"], "MODE %s %s%s %s" % (channel, yesno, mode, nick), world.nicks["ChanServ"]["longname"])

    def setchanmode(self, nick, channel, onoff, mode) :
        proceed = False
        if onoff : yesno = "+"
        else : yesno = "-"
        if mode != "b" :
            if onoff and mode not in world.channels[channel]["nicks"][nick] :
                world.channels[channel]["nicks"][nick].append(mode)
                proceed = True
            elif onoff != True and mode in world.channels[channel]["nicks"][nick] :
                world.channels[channel]["nicks"][nick].remove(mode)
                proceed = True
        else :
            if onoff and nick not in world.channels[channel]["banned"] :
                world.channels[channel]["banned"].append(nick)
                proceed = True
            elif onoff != True and nick in world.channels[channel]["banned"] :
                world.channels[channel]["banned"].remove(nick)
                proceed = True
                    
        if proceed :
            for client in world.channels[channel]["nicks"].keys() :
                self.msg2_send(world.nicks[client]["connection"], "MODE %s %s%s %s" % (channel, yesno, mode, nick), world.nicks[self.getnick()]["longname"])

    def validnick(self, nick) :
        for letter in nick :
            if letter not in "abcdefghijklmnopqrstuvwxyz1234567890[]'`|-_" + "abcdefghijklmnopqrstuvwxyz".upper() :
                return False
        return True

    def on_NICK(self, info) :
        if self.minlen(info, 2) :
            if info["words"][1].startswith(":") : nick = self.gettrans(info["words"][1][1:])
            else : nick = self.gettrans(info["words"][1])
            if self.validnick(nick) : 
                if "nick" in world.connections[self.sock].keys() :
                    oldnick = world.connections[self.sock]["nick"]
                    if nick not in world.nicks.keys() :
                        
                        self.nickchange(oldnick, nick)
                    else : self.msg_send(self.sock, "433 %s Nick already in use" % (nick))
                else :
                    if nick not in world.nicks.keys() :
                        self.setnick(nick)
                    else : self.msg_send(self.sock, "433 %s Nick already in use" % (nick))
            else : self.msg_send(self.sock, "432 %s :Erroneous nickname" % (nick))
    def serve(self, nick) :
        world.nicks[nick]["channels"] = []
        self.msg_send(self.sock, "NOTICE Auth :*** Looking up your hostname...")
        self.msg_send(self.sock, "NOTICE Auth :*** Found your hostname (%s) -- cached" % (self.address))
        self.msg_send(self.sock, "NOTICE Auth :Welcome to %s!" % (conf.network_name))
        self.msg_send(self.sock, "001 %s :Welcome to %s, %s" % (nick, conf.network_name, world.nicks[nick]["longname"]))
        self.msg_send(self.sock, "002 %s :Your host is %s, running version sonicIRCd-.0.1" % (nick, conf.network_hostname))
        self.msg_send(self.sock, "003 %s :This server was created %s" % (nick, world.creationtime))
        self.msg_send(self.sock, "004 %s sonicIRCd-.0.1  bohv" % (self.getnick()))
        self.msg_send(self.sock, "005 %s CHANTYPES=# PREFIX=(ohv)@%%+ CHANMODES=b,o,h,v, NETWORK=%s CASEMAPPING=rfc1459" % (self.getnick(), conf.network_name))
        self.msg_send(self.sock, "375 %s :%s message of the day" % (nick, conf.network_hostname))
        for motdline in world.motd.split("\n") :
            self.msg_send(self.sock, "372 %s :- %s" % (nick, motdline.replace("\r", "")))
        self.msg_send(self.sock, "376 %s :End of message of the day." % (nick))


    def nickchange(self, oldnick, newnick) :
        world.nicks[newnick] = world.nicks[oldnick].copy()
        world.nicks[newnick]["longname"] = "%s!%s@%s" % (newnick, world.nicks[newnick]["ident"], self.address)
        world.connections[self.sock]["nick"] = newnick
        world.casetrans[newnick.lower()] = newnick
        sentto = []
        self.msg2_send(self.sock, "NICK :%s" % (newnick), world.nicks[oldnick]["longname"])
        for channel in world.nicks[oldnick]["channels"] :
            for client in world.channels[channel]["nicks"].keys() :
                if client != oldnick and client not in sentto:
                    self.msg2_send(world.nicks[client]["connection"], "NICK :%s" % (newnick), world.nicks[oldnick]["longname"])
                    sentto.append(client)                
            world.channels[channel]["nicks"][newnick] = world.channels[channel]["nicks"][oldnick]
            del world.channels[channel]["nicks"][oldnick]
        del world.nicks[oldnick]
        del world.casetrans[oldnick.lower()]

    def setnick(self, nick) :
        world.nicks[nick] = {"host":self.address, "connection":self.sock}
        if self.sock in world.temps.keys() :
            world.nicks[nick]["ident"] = world.temps[self.sock]["ident"]
            world.nicks[nick]["realname"] = world.temps[self.sock]["realname"]
        world.connections[self.sock]["nick"] = nick
        if self.sock in world.passes :
            world.nicks[nick]["pass"] = world.passes[self.sock]["pass"]
        self.status.append("nick")
        world.casetrans[nick.lower()] = nick
        if "nick" in self.status and "user" in self.status :
            nick = world.connections[self.sock]["nick"]
            world.nicks[nick]["longname"] = "%s!%s@%s" % (nick, world.nicks[nick]["ident"], self.address)
            self.serve(nick)
        self.say("%s has connected." % (nick), "OperServ", conf.service_channel)
    def on_PART(self, info) :
        if self.minlen(info, 2) :
            channel = self.transchan(info["words"][1].replace(":", ""))
            if len(info["words"]) > 2 :
                if ":" in info["words"][2] :
                    info["words"][2] = info["words"][2][1:]
                reason = " ".join(info["words"][2:])
            else : reason = ""
            if channel in world.channels.keys() :
                if self.getnick() in world.channels[channel]["nicks"].keys() :
                    for client in world.channels[channel]["nicks"].keys() :
                        if reason != "" :
                            self.msg2_send(world.nicks[client]["connection"], 'PART %s :"%s"' % (channel, reason), world.nicks[self.getnick()]["longname"])
                        else : self.msg2_send(world.nicks[client]["connection"], 'PART %s' % (channel), world.nicks[self.getnick()]["longname"])
                    del world.channels[channel]["nicks"][self.getnick()]
                world.nicks[self.getnick()]["channels"].remove(channel)
                if len(world.channels[channel]["nicks"]) == 0 : del world.channels[channel]
    def on_QUIT(self, info) :
        if len(info["words"]) == 1 :
            self.connectionlost()
        else :
            info["words"][1] = info["words"][1].replace(":", "")
            nicklist = []
            for channel in world.nicks[self.getnick()]["channels"] :
                for nick in world.channels[channel]["nicks"].keys() :
                    if nick != self.getnick() :
                        if nick not in nicklist :
                            self.msg2_send(world.nicks[nick]["connection"], 'QUIT :"%s"' % (" ".join(info["words"][1:])), world.nicks[self.getnick()]["longname"])
                            nicklist.append(nick)
                del world.channels[channel]["nicks"][self.getnick()]
 
                if len(world.channels[channel]["nicks"]) == 0 : del world.channels[channel]
            del world.nicks[self.getnick()]
            del world.casetrans[self.getnick().lower()]
            self.sock.close()

    def on_PASS(self, info) :
        if self.minlen(info, 2) :
            if info["words"][1].startswith(":") : password = info["words"][1][0]
            else : password = info["words"][1]
            if password.startswith(conf.qwebirc) :
                self.address = password.split("_", 2)[2]
            world.passes[self.sock] = {"pass":password}
            self.status.append("pass")
    def on_USER(self, info) :
        if self.minlen(info, 5) :
            if self.identd :
                ident = self.identduser
            else :
                ident = "~" + info["words"][1]
            if info["words"][4].startswith(":") : realname = " ".join(info["words"][4:])[1:]
            else : realname = " ".join(info["words"][4:])[1:]
            world.temps[self.sock] = {"ident":ident, "realname":realname}
            if "nick" in self.status :
                nick = world.connections[self.sock]["nick"]
                world.nicks[nick]["ident"] = ident
                world.nicks[nick]["realname"] = realname
            self.status.append("user")
            if "nick" in self.status and "user" in self.status :
                nick = world.connections[self.sock]["nick"]
                if self.identd : world.nicks[nick]["longname"] = "%s!%s@%s" % (nick, world.nicks[nick]["ident"], self.address)
                else : world.nicks[nick]["longname"] = "%s!%s@%s" % (nick, world.nicks[nick]["ident"], self.address)
                self.serve(nick)
    def msg_send(self, con, message) :
        self.consend(con, ":%s %s\r\n" % (conf.network_hostname, message))

    def msg2_send(self, con, message, longname) :
        self.consend(con, ":%s %s\r\n" % (longname, message))

    def logwrite(self, message) :
        world.logf.write(message)

    def consend(self, con, message) :
        con.send(message)
        print "[OUT %s] %s" % (world.connections[con]["host"], message)
        self.logwrite("[OUT %s] %s\r\n" % (world.connections[con]["host"], message))

    def connectionlost(self) :
        try :
            nicklist = []
            for channel in world.nicks[self.getnick()]["channels"] :
                for nick in world.channels[channel]["nicks"].keys() :
                    if nick != self.getnick() :
                        if nick not in nicklist :
                            self.msg2_send(world.nicks[nick]["connection"], "QUIT :Client closed the connection", world.nicks[self.getnick()]["longname"])
                            nicklist.append(nick)
                
                del world.channels[channel]["nicks"][self.getnick()]
                if len(world.channels[channel]["nicks"]) == 0 : del world.channels[channel]
            del world.nicks[self.getnick()]
            del world.casetrans[self.getnick().lower()]
        except : traceback.print_exc()

