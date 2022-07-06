import os
import pytest

from starkware.starknet.testing.starknet import Starknet
from sympy import true

# The path to the contract source code.
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
CONTRACT_FILE = os.path.join(TEST_DIR, "./imposter_game.cairo")

# Constants
FALSE = 0
TRUE = 1

def pytest_namespace():
    return {'contract': {}}

@pytest.fixture(autouse=True)
async def init_contract():
    # Create a new Starknet class that simulates the StarkNet
    # system.
    starknet = await Starknet.empty()

    # Deploy the contract.
    pytest.contract = await starknet.deploy(
        source=CONTRACT_FILE,
    )

############
# TEST CASES
############

@pytest.mark.asyncio
async def test_game_imposter_wins():
    contract = pytest.contract

    # Join the game
    await contract.join_game(saltedHashAddress=0x68650c6c5c, index=0).invoke()
    await contract.join_game(saltedHashAddress=0x68650c6c5d, index=1).invoke()
    await contract.join_game(saltedHashAddress=0x68650c6c5e, index=0).invoke()
    await contract.join_game(saltedHashAddress=0x68650c6c5f, index=3).invoke()
    await contract.join_game(saltedHashAddress=0x68650c6c6a, index=4).invoke()
    await contract.join_game(saltedHashAddress=0x68650c6c6b, index=5).invoke()
    await contract.join_game(saltedHashAddress=0x68650c6c6c, index=6).invoke()
    await contract.join_game(saltedHashAddress=0x68650c6c6d, index=7).invoke()
    await contract.join_game(saltedHashAddress=0x68650c6c6e, index=8).invoke()
    await contract.join_game(saltedHashAddress=0x68650c6c6f, index=9).invoke()

    # Check that players have joined
    players = await contract.view_players_hash().call()
    print(str(players.result.players))

    # Start the game
    await contract.start_game().invoke()

    assert true