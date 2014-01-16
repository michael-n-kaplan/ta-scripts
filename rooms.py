#  twistd -ny rooms.py

# 
from random import randint

# Read from file
from twisted.application import internet, service
from twisted.internet import protocol, reactor, defer
from twisted.protocols import basic

class room:
  pass

rooms = {}

r1 = room()
r1.short = "Short description of starting room"
r1.coords = (0,0)  ## or use x / y instead?
r1.exits = [ ("w", (-1,0)), ("enter portal", (-2,1))]

def makeRoom(coords, exits, short):
  r = room()
  r.coords = coords
  r.exists = exits
  r.short = short
  rooms[coords] = r
  return r

rooms[(0,0)] = r1
makeRoom( (-1,0), [], "-1,0")
makeRoom( (-2,1), [], "-2,1")

def move(currentRoom, direction):
  exits = currentRoom.exits
  for r in exits:
    if r[0] == direction:
      return rooms[r[1]]
  print "No exit in the direction"

class FingerProtocol(basic.LineReceiver):
    def lineReceived(self, user):
        self.factory.handleLine(user
        ).addErrback(lambda _: "Internal error in server"
        ).addCallback(lambda m:
                      (self.transport.write(m+"\r\n")))

class FingerService(service.Service):
    def __init__(self, filename):
        self.users = {}
        self.filename = filename
        self.x = 0
        self.y = 0
    def _read(self):
        for line in file(self.filename):
            user, status = line.split(':', 1)
            user = user.strip()
            status = status.strip()
            self.users[user] = status
        self.call = reactor.callLater(30, self._read)
    def startService(self):
        self._read()
        service.Service.startService(self)
    def stopService(self):
      service.Service.stopService(self)
        self.call.cancel()
    def getFingerFactory(self):
        f = protocol.ServerFactory()
        f.protocol, f.handleLine = FingerProtocol, self.handleLine
        return f

    def checkRoom(self):
       if (self.x == 0 and self.y == 0):
         return "\nThere is a portal here"
       else:
         return ""

    def handleLine(self, line):
        line.strip()
        text = ""
        if( line == "go portal"):
          if (self.x == 0 and self.y == 0):
            self.x = -2
            self.y =  1
            return defer.succeed("Room: (%d, %d)" % (self.x, self.y))
          else:
            return defer.succeed("There is no portal in this room.\nRoom: (%d, %d)" % (self.x, self.y))
        if( line == "e" ):
          self.x += 1
          ## create a blank room to test map digging
          if (self.x == -1 and self.y == 1):
            self.x = 0
          text = self.checkRoom()
          return defer.succeed("Room: (%d, %d)%s" % (self.x, self.y, text))
        if( line == "w" ):
          self.x -= 1
          ## ensure this room doesn't exist from any direction
          if (self.x == -1 and self.y == 1):
            self.x = -2
          text = self.checkRoom()
          return defer.succeed("Room: (%d, %d)%s" % (self.x, self.y, text))
        if( line == "n" ):
          if( self.x == -1 and self.y == 0):
            return defer.succeed("No exit in that direction")
          self.y += 1
          text = self.checkRoom()
          return defer.succeed("Room: (%d, %d)%s" % (self.x, self.y, text))
        if( line == "s" ):
          if( self.x == -1 and self.y == 2):
            return defer.succeed("No exit in that direction")
          self.y -= 1
          text = self.checkRoom()
          return defer.succeed("Room: (%d, %d)%s" % (self.x, self.y, text))
        if( line == "ne" ):
          if( self.x == -2 and self.y == 0):
            return defer.succeed("No exit in that direction")
          self.x += 1
          self.y += 1
          text = self.checkRoom()
          return defer.succeed("Room: (%d, %d)%s" % (self.x, self.y, text))
       if( line == "se" ):
          if( self.x == -3 and self.y == 2):
            return defer.succeed("No exit in that direction")
          self.x += 1
          self.y -= 1
          text = self.checkRoom()
          return defer.succeed("Room: (%d, %d)%s" % (self.x, self.y, text))
        if( line == "sw" ):
          if( self.x == 0 and self.y == 2):
            return defer.succeed("No exit in that direction")
          self.x -= 1
          self.y -= 1
          text = self.checkRoom()
          return defer.succeed("Room: (%d, %d)%s" % (self.x, self.y, text))
        if(line == "ex"):
           return defer.succeed("Exits: se,w.")
        if(line == "nw"):
           return defer.succeed("Sorry, there's no exit in that direction.")
        if(line == "reroll"):
           return defer.succeed(gen_stats())
        return defer.succeed("Unknown Command: %s\nRoom: (%d, %d)%s" % (
           line, self.x, self.y, text))

# application = service.Application('finger', uid=1000, gid=1000)
application = service.Application('finger')
f = FingerService('users')
finger = internet.TCPServer(1079, f.getFingerFactory())

finger.setServiceParent(service.IServiceCollection(application))
f.setServiceParent(service.IServiceCollection(application))
