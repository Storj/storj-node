import binascii
import time
try:
    from Queue import Queue, Full  # py2
except ImportError:
    from queue import Queue, Full  # py3
from kademlia.protocol import KademliaProtocol
from kademlia.routing import RoutingTable
from kademlia.routing import TableTraverser
from kademlia.node import Node
import heapq
import operator
import logging


def _findNearest(self, node, k=None, exclude=None):
    k = k or self.ksize
    nodes = []
    for neighbor in TableTraverser(self, node):
        if exclude is None or not neighbor.sameHomeAs(exclude):
            heapq.heappush(nodes, (node.distanceTo(neighbor), neighbor))
        if len(nodes) == k:
            break

    return list(map(operator.itemgetter(1), heapq.nsmallest(k, nodes)))


RoutingTable.findNeighbors = _findNearest  # XXX hack find neighbors


class StorjProtocol(KademliaProtocol):

    def __init__(self, *args, **kwargs):
        max_messages = kwargs.pop("max_messages")
        self.messages_relay = Queue(maxsize=max_messages)
        self.messages_received = Queue(maxsize=max_messages)
        self.is_public = False  # assume False, set by server
        KademliaProtocol.__init__(self, *args, **kwargs)
        self.log = logging.getLogger(__name__)

    def queue_relay_message(self, message):
        try:
            self.messages_relay.put_nowait(message)
            return True
        except Full:
            msg = "Relay message queue full, dropping message for %s"
            self.log.warning(msg % binascii.hexlify(message["dest"]))
            return False

    def queue_received_message(self, message):
        try:
            self.messages_received.put_nowait(message)
            return True
        except Full:
            self.log.warning("Received message queue full, dropping message.")
            return False

    def rpc_is_public(self, sender, nodeid):
        # FIXME add self.welcomeIfNewNode(Node(nodeid, sender[0], sender[1]))
        return self.is_public

    def rpc_relay_message(self, sender, nodeid, destid, message):
        self.log.debug("Got relay message from {0} at {1} for {2}.".format(
            binascii.hexlify(nodeid), sender, binascii.hexlify(destid)
        ))
        # FIXME add self.welcomeIfNewNode(Node(nodeid, sender[0], sender[1]))
        if destid == self.sourceNode.id:
            queued = self.queue_received_message({
                "source": None, "message": message, "timestamp": time.time()
            })
        else:
            # FIXME only add if ownid between sender and dest
            queued = self.queue_relay_message({
                "dest": destid, "message": message, "timestamp": time.time()
            })
        return (sender[0], sender[1]) if queued else None

    def rpc_direct_message(self, sender, nodeid, message):
        self.log.debug("Got direct message from {0}@{1}".format(
            binascii.hexlify(nodeid), sender
        ))
        source = Node(nodeid, sender[0], sender[1])
        # FIXME add self.welcomeIfNewNode(source)
        queued = self.queue_received_message({
            "source": source, "message": message, "timestamp": time.time()
        })
        return (sender[0], sender[1]) if queued else None

    def callRelayMessage(self, nodeToAsk, destid, message):
        address = (nodeToAsk.ip, nodeToAsk.port)
        self.log.debug("Sending relay message to {0}:{1}".format(*address))
        d = self.relay_message(address, self.sourceNode.id, destid, message)
        return d.addCallback(self.handleCallResponse, nodeToAsk)

    def callDirectMessage(self, nodeToAsk, message):
        address = (nodeToAsk.ip, nodeToAsk.port)
        self.log.debug("Sending direct message to {0}:{1}".format(*address))
        d = self.direct_message(address, self.sourceNode.id, message)
        return d.addCallback(self.handleCallResponse, nodeToAsk)

    def callIsPublic(self, nodeToAsk):
        address = (nodeToAsk.ip, nodeToAsk.port)
        self.log.debug("Querying if node is public {0}:{1}".format(*address))
        d = self.is_public(address, self.sourceNode.id)
        return d.addCallback(self.handleCallResponse, nodeToAsk)
