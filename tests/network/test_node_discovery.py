import logging
LOG_FORMAT = "%(levelname)s %(name)s %(lineno)d: %(message)s"
logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)


import time
import unittest
import btctxstore
from storjnode import network


INITIAL_RELAYNODES = [("127.0.0.1", 6667)]


class TestNodeDiscovery(unittest.TestCase):

    def setUp(self):
        self.btctxstore = btctxstore.BtcTxStore()
        self.alice_wif = self.btctxstore.create_key()
        self.alice_address = self.btctxstore.get_address(self.alice_wif)
        self.bob_wif = self.btctxstore.create_key()
        self.bob_address = self.btctxstore.get_address(self.bob_wif)
        self.alice = network.Network(INITIAL_RELAYNODES, self.alice_wif)
        self.alice.connect()
        self.bob = network.Network(INITIAL_RELAYNODES, self.bob_wif)
        self.bob.connect()
        time.sleep(10)

    def tearDown(self):
        self.alice.disconnect()
        self.bob.disconnect()

    def test_connects(self):
        self.alice.connect_to_node(self.bob_address)
        time.sleep(10)
        self.assertTrue(self.alice.node_connected(self.bob_address))
        self.assertTrue(self.bob.node_connected(self.alice_address))


if __name__ == "__main__":
    unittest.main()