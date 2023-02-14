# Hyperledger Iroha Multinode Demo
## Hayden McAlister
---
This is an archive of a working example of a multinode blockchain network running Hyperledger Iroha. This example creates a new network with four nodes, then runs some tests to demonstrate functionality of the network, focusing on expected behavior.

---
## Dependencies
In these tests I have used docker, docker-compose, and python 3.10 (although python 3.X should work fine). You will also need the iroha python package, available by running `pip3 install iroha`

I have also used my own Hyperledger Iroha container, which has been pushed onto DockerHub under the [gamma749/iroha](https://hub.docker.com/repository/docker/gamma749/iroha) repo. 

---
## Running this example
This example can be run by moving to the `multinode-network` directory and using the `manage-network.sh` script.
- `./manage-network.sh up` will create a new four node network using docker compose

You will need a new network for each run through of the test, as the tests involve creating new, unique objects on the blockchain and will fail if those objects are already created. You can stop and create a new network using `./manage-network.sh restart`

From here, open a new terminal in the `usr_scripts` directory and run your choice of
- `python network_testing.py` for a more interactive/manual stepping through of the tests
	- Note that running the tests manually means you will get logging outputs. For more detailed logs, change the `network_testing.py` file to DEBUG logging. For less detailed (but still useful!) logs use the INFO logging. This option can be found on line 172.
- `pytest -x -rA network_testing.py` for an automatic set of testing using pytest
	- Note the `-x -rA` are some extra flags to give us information on passed tests and to stop testing on a single fail (as these tests are ordered and build on one another)

If you want to check your tests against what I got, I have saved the blockchain at the end of the `network_testing.py` script in the `network_testing_logs` directory. There are also screencasts of my runs of the tests in the `Videos` directory. (Sorry for the size!)

All code for the tests is available in the `network_testing.py` (and utility code is available in `IrohaUtils.py`) in the `usr_scripts` directory. The tests are reasonably self documenting, and perform the basic Iroha commands.
