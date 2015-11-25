import storjnode
from storjnode.network.api import DEFAULT_BOOTSTRAP_NODES
from storjnode.network.file_transfer import FileTransfer
from storjnode.network.process_transfers import process_transfers
from storjnode.util import address_to_node_id
import storjnode.storage as storage
import btctxstore
import pyp2p
import hashlib
import tempfile
import os
import time
import requests
import unittest
import shutil
import logging
from storjnode.network.process_transfers import get_contract_id
from pyp2p.sock import Sock
from crochet import setup
setup()


_log = logging.getLogger(__name__)

class TestProcessTransfers(unittest.TestCase):

    def setUp(self):
        self.test_storage_dir = tempfile.mkdtemp()

        # Sample node.
        self.wallet = btctxstore.BtcTxStore(testnet=False, dryrun=True)
        self.wif = self.wallet.get_key(self.wallet.create_wallet())
        self.node_id = address_to_node_id(self.wallet.get_address(self.wif))
        self.store_config = {
            os.path.join(self.test_storage_dir, "storage"): {"limit": 0}
        }

        # dht_node = pyp2p.dht_msg.DHT(node_id=node_id)
        self.dht_node = storjnode.network.Node(self.wif, bootstrap_nodes=DEFAULT_BOOTSTRAP_NODES, disable_data_transfer=True)

        # Transfer client.
        self.client = FileTransfer(
            pyp2p.net.Net(
                node_type="simultaneous",
                nat_type="preserving",
                net_type="direct",
                passive_port=60500,
                dht_node=self.dht_node,
                debug=1
            ),
            wif=self.wif,
            store_config=self.store_config
        )

    def tearDown(self):
        shutil.rmtree(self.test_storage_dir)
        self.dht_node.stop()

    def test_get_contract_id(self):
        con = Sock("towel.blinkenlights.nl", 23, blocking=1)
        self.client.con_transfer[con] = b""
        contract_id = b""
        assert(get_contract_id(self.client, con, contract_id) == 1)
        con.close()

if __name__ == "__main__":
    unittest.main()