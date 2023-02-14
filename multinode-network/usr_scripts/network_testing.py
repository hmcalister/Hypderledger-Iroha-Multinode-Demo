#! /bin/python

"""
Test multinode Iroha network with several mundane scenarios, with logging of outputs
This module assumes a fresh network, so make sure to run manage-network restart
Also note these tests are ordered. Some tests create objects that will be used by later tests
Do NOT employ pytest-random, as tests will fail. This is intended
"""
from operator import le
from IrohaUtils import *
import pytest
import logging
import socket
import sys

def node_locations():
    return[
        (IROHA_HOST_ADDR_1, int(IROHA_PORT_1)),
        (IROHA_HOST_ADDR_2, int(IROHA_PORT_2)),
        (IROHA_HOST_ADDR_3, int(IROHA_PORT_3)),
        (IROHA_HOST_ADDR_4, int(IROHA_PORT_4)),
    ]


@pytest.fixture(name="node_locations")
def node_locations_fixture():
    return node_locations()


def node_grpcs():
    return [net_1, net_2, net_3, net_4]

@pytest.fixture(name="node_grpcs")
def node_grpcs_fixture():
    return node_grpcs()


def test_node_reachable(node_locations):
    """
    Test that a node can be reached on the address:port specified
    """

    for i, location in enumerate(node_locations):
        logging.info(f"ATTEMPTING TO REACH NODE_{i+1}")
        logging.debug(f"Trying to reach location f{location}")
        a_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        a_socket.settimeout(1)
        conn_result = a_socket.connect_ex(location)
        a_socket.close()
        logging.debug(f"CONNECTION RESULT {conn_result}")
        assert conn_result == 0
        logging.info("\tCONNECTION SUCCESS")


def test_create_domain():
    """
    Test that an admin can create a domain
    """

    logging.info("ATTEMPTING TO CREATE DOMAIN pytest")
    commands = [
        iroha.command('CreateDomain', domain_id='pytest', default_role='user')
    ]

    tx = IrohaCrypto.sign_transaction(
        iroha.transaction(commands), ADMIN_PRIVATE_KEY)
    logging.debug(tx)
    status = send_transaction(tx, net_1)
    logging.debug(status)
    assert status[0] == "COMMITTED"
    logging.info("\tSUCCESSFULLY CREATED DOMAIN")


def test_create_asset():
    """
    Test that an admin can create an asset on a domain
    """

    logging.info("ATTEMPTING TO CREATE ASSET coin#pytest")
    commands = [
        iroha.command('CreateAsset', asset_name='coin',
                      domain_id='pytest', precision=2)
    ]

    tx = IrohaCrypto.sign_transaction(
        iroha.transaction(commands), ADMIN_PRIVATE_KEY)
    logging.debug(tx)
    status = send_transaction(tx, net_1)
    logging.debug(status)
    assert status[0] == "COMMITTED"
    logging.info("\tSUCCESSFULLY CREATED ASSET")


def test_add_asset():
    """
    Test if an admin can add an asset to their account in a domain
    """

    logging.info("ATTEMPTING TO ADD 1000 coin#pytest TO admin@test")
    tx = iroha.transaction([
        iroha.command('AddAssetQuantity',
                      asset_id='coin#pytest', amount='1000.00')
    ])
    tx = IrohaCrypto.sign_transaction(tx, ADMIN_PRIVATE_KEY)
    logging.debug(tx)
    status = send_transaction(tx, net_1)
    logging.debug(status)
    assert status[0] == "COMMITTED"
    logging.info("\tSUCCESSFULLY ADDED ASSET")


def test_create_users(node_grpcs):
    """
    Test that an admin can create users in a domain, and check this for one user per node
    """

    logging.info("ATTEMPTING TO CREATE USERS: ONE USER PER NODE")

    for i, node_grpc in enumerate(node_grpcs):
        logging.info(f"\tCREATE USER{i+1} ON NODE_{i+1}")
        user_private_key = IrohaCrypto.private_key()
        user_public_key = IrohaCrypto.derive_public_key(user_private_key)
        tx = iroha.transaction([
            iroha.command('CreateAccount', account_name=f'user{i+1}', domain_id='pytest',
                          public_key=user_public_key)
        ])
        IrohaCrypto.sign_transaction(tx, ADMIN_PRIVATE_KEY)
        logging.debug(tx)
        status = send_transaction(tx, node_grpc)
        logging.debug(status)
        assert status[0] == "COMMITTED"
        logging.info(f"\t\tSUCCESSFULLY CREATED USER{i+1}")


def test_transfer_asset_to_users(node_grpcs):
    """
    Test that an admin can transfer assets to other users
    """

    logging.info("ATTEMPT TO TRANSFER coin#pytest FROM ADMIN TO USERS")
    
    for i, node_grpc in enumerate(node_grpcs):
        logging.info(f"\tTRANSFER TO USER{i+1} VIA NODE_{i+1}")
        tx = iroha.transaction([
            iroha.command('TransferAsset', src_account_id='admin@test', dest_account_id=f'user{i+1}@pytest',
                          asset_id='coin#pytest', description='Top Up', amount=f'{(i+1)*1.11}')
        ])
        IrohaCrypto.sign_transaction(tx, ADMIN_PRIVATE_KEY)
        logging.debug(tx)
        status = send_transaction(tx, node_grpc)
        logging.debug(status)
        assert status[0] == "COMMITTED"
        logging.info(f"\t\tSUCCESSFULLY TRANSFERRED ASSET TO USER{i+1}")

def test_query_on_asset(node_grpcs):
    """
    Test that an admin can query an asset property
    """
    logging.info("QUERY ASSET coin#pytest OVER EACH NODE")

    for i, node_grpc in enumerate(node_grpcs):
        logging.info(f"\tQUERY OVER NODE_{i+1}")
        query = iroha.query('GetAssetInfo', asset_id='coin#pytest')
        IrohaCrypto.sign_query(query, ADMIN_PRIVATE_KEY)
        response = node_grpc.send_query(query)
        data = response.asset_response.asset
        logging.debug(data)
        assert str(data) == 'asset_id: "coin#pytest"\ndomain_id: "pytest"\nprecision: 2\n'
        logging.info(f"\t\tSUCCESSFULLY QUERIED ASSET ON NODE_{i+1}")

if __name__=="__main__":
    #logging.basicConfig(level=logging.DEBUG)
    logging.basicConfig(level=logging.INFO)
    logging.debug("STARTING BASIC NETWORK TESTS")

    input(f"{bcolors.OKGREEN}Test if all nodes are reachable on Iroha ports{bcolors.ENDC}")
    test_node_reachable(node_locations())
    print(f"{'-'*80}\n\n")

    input(f"{bcolors.OKGREEN}Test if admin can create a domain{bcolors.ENDC}")
    test_create_domain()
    print(f"{'-'*80}\n\n")

    input(f"{bcolors.OKGREEN}Test if an admin can create an asset in the new domain{bcolors.ENDC}")
    test_create_asset()
    print(f"{'-'*80}\n\n")

    input(f"{bcolors.OKGREEN}Test if an admin can add the new asset to their account{bcolors.ENDC}")
    test_add_asset()
    print(f"{'-'*80}\n\n")

    input(f"{bcolors.OKGREEN}Test if an admin can create new users, using each node{bcolors.ENDC}")
    test_create_users(node_grpcs())
    print(f"{'-'*80}\n\n")

    input(f"{bcolors.OKGREEN}Test if an admin can transfer the new asset to each new account{bcolors.ENDC}")
    test_transfer_asset_to_users(node_grpcs())
    print(f"{'-'*80}\n\n")

    input(f"{bcolors.OKGREEN}Test if an admin can query the new asset on each node{bcolors.ENDC}")
    test_query_on_asset(node_grpcs())
    print(f"{'-'*80}\n\n")

    logging.debug("FINISHED BASIC NETWORK TESTS")
    logging.debug("SAVING LOGS TO network_testing DIRECTORY")

    logging.info("SAVE BLOCKCHAIN LOGS TO network_testing_logs/")
    for i, grpc in enumerate(node_grpcs()):
        logging.info(f"\tSAVING LOGS OF node{i+1}")
        log_all_blocks(grpc, f"node{i+1}.log", "network_testing_logs")
