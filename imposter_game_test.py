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
async def test_fails_too_many_players():
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
    with pytest.raises(Exception): 
      await contract.join_game(saltedHashAddress=0x68650c6c6e, index=8).invoke()

    # Check max players
    players = await contract.view_player_count().call()
    assert players.result.player_count == 8

@pytest.mark.asyncio
async def test_fails_not_enough_players():
    contract = pytest.contract

    # Join the game
    await contract.join_game(saltedHashAddress=0x68650c6c5c, index=0).invoke()
    await contract.join_game(saltedHashAddress=0x68650c6c5d, index=1).invoke()
    await contract.join_game(saltedHashAddress=0x68650c6c5e, index=0).invoke()

    # Start the game
    with pytest.raises(Exception):
      await contract.start_game(
        impostersMerkleRoot=0x68650c6c5c,
        collectPointsMerkleRoot=0x68650c6c5c,
        attackDelayMerkleRoot=0x68650c6c5c,
        doNothingMerkleRoot=0x68650c6c5c
      ).invoke()

@pytest.mark.asyncio
async def test_success_points_collected():
    contract = pytest.contract

    # Join the game
    await contract.join_game(saltedHashAddress=0x68650c6c5c, index=0).invoke()
    await contract.join_game(saltedHashAddress=0x68650c6c5d, index=1).invoke()
    await contract.join_game(saltedHashAddress=0x68650c6c5e, index=0).invoke()
    await contract.join_game(saltedHashAddress=0x68650c6c5f, index=3).invoke()

    # Check that players have joined
    players = await contract.view_players_hash().call()

    # Start the game
    await contract.start_game(
      impostersMerkleRoot=0x68650c6c5b,
      collectPointsMerkleRoot=0x68650c6c5c,
      attackDelayMerkleRoot=0x68650c6c5d,
      doNothingMerkleRoot=0x68650c6c5e
    ).invoke()

    # Collect points
    await contract.do_nothing(actionProof=0x68650c6c5c, actionHash=3, playerProof=1, playerHash=1).invoke()
    await contract.do_nothing(actionProof=0x68650c6c5c, actionHash=3, playerProof=0x68650c6c5b, playerHash=1).invoke()

    # Check number of total points
    total_points = await contract.view_total_points().call()
    assert total_points.result.total_points == 2