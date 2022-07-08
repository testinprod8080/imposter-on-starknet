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

COMPLETE_TASK_ACTION_TYPE = 3

###########
# TEST DATA
###########

PLAYER1 = 0x68650c6c5c
PLAYER2 = 0x68650c6c5d
PLAYER3 = 0x68650c6c5e
PLAYER4 = 0x68650c6c5f

NONIMPOSTERMERKLEROOT = 0x68650c6c5b
COMPLETETASKROOT = 0x68650c6c5c

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
      notImpostersMerkleRoot=NONIMPOSTERMERKLEROOT,
      taskMerkleRoot=COMPLETETASKROOT
    ).invoke()
    return join_all_players

############
# TEST CASES
############

# @pytest.mark.asyncio
# async def test_fails_not_enough_players(init_contract):
#     contract = init_contract

#     # Join the game
#     await contract.join_game(saltedHashAddress=PLAYER1, index=0).invoke()
#     await contract.join_game(saltedHashAddress=PLAYER2, index=1).invoke()
#     await contract.join_game(saltedHashAddress=PLAYER3, index=0).invoke()

#     # Start the game
#     with pytest.raises(Exception):
#       await contract.start_game(
#         notImpostersMerkleRoot=PLAYER1,
#         locationMerkleRoots={}
#       ).invoke()

# @pytest.mark.asyncio
# async def test_fails_call_action_while_not_started(init_contract):
#     contract = init_contract

#     # Join the game
#     await contract.join_game(saltedHashAddress=PLAYER1, index=0).invoke()

#     # Start the game
#     with pytest.raises(Exception):
#       await contract.register_complete_task(
#           actionProof=COMPLETETASKROOT, 
#           actionHash=3, 
#           playerProof=1, 
#           playerHash=1
#         ).invoke()

# @pytest.mark.asyncio
# async def test_fails_too_many_players(join_all_players):
#     contract = join_all_players

#     # Join the game
#     with pytest.raises(Exception): 
#       await contract.join_game(saltedHashAddress=0x123, index=4).invoke()

# @pytest.mark.asyncio
# async def test_fails_not_player(started_game):
#     contract = started_game

#     # Non player calls action
#     with pytest.raises(Exception):
#       await contract.register_complete_task(
#           actionProof=COMPLETETASKROOT, 
#           actionHash=3, 
#           playerProof=1, 
#           playerHash=1
#         ).invoke()

@pytest.mark.asyncio
async def test_success_nonimposter_adds_points(started_game):
    contract = started_game

    # ROUND 1

    # Complete task to add 1 pt
    await contract.register_complete_task(
        actionProof=COMPLETETASKROOT, 
        actionHash=3, 
        playerProof=NONIMPOSTERMERKLEROOT, 
        playerHash=PLAYER3
      ).invoke()

    # Imposter pretends to complete task, should not add points
    await contract.register_complete_task(
        actionProof=COMPLETETASKROOT, 
        actionHash=3, 
        playerProof=1, 
        playerHash=PLAYER1
      ).invoke()

    # Check actions
    actions = await contract.view_round_actions(1).call()
    player1Action = actions.result.actions[0]
    assert player1Action.actionType == COMPLETE_TASK_ACTION_TYPE
    player3Action = actions.result.actions[2]
    assert player3Action.actionType == COMPLETE_TASK_ACTION_TYPE

    # End round
    total_points = await contract.view_total_points().call()
    assert total_points.result.total_points == 0
    await contract.end_round().invoke()

    # Check number of total points
    total_points = await contract.view_total_points().call()
    assert total_points.result.total_points == 1 

    # ROUND 2

    # Complete task to add 1 pt
    await contract.register_complete_task(
        actionProof=COMPLETETASKROOT, 
        actionHash=3, 
        playerProof=NONIMPOSTERMERKLEROOT, 
        playerHash=PLAYER3
      ).invoke()

    # Complete task to add 1 pt
    await contract.register_complete_task(
        actionProof=COMPLETETASKROOT, 
        actionHash=3, 
        playerProof=NONIMPOSTERMERKLEROOT, 
        playerHash=PLAYER2
      ).invoke()

    # Complete task to add 1 pt
    await contract.register_complete_task(
        actionProof=COMPLETETASKROOT, 
        actionHash=3, 
        playerProof=NONIMPOSTERMERKLEROOT, 
        playerHash=PLAYER4
      ).invoke()

    # Imposter pretends to complete task, should not add points
    await contract.register_complete_task(
        actionProof=COMPLETETASKROOT, 
        actionHash=3, 
        playerProof=1, 
        playerHash=PLAYER1
      ).invoke()

    # Check number of total points
    total_points = await contract.view_total_points().call()
    assert total_points.result.total_points == 1
    await contract.end_round().invoke()
    total_points = await contract.view_total_points().call()
    assert total_points.result.total_points == 4