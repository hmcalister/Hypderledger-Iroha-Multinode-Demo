Some testing of the network is available using pytest.

Please ensure the network is in a "fresh" state by running `manage-network restart` in the parent directory.

Run `pytest -x -rA -v {testfile}` to run some unit tests on the iroha multinode network.
- `pytest` is a python testing program. It will automatically read the `network_testing.py` file and determine how to apply the tests within
- `-x` means to break from the program when one test fails. This is done because later tests rely on earlier tests (e.g. one of the first tests is creating a domain. If this test fails then the next test, creating an asset in that domain, will also fail)
- `-rA` means we will get more information on all tests at the end of testing, rather than just the failed tests.
- `-v` means verbose, and will display the tests running as they run. I find this more useful and interesting than the default "dot" notation.

You can also run these tests manually using `python {testfile}`. This will run the tests in your python environment and wait for your input between tests. This way, you can inspect the logging info and debug statements if need be. Running in this way also generates logs, which are stored in the respective log directories. Currently, the logs are simply the JSON representation of the blockchain from each node.

The test files offered are:

`network_testing.py` is a set of unit tests that will demonstrate that the network is usable in cases of expected behavior. For example, creating new assets and users, and recording transactions. Nothing is pushed to the limit here but this set of tests provides a good example of the network *working*.

`malicious_client.py` is a set of unit tests that demonstrate the network maintaining consensus when a client is behaving poorly. This set of tests includes actions such as replay attacks, double spending, and attempting to circumvent permissions. These tests demonstrate the blockchain is robust in the face of a malicious client, as the only attack that succeeds requires a private key to be compromised, which is indicative of a greater underlying problem.

Also, please note these tests were developed in python 3.10.0 and have not been checked on other versions. If you find that the tests fail on your machine, this may be the culprit, although I have not employed any 3.10 specific features.