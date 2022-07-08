import os
import pytest

from starkware.starknet.testing.starknet import Starknet
from sympy import true

# The path to the contract source code.
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
CONTRACT_FILE = os.path.join(TEST_DIR, "./imposter_game.cairo")

###########
# Constants
###########

FALSE = 0
TRUE = 1

###########
# TEST DATA
###########

PLAYER1=0x68650c6c5c
PLAYER2=0x68650c6c5d
PLAYER3=0x68650c6c5e
PLAYER4=0x68650c6c5f

############
# TEST SETUP
############

@pytest.fixture
async def init_starknet():
  # Create a new Starknet class that simulates the StarkNet system.
  return await Starknet.empty()

@pytest.fixture
async def init_contract(init_starknet):
    # Deploy the contract.
    return await init_starknet.deploy(
        source=CONTRACT_FILE,
    )

@pytest.fixture
async def join_all_players(init_contract):
    await init_contract.join_game(saltedHashAddress=PLAYER1, index=0).invoke()
    await init_contract.join_game(saltedHashAddress=PLAYER2, index=1).invoke()
    await init_contract.join_game(saltedHashAddress=PLAYER3, index=0).invoke()
    await init_contract.join_game(saltedHashAddress=PLAYER4, index=3).invoke()
    return init_contract

@pytest.fixture
async def started_game(join_all_players):
    await join_all_players.start_game(
      notImpostersMerkleRoot=0x68650c6c5b,
      taskMerkleRoot=0x68650c6c5c
    ).invoke()
    return join_all_players

############
# TEST CASES
############

@pytest.mark.asyncio
async def test_fails_not_enough_players(init_contract):
    contract = init_contract

    # Join the game
    await contract.join_game(saltedHashAddress=PLAYER1, index=0).invoke()
    await contract.join_game(saltedHashAddress=PLAYER2, index=1).invoke()
    await contract.join_game(saltedHashAddress=PLAYER3, index=0).invoke()

    # Start the game
    with pytest.raises(Exception):
      await contract.start_game(
        notImpostersMerkleRoot=PLAYER1,
        locationMerkleRoots={}
      ).invoke()

@pytest.mark.asyncio
async def test_fails_call_action_while_not_started(init_contract):
    contract = init_contract

    # Join the game
    await contract.join_game(saltedHashAddress=PLAYER1, index=0).invoke()

    # Start the game
    with pytest.raises(Exception):
      await contract.register_complete_task(actionProof=0x68650c6c5c, actionHash=3, playerProof=1, playerHash=1).invoke()

@pytest.mark.asyncio
async def test_fails_too_many_players(join_all_players):
    contract = join_all_players

    # Join the game
    with pytest.raises(Exception): 
      await contract.join_game(saltedHashAddress=0x68650c6c6a, index=4).invoke()

@pytest.mark.asyncio
async def test_fails_not_player(started_game):
    contract = started_game

    # Non player calls action
    with pytest.raises(Exception):
      await contract.register_complete_task(actionProof=0x68650c6c5c, actionHash=3, playerProof=1, playerHash=1).invoke()

@pytest.mark.asyncio
async def test_success_nonimposter_adds_points(started_game):
    contract = started_game

    # Complete task to bump up points
    await contract.register_complete_task(actionProof=0x68650c6c5c, actionHash=3, playerProof=0x68650c6c5b, playerHash=PLAYER3).invoke()

    # Check actions
    actions = await contract.view_curr_round_actions(1).call()
    player3Action = actions.result.actions[2]
    assert player3Action.actionType == 2

# @pytest.mark.asyncio
# async def test_success_nonimposter_adds_points(started_game):
#     contract = started_game

#     # Imposter does task
#     await contract.register_complete_task(actionProof=0x68650c6c5c, actionHash=3, playerProof=1, playerHash=PLAYER1).invoke()

#     # Complete task to bump up points
#     await contract.register_complete_task(actionProof=0x68650c6c5c, actionHash=3, playerProof=0x68650c6c5b, playerHash=PLAYER3).invoke()

#     # Check number of total points
#     total_points = await contract.view_total_points().call()
#     assert total_points.result.total_points == 1 