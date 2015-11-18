#!/usr/bin/env python
import time
import signal
import binascii
import storjnode
from crochet import setup, TimeoutError

# start twisted via crochet and remove twisted handler
setup()
signal.signal(signal.SIGINT, signal.default_int_handler)

# isolate nodes becaues this example fails behind a NAT

# create alice node (with bitcoin wif as node key)
alice_key = "Kyh4a6zF1TkBZW6gyzwe7XRVtJ18Y75C2bC2d9axeWZnoUdAVXYc"
alice_node = storjnode.network.Node(
    alice_key, bootstrap_nodes=[("240.0.0.0", 1337)]
)

# create bob node (with bitcoin hwif as node key)
bob_key = ("xprv9s21ZrQH143K3uzRG1qUPdYhVZG1TAxQ9bLTWZuFf1FHR5hiWuRf"
           "o2L2ZNoUX9BW17guAbMXqHjMJXBFvuTBD2WWvRT3zNbtVJ1S7yxUvWd")
bob_node = storjnode.network.Node(
    bob_key, bootstrap_nodes=[("127.0.0.1", alice_node.port)]
)

try:
    # add message handler to bob node
    def message_handler(source, message):
        src = binascii.hexlify(source) if source is not None else "unknown"
        print("%s from %s" % (message, src))
    bob_node.add_message_handler(message_handler)

    print("Giving nodes some time to find peers.")
    time.sleep(storjnode.network.WALK_TIMEOUT)

    # send direct message (blocking call)
    alice_node.direct_message(bob_node.get_id(), "hi bob")
    # bob_node.direct_message(alice_node.get_id(), "hi alice")

except TimeoutError:
    print("Got timeout error")

except KeyboardInterrupt:
    pass

finally:
    print("Stopping nodes")
    alice_node.stop()
    bob_node.stop()
