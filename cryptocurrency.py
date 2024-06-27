# added transaction fee ,
import random
from threading import Event
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
import pandas as pd


# part 1 building the block
class Blockchain:

    def __init__(self):
        self.chain = []
        self.transactions = []
        # creating the genesis block
        self.create_block(proof=1, previous_hash='0')
        self.throughput=[]
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
    
    def add_transaction(self, sender, receiver, amount,fee,timestamp):
        transaction_id = str(uuid4())  # Generate a unique transaction ID
        # start_time = time.time()
        self.transactions.append({'transaction_id': transaction_id,'sender': sender, 'receiver': receiver, 'amount': amount,'fee':fee,'timestamp':timestamp} )
        previous_block = self.get_previous_block()
        # end_time = time.time()
        # latency = end_time - start_time
        return previous_block['index'] + 1 # , latency
    
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
    blockchain.add_transaction(sender=node_address, receiver='user1', amount=1,fee=0,timestamp=str(datetime.datetime.now()))
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
    transaction_keys = ['sender', 'receiver', 'amount','fee','timestamp']
    if not all(key in json_data for key in transaction_keys):
        return 'Some elements of the transaction are missing', 400
    index = blockchain.add_transaction(json_data['sender'], json_data['receiver'], json_data['amount'],json_data['fee'],json_data['timestamp'])
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



# adding n nodes
@app.route('/inc_Nodes', methods=['GET'])
def inc_Nodes():
    n = request.args.get('n', type=int)
    n=n-1  #starting from 0

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
    
    # # output in excel 
    # df=pd.read_excel('my.xlsx')
    # df.loc[df['Throughput'].count(),'Total Transaction']=n
    # df.to_excel('my.xlsx',index=False)

    # sender = choice(list(blockchain.nodes))
    for i in range(n):
        requests.get('http://127.0.0.1:5000/generate_random_transaction')
        # requests.get(f'http://{sender}/generate_random_transaction')
    return jsonify({'message': f'sending {i+1}th transaction'}), 200

#helper function1 of n_transaction
# Generate and send one random transaction to different nodes
@app.route('/generate_random_transaction', methods=['GET'])
def generate_random_transaction():
    if not blockchain.nodes:  # Check if there are available nodes
        return jsonify({'message': 'No nodes available to generate transaction'}), 200
    sender = choice(list(blockchain.nodes))  # Randomly select a sender from the existing nodes
    receiver = f'user{randint(1, len(blockchain.nodes))}'  # Randomly select a receiver node
    amount = randint(4, 10)  # Random transaction amount

    # Calculate fee as a random value between 1.5% and 10% of the amount
    fee_percentage = random.uniform(1.5, 10)
    fee = (fee_percentage / 100) * amount
    # fee=4

    # Get the current date and time
    current_time=str(datetime.datetime.now())
    # current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    add_transaction_to_all_nodes(sender, receiver, amount,fee,current_time)

    response = {
        'message': 'Random transaction added to the Blockchain',
        'transaction_info': {
            'sender': sender,
            'receiver': receiver,
            'amount': amount,
            'fee':fee,
            'timestamp':current_time
        }
    }
    return jsonify(response), 200
#helper function2 of  generate_random_transaction
def add_transaction_to_all_nodes(sender, receiver, amount,fee,current_time):
    url ='http://127.0.0.1:5000/add_transaction'
    data = {'sender': sender, 'receiver': receiver, 'amount': amount,'fee':fee,'timestamp':current_time}
    requests.post(url,json=data)
    for node in blockchain.nodes:
        url = f'http://{node}/add_transaction'
        data = {'sender': sender, 'receiver': receiver, 'amount': amount,'fee':fee,'timestamp':current_time}
        response = requests.post(url, json=data)

#get k top transaction 
@app.route('/get_highest_transactions', methods=['GET'])
def get_highest_transactions():
    k = request.args.get('k', type=int)
# Get the top k highest transactions based on the transaction amount
    result = calculate_integer_percentages(k)
    per_80, per_12, per_8 = result
    # print(per_80)
    # print(per_12)
    # print(per_8)
    sorted_transactions = sorted(blockchain.transactions, key=itemgetter('amount'), reverse=True)
    # print(sorted_transactions)
        # Print only the transaction amounts
    transaction_amounts = [transaction['amount'] for transaction in sorted_transactions]
    # print(transaction_amounts)
    # print("top transaction")
    # Determine the first, middle, and last elements
    first_index = 0
    middle_index = per_80
    # middle_index = len(lst) // 2
    last_index = len(sorted_transactions) - 1

    # top_transactions = sorted_transactions[:per_80]
    top_transactions = []
    while per_80 > 0 and first_index < len(blockchain.transactions):
        temp = sorted_transactions[first_index]
        if temp['transaction_id'] not in [trans['transaction_id'] for trans in top_transactions]:
            top_transactions.append(temp)
        first_index += 1
        per_80 -= 1

    while per_12 > 0 and middle_index < len(blockchain.transactions):
        temp=sorted_transactions[middle_index]
        if temp['transaction_id'] not in [trans['transaction_id'] for trans in top_transactions]:
            top_transactions.append(temp)
        middle_index += 1
        per_12 -= 1

    while per_8 > 0 and last_index >= 0:
        temp=sorted_transactions[last_index]
        if temp['transaction_id'] not in [trans['transaction_id'] for trans in top_transactions]:
            top_transactions.append(temp)
        last_index -= 1
        per_8 -= 1
    # # print(top_transactions)
    # transaction_amounts = [transaction['amount'] for transaction in top_transactions]
    # print(transaction_amounts)
    response = {'highest_transactions': top_transactions}
    return jsonify(response), 200

#helper to calculate 80% 12 % 8% of number 
def calculate_integer_percentages(number):
    """
    This function takes a number as input, calculates the integer parts of 80%, 12%, and 8% of that number,
    and ensures their sum equals the original number.
    """
    percent_80 = int(number * 0.8)
    percent_12 = int(number * 0.12)
    percent_8 = int(number * 0.08)
    
    # Calculate the difference to adjust the sum to be equal to the original number
    total = percent_80 + percent_12 + percent_8
    difference = number - total
    
    # Adjust the values to make sure their sum is equal to the original number
    if difference > 0:
        percent_80 += difference
    elif difference < 0:
        percent_80 += difference

    return percent_80, percent_12, percent_8
# remove highest k transaction 
# Flask route to remove the highest k transactions from the transaction pool
@app.route('/remove_highest_transactions', methods=['POST'])
def remove_highest_transactions():
    data = request.get_json()
    top_transactions = data.get('highest_transactions', [])

    # Remove the highest k transactions from the pool
    for transaction in top_transactions:
        if transaction in blockchain.transactions:
            blockchain.transactions.remove(transaction)
    
    response = {'message': 'Highest k transactions removed from the transaction pool'}
    return jsonify(response), 200
## new  1
@app.route('/remove_all_trans', methods=['POST'])
def remove_all_trans():
    data = request.get_json()
    top_transactions = data.get('highest_transactions', [])
    response = requests.post(f'http://127.0.0.1:5000/remove_highest_transactions',json={'highest_transactions': top_transactions})
    for node in blockchain.nodes:
        requests.post(f'http://{node}/remove_highest_transactions',json={'highest_transactions': top_transactions})
    if response.status_code != 200:
        return jsonify({'message': 'can not remove highest transaction'}), 500
    else :
        return jsonify({'message': 'removed all highest transaction '}), 200
    
    # Create an event object

#my 
@app.route('/mine_block_with_transactions', methods=['GET'])
def mine_block_with_transactions():
    n_high = request.args.get('tpb', type=int) # n_high is transaction per block
    flag = request.args.get('flag', type=int) # flag for throughput put into [] or not 1 is yes
    current_node = '127.0.0.1:5000'
    if blockchain.nodes:
        mining_node = choice(list(blockchain.nodes) + [current_node])
    else:
        mining_node = current_node

    
    start_time=time.time()

    # Check if the selected node is running
    # step 1: store highest transaction
    # Send a request to the selected node to get the top  highest transactions

    #new select 80%12%8% using tpb it should return selected transaction 
    response = requests.get(f'http://{mining_node}/get_highest_transactions?k={n_high}')

    if response.status_code != 200:
        return jsonify({'message': 'Error getting highest transactions from the mining node'}), 500

    top_transactions = response.json()['highest_transactions']

    # step 2: remove highest transaction
    # it should take set from that set remove transaction from all nodes not tpb not return anything
    response = requests.post('http://127.0.0.1:5000/remove_all_trans', json={'highest_transactions': top_transactions})
    if response.status_code != 200:
        return jsonify({'message': 'can not remove highest transaction'}), 500
    
    # step3: get remaining transaction
    response = requests.get(f'http://{mining_node}/get_transaction_pool')
    remaining_transaction = response.json()['transactions']

    # step4: mining node transaction contains only highest transaction
    response = requests.post(f'http://{mining_node}/set_the_transaction',
                            json={'top_transactions': top_transactions})

    # start_time=time.time()
    # step5: random node mine a block
    response = requests.get(f'http://{mining_node}/mine_block')

    # Step 6: mining node contains remaining transactions
    response = requests.post(f'http://{mining_node}/set_the_transaction',
                             json={'top_transactions': remaining_transaction})
    #throughput work
    end_time = time.time()
    block_mining_time = end_time - start_time
    if flag==1:
        response = requests.post(f'http://{mining_node}/add_time',
                        json={'block_time': block_mining_time, 'tpb': n_high})
    
    # Set the event indicating block mining is complete

    return jsonify({'msg': 'successfully', 'top-transaction': top_transactions}), 200
    

# helper add time into throughput
@app.route('/add_time', methods=['POST'])
def add_time():
    try:
        block_time = request.json['block_time']
        tpb = request.json['tpb']  # transactions per block
        throughput = tpb / block_time  # Calculate throughput
        if throughput > 0:
            blockchain.throughput.append(throughput)
        return jsonify({'message': 'Throughput added successfully'}), 200
    except KeyError:
        return jsonify({'error': 'Block time or transactions per block not provided in the request'}), 400
# Route to get the throughput list
@app.route('/get_throughput_list', methods=['GET'])
def get_throughput_list():
    throughput_list = blockchain.throughput
    response = {'throughput': throughput_list}
    return jsonify(response), 200

#helper of mine_block_with_transactions
@app.route('/set_the_transaction', methods=['POST'])
def set_the_transaction():
    data = request.get_json()
    blockchain.transactions = data.get('top_transactions')

    response = {'message': 'Remaining transactions added to the Blockchain'}
    return jsonify(response), 200

# Route to calculate the average throughput
@app.route('/average_throughput', methods=['GET'])
def average_throughput():
        # output in excel 
    throughput_list = blockchain.throughput
    if not throughput_list:
        response = {'average_throughput': 0.0}
        return jsonify(response), 200
    average = sum(throughput_list) / len(throughput_list)
    response = {'average_throughput': average}
    return jsonify(response), 200

# n is transaction/block 
#and it send the required transaction request
@app.route('/n_mine_block_with_transactions' , methods=["GET"])
def n_mine_block_with_transactions():
    n = request.args.get('tpb', type=int)

    # output in excel 
    df=pd.read_excel('my.xlsx')
    df.loc[df['Throughput'].count(),'Transaction per block']=n
    tpb=n
    i=0
    n =(int)(len(blockchain.transactions)/n)
    df.loc[df['Throughput'].count(),'Total Transaction']=len(blockchain.transactions)
    # n is the block contain n transaction 
    # mine block till the size of mempool is >=n
    for i in range(n):
        requests.get(f'http://127.0.0.1:5000/mine_block_with_transactions?tpb={tpb}&flag={1}')
    
    df.loc[df['Throughput'].count(),'Block mine']=i+1
    df.to_excel('my.xlsx', index=False)
    return jsonify({'message': f'mine  {i+1} block '}), 200

# Flask route to get all transactions in the transaction pool
@app.route('/get_transaction_pool', methods=['GET'])
def get_transaction_pool():
    response = {'transactions': blockchain.transactions,
                'count':len(blockchain.transactions)}
    return jsonify(response), 200

# Flask route to calculate and put average throughput into Excel
@app.route('/put_avg_in_excel', methods=['GET'])
def put_avg_in_excel():
    df = pd.read_excel('my.xlsx')
    # response=average_throughput()
    response = requests.get(f'http://{request.host}/average_throughput')
    output=0
    if response.status_code == 200:
        output+=response.json()['average_throughput']

    # Send request to all nodes to calculate their average throughput
    i=1
    for node in blockchain.nodes:
        response = requests.get(f'http://{node}/average_throughput')
        if response.status_code == 200:
            output+=response.json()['average_throughput']
            i+=1
    df.loc[df['Throughput'].count(),'Throughput']=output/i
    df.loc[df['nodes'].count(),'nodes']=i
    df.to_excel('my.xlsx', index=False)

    return jsonify({'message': 'Average throughput added to the Excel file'}), 200




# auto connecting to all nodes  use auto_add
@app.route('/auto_connect', methods=['GET'])
def auto_connect():
    n = request.args.get('n', type=int)
    n=n-1 #starting from 0
    for i in range(n+1):
        requests.get(f'http://127.0.0.1:{5000 + i}/auto_add?n={n}')
    
    # start sending transaction 
    # start_sending_transactions()
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


@app.route('/execute_all', methods=['GET'])
def execute_all():
    tpb = request.args.get('tpb', type=int)
    # #send at least tpb*5 transaction
    # response=requests.get(f'http://{request.host}/n_transaction?n={tpb*5}')
    # if response.status_code!=200:
    #     return jsonify({
    #         "msg":"can not send transaction tpb*5"
    #     }),200
    # Clear throughput for all nodes
    blockchain.throughput=[]
    for node in blockchain.nodes:
        # Send a request to each node to clear their throughput list
            response = requests.get(f'http://{node}/clear_throughput_local')
            if response.status_code != 200:
                return jsonify({'message': f'Error clearing throughput for node {node}'}), 400
    
    response_4 = requests.get(f'http://{request.host}/n_mine_block_with_transactions?tpb={tpb}')
    if response_4.status_code != 200:
        return jsonify({'message': 'Error mining n block'}), 400
    
    response_5 = requests.get(f'http://{request.host}/put_avg_in_excel')
    
    # i=random.randint(2,5)
    # time.sleep(4)  #time dele for add transaction 
    
    return jsonify({
                    'message': 'Output added to the Excel file',
                    'transaction per block':tpb
                    }), 200


# Helper function to clear throughput for a single node
@app.route('/clear_throughput_local', methods=['GET'])
def clear_throughput_local():
    blockchain.throughput = []
    return jsonify({'message': 'Throughput cleared locally'}), 200



# continuous transaction
@app.route('/continuous_transaction', methods=['GET'])
def continuous_transaction():
    # i=1
    incr = 15
    tpb = 5
    # while i<500:
    while True:
        # n = random.randint(1, 5)
        response = requests.get(f'http://{request.host}/n_transaction?n={1}')
        if response.status_code != 200:
            return jsonify({'message': 'transaction not added in mempool'}), 400
        
        # Introduce some delay between consecutive transactions
        # time.sleep(1)

        # 2000 transactions then 5000 transactions and so on
        if len(blockchain.transactions) == incr and incr <= 15000:
            incr =incr+20
            #tpb=tpb+5
            response=requests.get(f'http://{request.host}/execute_all?tpb={tpb}')
            if response.status_code != 200:
                return jsonify({'message': 'execute_all sending request fail'}), 400
        # i+=1
# Add a final return statement if needed after the loop
# return jsonify({'message': 'Continuous transactions completed successfully'}), 200


# continuous mining
@app.route('/continuous_mining', methods=['GET'])
def continuous_mining():
    tpb=5
    while True:
        n=random.randint(1,2)
        response=requests.get(f'http://{request.host}/mine_block_with_transactions?tpb={tpb}&flag={0}')
        if response.status_code!=200:
            return jsonify({'message': 'block  not mined'}), 400
        
        # Introduce some delay between consecutive transactions
        time.sleep(4)
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

