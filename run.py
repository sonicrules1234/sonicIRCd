#!/usr/bin/env python
import world, socket, conf, thread, traceback, select, time, fnmatch, shelve, hashlib, random, sonicIRCd, os, sys
#import daemon

print "Starting sonicIRCd..."
if world.pythonversion == "2.5" :
    import OpenSSL
else : import ssl
def waitfordata() :
    while True :
        if len(world.conlist) != 0 :
            noerror = False
            tempconlist = world.conlist[:]
            try :
                connections = select.select(tempconlist, [], [], 5)
                noerror = True
            except :
                for network in tempconlist :
                    try :
                        connections = select.select([network], [], [], 0)
                    except :
                        try :
                            if world.instances[network].getnick() in world.nicks.keys() : world.instances[network].connectionlost()
                        except : pass
                        world.conlist.remove(network)
            if noerror :
                for connection in connections[0] :
                    try : data = connection.recv(4096)
                    except : data = ""
                    if data != "" :
                        try :
                            returnval = world.instances[connection].parseData(data)
                            if returnval == "Rehash" :
                                print "Rehashing"
                                reload(sonicIRCd)
                                instances = world.instances.keys()[:]
                                rehash = __import__("rehash")
                                for instance in instances :
                                    rehash.main(instance, world, sonicIRCd.sonicIRCd())
                                del instances
                                reload(conf)
                                world.instances[connection].msg_send(connection, "382 %s sonicIRCd.py and conf.py :Rehashed successfully" % (world.connections[connection]["nick"]))
                                
                        except : traceback.print_exc()
                    else:
                        print "No data, closing the connection"
                        connection.close()
                        try :
                            if world.instances[connection].getnick() in world.nicks.keys() : world.instances[connection].connectionlost()
                        except : pass
                        world.conlist.remove(connection)
                del tempconlist
        else :
            world.waitingfordata = False
            break

def regserv() :
        
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', conf.port))
    s.listen(1)



    while True :
        try :        
            conn, addr = s.accept()
            if addr[0] not in conf.bannedips :
                world.instances[conn] = sonicIRCd.sonicIRCd()
                world.instances[conn].ssl = False
                thread.start_new_thread(world.instances[conn].onConnect, (conn, addr))
                if not world.waitingfordata :
                    world.waitingfordata = True
                    thread.start_new_thread(waitfordata, ())
            else : conn.close()
        except :
            break
    s.close()



def sslserv() :
    try :
        
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if world.pythonversion == "2.5" :
            contextobject = OpenSSL.SSL.Context(OpenSSL.SSL.SSLv3_METHOD)
            contextobject.use_certificate_file(conf.certfile)
            contextobject.use_privatekey_file(conf.keyfile)
            s = OpenSSL.SSL.Connection(contextobject, s)
        else : s = ssl.wrap_socket(s, certfile=conf.certfile, keyfile=conf.keyfile)
        s.bind(('', conf.sslport))
        s.listen(1)
    except: traceback.print_exc()


    while True :
        try :        
            conn, addr = s.accept()
            if addr[0] not in conf.bannedips :
                world.instances[conn] = sonicIRCd.sonicIRCd()
                world.instances[conn].ssl = True
                thread.start_new_thread(world.instances[conn].onConnect, (conn, addr))
                if not world.waitingfordata :
                    world.waitingfordata = True
                    thread.start_new_thread(waitfordata, ())
            else : conn.close()
        except :
            traceback.print_exc()
            break

    s.close()
class ErrorLogger:
    def write(self, s):
        errors = open("errors.txt", "a")
        errors.write(s)
        errors.close()
class OutputLogger:
    def write(self, s):
        output = open("output.txt", "a")
        output.write(s)
        output.close()

sys.stdin.close()
sys.stdout = OutputLogger()
sys.stderr = ErrorLogger()
try: 
    if os.name=="nt":
        pass
    else:
        pid = os.fork() 
        if pid > 0:
	    # exit first parent
            sys.exit(0) 
except OSError, e: 
    sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
    sys.exit(1)
pidfile = open("pid.txt", "w")
pidfile.write(str(os.getpid()) + "\n")
pidfile.close()
try :
    thread.start_new_thread(sslserv, ())
    regserv()
except : traceback.print_exc()
world.userdb.close()
world.chandb.close()
for connection in world.conlist :
    try : connection.close()
    except : pass
#os.remove("pid.txt")
