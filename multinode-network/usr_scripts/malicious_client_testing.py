#! /bin/python

"""
Test multinode Iroha network with several scenarios of a malicious client, with logging of outputs
This module assumes a fresh network, so make sure to run manage-network restart
Also note these tests are ordered. Some tests create objects that will be used by later tests
Do NOT employ pytest-random, as tests will fail. This is intended

We start this test by setting up a new domain (pytest) with a basic_role that can only transfer and receive assets
There are users a, b, and c. Each will start with 100 coins
Throughout these tests, user_a will be considered as the malicious one. Other users will remain "honest"
"""
from time import sleep
from _pytest.fixtures import yield_fixture
from iroha import primitive_pb2
from IrohaUtils import *
import pytest
import logging
import socket


user_a = new_user("user_a", "pytest")
user_b = new_user("user_b", "pytest")
user_c = new_user("user_c", "pytest")

def node_locations():
    return[
        (IROHA_HOST_ADDR_1, int(IROHA_PORT_1)),
        (IROHA_HOST_ADDR_2, int(IROHA_PORT_2)),
        (IROHA_HOST_ADDR_3, int(IROHA_PORT_3)),
        (IROHA_HOST_ADDR_4, int(IROHA_PORT_4)),
    ]

@pytest.fixture(scope="session", name="node_locations")
def node_locations_fixture():
    return node_locations()

def node_grpcs():
    return [net_1, net_2, net_3, net_4]

@pytest.fixture(name="node_grpcs")
def node_grpcs_fixture():
    return node_grpcs()


@pytest.fixture(scope="session", autouse=True)
def set_up_test_environment_fixture(node_locations):
    set_up_test_environment(node_locations)

def set_up_test_environment(node_locations):
    """
    Ensure network is up and create all needed domains, assets, accounts etc for testing
    """

    # Check if network is reachable -------------------------------------------
    logging.info("ENSURE NETWORK IS UP")
    for i, location in enumerate(node_locations):
        logging.info(f"ATTEMPTING TO REACH NODE_{i+1}")
        logging.debug(f"Trying to reach location f{location}")
        a_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        a_socket.settimeout(60)
        conn_result = a_socket.connect_ex(location)
        a_socket.close()
        logging.debug(f"CONNECTION RESULT {conn_result}")
        assert conn_result == 0
        logging.info("\tCONNECTION SUCCESS")

    logging.info("NETWORK IS UP")
    sleep(3)

    # Role Creation -----------------------------------------------------------
    logging.info("CREATING ROLES")
    commands = [
        # A basic user that can send and receive assets, and that's all
        # Will use "can grant..." to allow admin to reset the account balances between tests
        iroha_admin.command("CreateRole", role_name="basic_user", permissions=[
            primitive_pb2.can_receive,
            primitive_pb2.can_transfer,
            primitive_pb2.can_grant_can_transfer_my_assets
        ])
    ]
    tx = IrohaCrypto.sign_transaction(
        iroha_admin.transaction(commands), ADMIN_PRIVATE_KEY)
    logging.debug(tx)
    status = send_transaction(tx, net_1)
    logging.debug(status)
    assert status[0] == "COMMITTED"
    logging.info("ROLES CREATED")

    # Domain Creation ---------------------------------------------------------
    logging.info("CREATING DOMAIN")
    commands = [
        iroha_admin.command('CreateDomain', domain_id='pytest', default_role='basic_user')
    ]
    tx = IrohaCrypto.sign_transaction(
        iroha_admin.transaction(commands), ADMIN_PRIVATE_KEY)
    logging.debug(tx)
    status = send_transaction(tx, net_1)
    logging.debug(status)
    assert status[0] == "COMMITTED"
    logging.info("DOMAIN CREATED")

    # Asset Creation ----------------------------------------------------------
    logging.info("CREATING ASSETS")
    commands = [
        iroha_admin.command('CreateAsset', asset_name='coin',
                      domain_id='pytest', precision=2)
    ]
    tx = IrohaCrypto.sign_transaction(
        iroha_admin.transaction(commands), ADMIN_PRIVATE_KEY)
    logging.debug(tx)
    status = send_transaction(tx, net_1)
    logging.debug(status)
    assert status[0] == "COMMITTED"
    logging.info("ASSETS CREATED")

    # User Creation -----------------------------------------------------------
    logging.info("CREATING USERS")
    commands = [
        # Create users a,b,c
        iroha_admin.command('CreateAccount', account_name=user_a["name"], domain_id='pytest',
                          public_key=user_a["public_key"]),
        iroha_admin.command('CreateAccount', account_name=user_b["name"], domain_id='pytest',
                          public_key=user_b["public_key"]),
        iroha_admin.command('CreateAccount', account_name=user_c["name"], domain_id='pytest',
                          public_key=user_c["public_key"])
    ]
    tx = IrohaCrypto.sign_transaction(
        iroha_admin.transaction(commands), ADMIN_PRIVATE_KEY)
    logging.debug(tx)
    status = send_transaction(tx, net_1)
    logging.debug(status)
    assert status[0] == "COMMITTED"
    logging.info("USERS CREATED")

    # Allow admin to transfer user assets -------------------------------------
    logging.info("ALLOW ADMIN TO TRANSFER USER ASSETS")
    for user in [user_a, user_b, user_c]:
        logging.info(f"{user['id']} GRANTS ADMIN TRANSFER PERMISSION")
        tx = user["iroha"].transaction([
            user["iroha"].command("GrantPermission", account_id="admin@test", permission=primitive_pb2.can_transfer_my_assets)
        ], creator_account=user["id"])
        tx = IrohaCrypto.sign_transaction(
            tx, user["private_key"])
        logging.debug(tx)
        status = send_transaction(tx, net_1)
        logging.debug(status)
        assert status[0] == "COMMITTED"
        logging.info(f"{user['id']} SUCCESSFULLY GRANTED PERMISSION TO ADMIN")

    # Asset Quantity Creation and Transfer ------------------------------------
    logging.info("ADDING ASSETS TO USERS")
    logging.info("ATTEMPTING TO ADD 1000 coin#pytest TO admin@test")
    tx = iroha_admin.transaction([
        iroha_admin.command('AddAssetQuantity',
                      asset_id='coin#pytest', amount='1000.00')
    ])
    tx = IrohaCrypto.sign_transaction(tx, ADMIN_PRIVATE_KEY)
    logging.debug(tx)
    status = send_transaction(tx, net_1)
    logging.debug(status)
    assert status[0] == "COMMITTED"
    logging.info("SUCCESSFULLY ADDED coin#pytest TO admin@test")

    logging.info("TRANSFERING ASSET TO USERS")
    commands = [
        # Create users a,b,c
        iroha_admin.command('TransferAsset', src_account_id='admin@test', dest_account_id=user_a["id"],
                          asset_id='coin#pytest', amount="100"),
        iroha_admin.command('TransferAsset', src_account_id='admin@test', dest_account_id=user_b["id"],
                          asset_id='coin#pytest', amount="100"),
        iroha_admin.command('TransferAsset', src_account_id='admin@test', dest_account_id=user_c["id"],
                          asset_id='coin#pytest', amount="100")
    ]
    tx = IrohaCrypto.sign_transaction(
        iroha_admin.transaction(commands), ADMIN_PRIVATE_KEY)
    logging.debug(tx)
    status = send_transaction(tx, net_1)
    logging.debug(status)
    assert status[0] == "COMMITTED"
    logging.info("TRANSFERAL OF ASSETS COMPLETE")

    logging.info("SET UP COMPLETE")

def test_setup():
    """
    A little hack to ensure the setup is noted when using pytest -v
    """

    assert True

@pytest.fixture(autouse=True)
def set_user_asset_balance_fixture():
    set_user_asset_balance()
    yield

@trace
def set_user_asset_balance():
    """
    Set the asset balance of all users to 100 before each test
    """

    logging.info("RESET ACCOUNT BALANCES")

    commands = []
    for user in [user_a, user_b, user_c]:
        logging.debug(f"SETTING {user['id']} BALANCE")
        user_assets = get_user_assets(user['id'])
        logging.debug(f"User assets: {user_assets}")
        # Because there is only one asset, we can hardcode index 0
        user_coin_balance = user_assets[0].balance
        logging.debug(f"User coin#pytest balance {user_coin_balance}")
        # Give admin 100, add 100 coins to user
        new_commands = [
            iroha_admin.command('AddAssetQuantity',
                      asset_id='coin#pytest', amount='100'),
            iroha_admin.command('TransferAsset', src_account_id='admin@test', dest_account_id=user["id"],
                            asset_id='coin#pytest', description="Top up 100 coin", amount="100")
        ]

        #Note the Iroha considers a movement of 0 coins stateless invalid, so lets handle this case
        if user_coin_balance != '0':
            # subtract balance from user
            new_commands.append(
            iroha_admin.command('TransferAsset', src_account_id=user["id"], dest_account_id='admin@test',
                        asset_id="coin#pytest", description="Transfer excess user balance back", amount=f"{user_coin_balance}")
            )
        for c in new_commands:
            commands.append(c)
        
    tx = IrohaCrypto.sign_transaction(
        iroha_admin.transaction(commands), ADMIN_PRIVATE_KEY)
    logging.debug(tx)
    status = send_transaction(tx, net_1)
    logging.debug(status)
    assert status[0] == "COMMITTED"
    for user in [user_a, user_b, user_c]:
        user_assets = get_user_assets(user['id'])
        assert str(user_assets) == f'[asset_id: "coin#pytest"\naccount_id: "{user["id"]}"\nbalance: "100"\n]'
    logging.debug(f"USERS BALANCE SET")

# Attempt an honest spend to test
def test_honest_transfer():
    """
    Test that two honest accounts can actually transfer funds between them
    User B will send 10 coin to User C
    """

    logging.info("HONEST TRANSFER 10 COIN FROM B to C")
    command = [
        user_b["iroha"].command("TransferAsset", src_account_id=user_b["id"], dest_account_id=user_c["id"],
                            asset_id="coin#pytest", amount="10")
    ]
    tx = IrohaCrypto.sign_transaction(
        user_b["iroha"].transaction(command), user_b["private_key"])
    logging.debug(tx)
    status = send_transaction(tx, net_1)
    logging.debug(status)
    assert status[0] == "COMMITTED"

    # Now check that both parties have the correct asset total
    user_b_assets = get_user_assets(user_b["id"])
    user_c_assets = get_user_assets(user_c["id"])
    assert str(user_b_assets) == f'[asset_id: "coin#pytest"\naccount_id: "{user_b["id"]}"\nbalance: "90"\n]'
    assert str(user_c_assets) == f'[asset_id: "coin#pytest"\naccount_id: "{user_c["id"]}"\nbalance: "110"\n]'
    logging.info("HONEST TRANSFER COMPLETE")

# Attempt to commit Double Spending
def test_double_spending_same_transaction():
    """
    User A will attempt to double spend their 100 coins to both user B and C at the same time
    """

    logging.info("ATTEMPTING DOUBLE SPEND ONE TRANSACTION")
    tx = user_a["iroha"].transaction([
        user_a["iroha"].command('TransferAsset', src_account_id=f'{user_a["id"]}', dest_account_id=f'{user_b["id"]}',
                          asset_id='coin#pytest', amount="100"),
        user_a["iroha"].command('TransferAsset', src_account_id=f'{user_a["id"]}', dest_account_id=f'{user_c["id"]}',
                          asset_id='coin#pytest', amount="100"),
        
    ])
    tx = IrohaCrypto.sign_transaction(tx, user_a["private_key"])
    logging.debug(tx)
    status = send_transaction(tx, net_1)
    logging.debug(status)
    assert status[0] == "REJECTED"
    logging.info("TRANSACTION REJECTED")

    # Now check no coin has left user A's account or entered user B or C
    for user in [user_a, user_b, user_c]:
        user_assets = get_user_assets(user['id'])
        assert str(user_assets) == f'[asset_id: "coin#pytest"\naccount_id: "{user["id"]}"\nbalance: "100"\n]'

    logging.info("NO COIN HAS BEEN TRANSFERRED")    

def test_double_spending_two_transactions():
    """
    User A will attempt to double spend their 100 coins to user B and user C at the same time,
    using two different transactions to two different peers

    It is possible that using asyncio, multiprocessing, or threading could help with this, as 
    we want to ensure the two transactions reach the peers at roughly the same time so the network does not process one over the other
    """

    logging.info("ATTEMPTING DOUBLE SPEND ON TWO TRANSACTIONS")
    tx_1 = user_a["iroha"].transaction([
        user_a["iroha"].command('TransferAsset', src_account_id=f'{user_a["id"]}', dest_account_id=f'{user_b["id"]}',
                          asset_id='coin#pytest', amount="100")
    ])
    tx_2 = user_a["iroha"].transaction([
        user_a["iroha"].command('TransferAsset', src_account_id=f'{user_a["id"]}', dest_account_id=f'{user_c["id"]}',
                          asset_id='coin#pytest', amount="100")
    ])

    tx_1 = IrohaCrypto.sign_transaction(tx_1, user_a["private_key"])
    tx_2 = IrohaCrypto.sign_transaction(tx_2, user_a["private_key"])

    logging.debug(tx_1)
    logging.debug(tx_2)
    
    # We cannot use IrohaUtils.send_transaction as this is blocking until a final status is found
    # Unless swapping to threading or asyncio this means there will be some code duplication here
    hex_hash_1 = binascii.hexlify(IrohaCrypto.hash(tx_1))
    hex_hash_2 = binascii.hexlify(IrohaCrypto.hash(tx_2))
    logging.debug('Transaction hash = {}, creator = {}'.format(
        hex_hash_1, tx_1.payload.reduced_payload.creator_account_id))
    logging.debug('Transaction hash = {}, creator = {}'.format(
        hex_hash_2, tx_2.payload.reduced_payload.creator_account_id))
    # Actually send the transactions, one after another
    net_1.send_tx(tx_1)
    net_2.send_tx(tx_2)

    # Get the status's of each transactions
    last_status = [None, None]
    logging.debug("TX_1 STATUS")
    for status in net_1.tx_status_stream(tx_1):
        logging.debug(status)
        last_status[0] = status
    logging.debug("TX_2 STATUS")
    for status in net_2.tx_status_stream(tx_2):
        logging.debug(status)
        last_status[1] = status
    # Sort the list of last status so we can check one commit and one reject
    last_status.sort()

    assert last_status[0][0]=="COMMITTED" and last_status[1][0]=="REJECTED"
    logging.info("ONE SPEND OCCURRED, DOUBLE SPEND PREVENTED")

# Attempt to create new role
def test_create_role_without_permission():
    """
    Attempts to create a new role with elevated permissions
    """

    logging.info("ATTEMPTING TO CREATE NEW ROLE AS USER_A")
    commands = [
        # A new user that can add asset quantities, which is BAD 
        user_a["iroha"].command("CreateRole", role_name="new_user", permissions=[
            primitive_pb2.can_receive,
            primitive_pb2.can_transfer,
            primitive_pb2.can_add_asset_qty
        ])
    ]
    tx = IrohaCrypto.sign_transaction(
        user_a["iroha"].transaction(commands), user_a["private_key"])
    logging.debug(tx)
    status = send_transaction(tx, net_1)
    logging.debug(status)
    assert status[0] == "REJECTED"
    logging.info("NO ROLE CREATED")

# Attempt to create new account

def test_create_account_without_permission():
    """
    Attempts to create a new account, which could be an attack vector
    """

    logging.info("ATTEMPTING TO CREATE NEW USER AS USER_A")
    user_x = new_user("user_x", "pytest")
    commands = [
        user_a["iroha"].command('CreateAccount', account_name=f'{user_x["name"]}', domain_id='pytest',
                          public_key=user_x["public_key"]),
        
    ]
    tx = IrohaCrypto.sign_transaction(
        user_a["iroha"].transaction(commands), user_a["private_key"])
    logging.debug(tx)
    status = send_transaction(tx, net_1)
    logging.debug(status)
    assert status[0] == "REJECTED"
    logging.info("NO USER CREATED")

# Attempt signing under other user
def test_sign_as_other_user():
    """
    Attempts to create a transaction that gives A 10 of C's coins, posing as C but signs as A
    """

    logging.info("ATTEMPTING TO SIGN AS OTHER USER, OWN PRIVATE KEY")
    commands = [
        user_a["iroha"].command("TransferAsset", src_account_id=f'{user_c["id"]}', dest_account_id=f'{user_a["id"]}',
                    asset_id="coin#pytest", amount="10")
    ]

    tx = IrohaCrypto.sign_transaction(
        user_a["iroha"].transaction(commands), user_a["private_key"])

    logging.debug(tx)
    status = send_transaction(tx, net_1)
    logging.debug(status)
    assert status[0] == "REJECTED"
    logging.info("TRANSFER FAILED SUCCESSFULLY ;)")

# Attempt signing of transaction if private key compromised
def test_sign_as_other_user_compromised_private_key():
    """
    Attempt to create a transaction that gives A 10 of C's coins, posing as C but signs with C private key
    """

    logging.info("ATTEMPTING TO SIGN AS OTHER USER, COMPROMISED OTHER USER PRIVATE KEY")
    commands = [
        user_a["iroha"].command("TransferAsset", src_account_id=f'{user_c["id"]}', dest_account_id=f'{user_a["id"]}',
                    asset_id="coin#pytest", amount="10")
    ]

    # Because private key is compromised, blockchain identity user_c["iroha"] can be used
    tx = IrohaCrypto.sign_transaction(
        user_c["iroha"].transaction(commands), user_c["private_key"])

    logging.debug(tx)
    status = send_transaction(tx, net_1)
    logging.debug(status)
    assert status[0] == "COMMITTED"
    logging.info("TRANSFER SUCCESSFUL")

# Attempt replay attack of own transaction (?)
def test_replay_own_transaction():
    """
    Attempt to replay an already committed transaction i.e. using the same signing and hash
    This is kind of like a double spend
    Really this is just to test that unexpected behavior is not allowed, rather than being an actual attack
    """

    logging.info("ATTEMPTING REPLAY OF OWN TRANSACTION, BOTH VALID")

    commands = [
        user_a["iroha"].command("TransferAsset", src_account_id=f'{user_a["id"]}', dest_account_id=f'{user_c["id"]}',
                    asset_id="coin#pytest", amount="10")
    ]

    tx = IrohaCrypto.sign_transaction(
        user_a["iroha"].transaction(commands), user_a["private_key"])

    logging.debug(tx)
    status = send_transaction(tx, net_1)
    logging.debug(status)
    assert status[0] == "COMMITTED"
    logging.info("FIRST TRANSACTION SUCCESSFUL")
    logging.info("ATTEMPTING TO REPLAY TRANSACTION")
    logging.debug(tx)
    status = send_transaction(tx, net_1)
    logging.debug(status)
    # As it turns out, Iroha *will* accept a committed transaction again but returns the old response without replaying the effect 
    user_a_assets = get_user_assets(user_a['id'])
    user_c_assets = get_user_assets(user_c["id"])
    assert str(user_a_assets) == f'[asset_id: "coin#pytest"\naccount_id: "{user_a["id"]}"\nbalance: "90"\n]'
    assert str(user_c_assets) == f'[asset_id: "coin#pytest"\naccount_id: "{user_c["id"]}"\nbalance: "110"\n]'
    logging.info("REPLAY FAILED")

# Attempt replay attack of others transaction
def test_replay_others_transaction():
    """
    Attempt to inspect another users transaction and replay this, so the same transaction occurs multiple times
    """

    logging.info("ATTEMPTING REPLAY ATTACK OF OTHERS TRANSACTION")
    logging.debug("User C sends some coin to User B")
    commands = [
        user_c["iroha"].command("TransferAsset", src_account_id=f'{user_c["id"]}', dest_account_id=f'{user_b["id"]}',
                    asset_id="coin#pytest", amount="10")
    ]

    tx = user_c["iroha"].transaction(commands)

    signed_tx = IrohaCrypto.sign_transaction(
        tx, user_c["private_key"])

    logging.debug(signed_tx)
    status = send_transaction(signed_tx, net_1)
    logging.debug(status)
    assert status[0] == "COMMITTED"
    logging.info("FIRST TRANSACTION COMMITTED")
    logging.info("ATTEMPTING REPLAY")
    logging.debug("User A gets a copy of signed_tx, attempts replay")
    logging.debug(signed_tx)
    status = send_transaction(signed_tx, net_1)
    logging.debug(status)
    # Again, the response code is from the first transaction, so is "committed" but the effect takes hold once
    user_b_assets = get_user_assets(user_b['id'])
    user_c_assets = get_user_assets(user_c["id"])
    assert str(user_b_assets) == f'[asset_id: "coin#pytest"\naccount_id: "{user_b["id"]}"\nbalance: "110"\n]'
    assert str(user_c_assets) == f'[asset_id: "coin#pytest"\naccount_id: "{user_c["id"]}"\nbalance: "90"\n]'
    logging.info("REPLAY ATTACK FAILED")

def get_user_assets(user_id):
    """
    Get all of the assets of a user and return these

    Args:
        user_id (string): The identity of the user to query, already on the blockchain

    Returns:
        List of account asset: The assets of the specified user
    """

    query = iroha_admin.query("GetAccountAssets", account_id=f"{user_id}")
    IrohaCrypto.sign_query(query, ADMIN_PRIVATE_KEY)
    response = net_1.send_query(query)
    data = response.account_assets_response.account_assets
    return data

if __name__=="__main__":
    #logging.basicConfig(level=logging.INFO)
    logging.basicConfig(level=logging.INFO)

    # input(f"{bcolors.OKGREEN}{bcolors.ENDC}")

    # print(f"{'-'*80}\n\n")

    
    input(f"{bcolors.OKGREEN}Set up test environment with users, domain, and assets{bcolors.ENDC}")
    set_up_test_environment(node_locations())
    print(f"{'-'*80}\n\n")

    input(f"{bcolors.OKGREEN}Test that two honest users can transfer\nB sends 10 coins to C{bcolors.ENDC}")
    set_user_asset_balance()
    test_honest_transfer()
    print(f"{'-'*80}\n\n")

    input(f"{bcolors.OKGREEN}Test that a malicious client cannot double spend in the same transaction{bcolors.ENDC}")
    set_user_asset_balance()
    test_double_spending_same_transaction()
    print(f"{'-'*80}\n\n")

    input(f"{bcolors.OKGREEN}Test that a malicious client cannot double spend in different transactions{bcolors.ENDC}")
    set_user_asset_balance()
    test_double_spending_two_transactions()
    print(f"{'-'*80}\n\n")

    input(f"{bcolors.OKGREEN}Test that a malicious client cannot create a role with no permission{bcolors.ENDC}")
    set_user_asset_balance()
    test_create_role_without_permission()
    print(f"{'-'*80}\n\n")

    input(f"{bcolors.OKGREEN}Test that a malicious client cannot create a new user without permission{bcolors.ENDC}")
    set_user_asset_balance()
    test_create_account_without_permission()
    print(f"{'-'*80}\n\n")

    input(f"{bcolors.OKGREEN}Test that a malicious client cannot sign as a different user using malicious private key{bcolors.ENDC}")
    set_user_asset_balance()
    test_sign_as_other_user()
    print(f"{'-'*80}\n\n")

    input(f"{bcolors.OKGREEN}Test that a malicious client can sign as a different user when the private key has been compromised{bcolors.ENDC}")
    set_user_asset_balance()
    test_sign_as_other_user_compromised_private_key()
    print(f"{'-'*80}\n\n")

    input(f"{bcolors.OKGREEN}Test that a user cannot replay their own transactions{bcolors.ENDC}")
    set_user_asset_balance()
    test_replay_own_transaction()
    print(f"{'-'*80}\n\n")

    input(f"{bcolors.OKGREEN}Test that a malicious user cannot replay others transactions{bcolors.ENDC}")
    set_user_asset_balance()
    test_replay_others_transaction()
    print(f"{'-'*80}\n\n")

    logging.debug("FINISHED BASIC NETWORK TESTS")
    logging.debug("SAVING LOGS TO malicious_client_testing DIRECTORY")

    logging.info("SAVE BLOCKCHAIN LOGS TO malicious_client_testing_logs/")
    for i, grpc in enumerate(node_grpcs()):
        logging.info(f"\tSAVING LOGS OF node{i+1}")
        log_all_blocks(grpc, f"node{i+1}.log", "malicious_client_testing_logs")