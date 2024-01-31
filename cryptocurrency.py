# in this code 2 function work
#1>  remove_highest_transactions ,get_highest_transactions
from operator import itemgetter
from multiprocessing import Process
from random import choice, randint
import datetime
import time
import hashlib
import json
from flask import Flask, jsonify, request
import requests
from uuid import uuid4
from urllib.parse import urlparse

# part 1 building the block
class Blockchain:

    def __init__(self):
        self.chain = []
        self.transactions = []
        # creating the genesis block
        self.create_block(proof=1, previous_hash='0')
        self.nodes = set()

    def create_block(self, proof, previous_hash):
        block = {'index': len(self.chain) + 1,
                'timestamp': str(datetime.datetime.now()),
                'proof': proof,
                'previous_hash': previous_hash,
                'transactions': self.transactions}
        # to empty the list of transaction
        self.transactions = []
        self.chain.append(block)
        return block

    def get_previous_block(self):
        return self.chain[-1]

    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False
        while check_proof is False:
            hash_operation = hashlib.sha256(str(new_proof ** 2 - previous_proof ** 2).encode()).hexdigest()
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1
        return new_proof

    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()

    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof ** 2 - previous_proof ** 2).encode()).hexdigest()
            if hash_operation[:4] != '0000':
                return False
            previous_block = block
            block_index += 1
        return True
    
    def add_transaction(self, sender, receiver, amount):
        start_time = time.time()
        self.transactions.append({'sender': sender, 'receiver': receiver, 'amount': amount})
        previous_block = self.get_previous_block()
        end_time = time.time()
        latency = end_time - start_time
        return previous_block['index'] + 1, latency
    
    def add_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)
    
    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        for node in network:
            response = requests.get(f'http://{node}/get_chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
            if length > max_length and self.is_chain_valid(chain):
                max_length = length
                longest_chain = chain
        if longest_chain:
            self.chain = longest_chain
            return True
        else:
            return False

# part 2 MINING our blockchain
# creating a web app
app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

# creating an addr for node on port 5000
node_address = str(uuid4()).replace('-', '')
# creating a blockchain
blockchain = Blockchain()

# mining a blockchain
@app.route('/mine_block', methods=['GET'])
def mine_block():
    start_time = time.time()
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    blockchain.add_transaction(sender=node_address, receiver='user1', amount=1)
    block = blockchain.create_block(proof, previous_hash)
    end_time = time.time()
    latency = end_time - start_time
    response = {'message': 'Congratulation, you just mined a block!',
                'index': block['index'],
                'timestamp': block['timestamp'],
                'proof': block['proof'],
                'previous_hash': block['previous_hash'],
                'transactions': block['transactions'],
                'latency': latency}
    return jsonify(response), 200

# Getting the full blockchain
@app.route('/get_chain', methods=['GET'])
def get_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }
    return jsonify(response), 200

# checking the Blockchain is valid
@app.route('/is_valid', methods=['GET'])
def is_valid():
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    if is_valid:
        response = {'message': 'All good. The Blockchain is valid'}
    else:
        response = {'message': 'We have a problem. The Blockchain is not valid'}
    return jsonify(response), 200

# adding a new transaction to the block
@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    json_data = request.get_json()
    transaction_keys = ['sender', 'receiver', 'amount']
    if not all(key in json_data for key in transaction_keys):
        return 'Some elements of the transaction are missing', 400
    index = blockchain.add_transaction(json_data['sender'], json_data['receiver'], json_data['amount'])
    response = {'message': f'This transaction added to the Block {index}'}
    return jsonify(response), 201

# part 3 Decentralize the Blockchain
# Connecting a new nodes
@app.route('/connect_node', methods=['POST'])
def connect_node():
    json_data = request.get_json()
    nodes = json_data.get('nodes')
    if nodes is None:
        return "No node", 400
    for node in nodes:
        blockchain.add_node(node)
    response = {'message': 'All the nodes are now connected. The icoin Blockchain contains the following nodes',
                'total_nodes': list(blockchain.nodes)}
    return jsonify(response), 201

# Replacing the chain with the longest chain if needed
@app.route('/replace_chain', methods=['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:
        response = {'message': 'The nodes had different chains, so the chain replaced by the longest one ',
                    'new_chain': blockchain.chain}
    else:
        response = {'message': 'All good. the chain is the longest one!!', 'actual_chain': blockchain.chain}
    return jsonify(response), 200



# adding n nodes and random transaction

@app.route('/inc_Nodes', methods=['GET'])
def inc_Nodes():
    n = request.args.get('n', type=int)

    # Move initialization of nodeArr here
    nodeArr = []
    processes = []
    
    # Get the current node's URL
    current_node = f'http://127.0.0.1:{5000}'  
    
    for i, port in enumerate(range(5001, 5001 + n)):
        nodeArr.append(port)
        # here we can add nodes
        p = Process(target=run_app, args=(port,))
        processes.append(p)

    for p in processes:
        p.start()


    for p in processes:
        p.join()

    response = {'message': 'All nodes are started, and random transactions are added', 'nodes': nodeArr}
    return jsonify(response), 200

# n number of random transaction
@app.route('/n_transaction' , methods=["GET"])
def n_transaction():
    n = request.args.get('n', type=int)
    # sender = choice(list(blockchain.nodes))
    for i in range(n):
        requests.get('http://127.0.0.1:5000/generate_random_transaction')
        # requests.get(f'http://{sender}/generate_random_transaction')
    return jsonify({'message': f'sending {i+1}th transaction'}), 200

#helper function1 of n_transaction
@app.route('/generate_random_transaction', methods=['GET'])
def generate_random_transaction():
    # Generate and send one random transaction to different nodes
    sender = choice(list(blockchain.nodes))  # Randomly select a sender from the existing nodes
    receiver = f'user{randint(1, len(blockchain.nodes))}'  # Randomly select a receiver node
    amount = randint(4, 10)  # Random transaction amount

    add_transaction_to_all_nodes(sender, receiver, amount)

    response = {
        'message': 'Random transaction added to the Blockchain',
        'transaction_info': {
            'sender': sender,
            'receiver': receiver,
            'amount': amount
        }
    }
    return jsonify(response), 200
#helper function2 of  generate_random_transaction
def add_transaction_to_all_nodes(sender, receiver, amount):
    url ='http://127.0.0.1:5000/add_transaction'
    data = {'sender': sender, 'receiver': receiver, 'amount': amount}
    requests.post(url,json=data)
    for node in blockchain.nodes:
        url = f'http://{node}/add_transaction'
        data = {'sender': sender, 'receiver': receiver, 'amount': amount}
        response = requests.post(url, json=data)

#get 3 top transaction 
@app.route('/get_highest_transactions', methods=['GET'])
def get_highest_transactions():
    # Get the top 3 highest transactions based on the transaction amount
    top_transactions = sorted(blockchain.transactions, key=itemgetter('amount'), reverse=True)[:3]

    response = {'highest_transactions': top_transactions}
    return jsonify(response), 200

#helper function 2
# Flask route to remove a transaction from the transaction pool
@app.route('/remove_transaction', methods=['POST'])
def remove_transaction():
    json_data = request.get_json()
    transaction_keys = ['sender', 'receiver', 'amount']
    if not all(key in json_data for key in transaction_keys):
        return 'Some elements of the transaction are missing', 400

    # Remove the transaction from the transaction pool
    blockchain.transactions.remove(json_data)

    response = {'message': 'Transaction removed from the transaction pool'}
    return jsonify(response), 200


#helper1 function of remove_highest_transactions
def remove_transaction_from_all_nodes(sender, receiver, amount):
    for node in blockchain.nodes:
        url = f'http://{node}/remove_transaction'
        data = {'sender': sender, 'receiver': receiver, 'amount': amount}
        requests.post(url, json=data)

# remove highest 3 transaction 
# Flask route to remove the highest 3 transactions from the transaction pool
@app.route('/remove_highest_transactions', methods=['GET'])
def remove_highest_transactions():
    # Get the top 3 highest transactions based on the transaction amount
    top_transactions = sorted(blockchain.transactions, key=itemgetter('amount'), reverse=True)[:3]

    # Remove the highest 3 transactions from the pool
    for transaction in top_transactions:
        if transaction in blockchain.transactions:
            blockchain.transactions.remove(transaction)
    
    # Remove the highest 3 transactions from all nodes
    for transaction in top_transactions:
        sender = transaction['sender']
        receiver = transaction['receiver']
        amount = transaction['amount']

        remove_transaction_from_all_nodes(sender, receiver, amount)

    response = {'message': 'Highest 3 transactions removed from the transaction pool'}
    return jsonify(response), 200


#my 
@app.route('/mine_block_with_transactions', methods=['GET'])
def mine_block_with_transactions():
    current_node = '127.0.0.1:5000'
    if blockchain.nodes:
        mining_node = choice(list(blockchain.nodes) + [current_node])
    else:
        mining_node = current_node

    # Check if the selected node is running
    # step 1: store highest transaction
    # Send a request to the selected node to get the top 3 highest transactions
    response = requests.get(f'http://{mining_node}/get_highest_transactions')

    if response.status_code != 200:
        return jsonify({'message': 'Error getting highest transactions from the mining node'}), 500

    top_transactions = response.json()['highest_transactions']

    # step 2: remove highest transaction
    response = requests.get(f'http://{mining_node}/remove_highest_transactions')

    if response.status_code != 200:
        return jsonify({'message': 'can not remove highest transaction'}), 500

    # step3: get remaining transaction
    response = requests.get(f'http://{mining_node}/get_transaction_pool')
    remaining_transaction = response.json()['transactions']

    # step4: mining node transaction contains only highest transaction
    response = requests.post(f'http://{mining_node}/set_the_transaction',
                            json={'top_transactions': top_transactions})

    # step5: random node mine a block
    response = requests.get(f'http://{mining_node}/mine_block')

    # Step 6: mining node contains remaining transactions
    response = requests.post(f'http://{mining_node}/set_the_transaction',
                             json={'top_transactions': remaining_transaction})

    return jsonify({'msg': 'successfully', 'top-transaction': top_transactions}), 200


#helper of mine_block_with_transactions
@app.route('/set_the_transaction', methods=['POST'])
def set_the_transaction():
    data = request.get_json()
    blockchain.transactions = data.get('top_transactions')

    response = {'message': 'Remaining transactions added to the Blockchain'}
    return jsonify(response), 200

# n number of request mine_block_with_transactions
@app.route('/n_mine_block_with_transactions' , methods=["GET"])
def n_mine_block_with_transactions():
    n = request.args.get('n', type=int)
    for i in range(n):
        requests.get('http://127.0.0.1:5000/mine_block_with_transactions')
    return jsonify({'message': f'send {i+1} request '}), 200

# Flask route to get all transactions in the transaction pool
@app.route('/get_transaction_pool', methods=['GET'])
def get_transaction_pool():
    response = {'transactions': blockchain.transactions,
                'count':len(blockchain.transactions)}
    return jsonify(response), 200


# auto connecting to all nodes  use auto_add
@app.route('/auto_connect', methods=['GET'])
def auto_connect():
    n = request.args.get('n', type=int)
    for i in range(n+1):
        requests.get(f'http://127.0.0.1:{5000 + i}/auto_add?n={n}')
    return jsonify({'message': 'Auto-connect completed'}), 200

@app.route('/auto_add', methods=['GET'])
def auto_add():
    n = request.args.get('n', type=int)
    for i in range(n+1):
        host_with_port = request.host
        if(host_with_port!=f'127.0.0.1:{5000 + i}'):
            blockchain.nodes.add(f'127.0.0.1:{5000 + i}')
    return jsonify({'message': 'Auto-add completed'}), 200


# Flask route to get all nodes
@app.route('/get_nodes', methods=['GET'])
def get_nodes():
    response = {'nodes': list(blockchain.nodes)}
    return jsonify(response), 200


# # Running the app
def run_app(port=5001):
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    # Running the Flask app on multiple processes
    processes = []

    # Here we can add nodes
    num_nodes = 0
    for i, port in enumerate(range(5001, 5001 + num_nodes)):
        p = Process(target=run_app, args=(port,))
        p.start()
        processes.append(p)

    # Start the Flask app on the main thread
    app.run(host='0.0.0.0', port=5000)

    for p in processes:
        p.join()


# throghput 
        # no. of transaction per second  tps
        # 1min 100 1s=?no.of trasaction
    # latency 
        # add trasaction id  
# add unused transaction to mem pool
        # head and tail 