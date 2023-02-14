# Hyperledger-Iroha-Multinode-Network

## Prerequisites
Ensure that your machine runs docker and docker-compose.

## Network Setup
From the multinode-network directory, run
`./manage-network up`
to start the iroha containers. Run
`./manage-network down`
to destroy those containers when finished.
Run
`./manage-network (pause|unpause)`
to pause or unpause the network respectively.

## Network topology
This multinode Iroha network runs four Iroha containers, each with its own Postgres database container. Currently, each node has its own folder (located in the `network` directory) that contains container specific configuration as well as the keys for that node. Also in the `network` directory is the `shared_init` directory, containing a shared genesis block for the blockchain and a few startup scripts that all containers can run to start. If a single container later needs to have a unique startup, this can be achieved by altering the entrypoint noted in the `docker-compose.yaml` file (also in the `network` folder).

Some python scripts exist in the `user_scripts` directory. These are for testing the Iroha network, and can be run either from the host machine (using the port forwarding set in the `docker-compose.yaml` file) or by copying this folder over to an Iroha node and running the python files from there. The `gamma749/iroha` Docker image has python3 and the python iroha package already installed, so there should be no issues in running the python scripts inside a container.

## References
Based heavily on the original github repository: https://github.com/Ta-SeenJunaid/Hyperledger-Iroha-Tutorial-with-Multi-Signature-and-Decentralized-Exchanged-in-Multi-Node-Set-up
