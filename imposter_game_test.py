import os
import pytest
import pytest_asyncio

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

MAX_POINTS = 5

INVALID_ACTION_TYPE = 0
DO_NOTHING_ACTION_TYPE = 1
MOVE_ACTION_TYPE = 2
COMPLETE_TASK_ACTION_TYPE = 3

GAMESTATE_NOTSTARTED = 0
GAMESTATE_STARTED = 1
GAMESTATE_VOTING = 2
GAMESTATE_ENDED = 3

ALIVE = 0
DEAD = 1

###########
# TEST DATA
###########

PLAYER1 = 0x68650c6c5c
PLAYER2 = 0x68650c6c5d
PLAYER3 = 0x68650c6c5e
PLAYER4 = 0x68650c6c5f

REALONESMERKLEROOT = 0x68650c6c5b
COMPLETETASKMERKLEROOT = 0x7451
KILLMERKLEROOT = 0xd34d
DONOTHINGMERKLEROOT = 0x000

############
# TEST SETUP
############

@pytest_asyncio.fixture
async def init_starknet():
  # Create a new Starknet class that simulates the StarkNet system.
  return await Starknet.empty()

@pytest_asyncio.fixture
async def init_contract(init_starknet):
    # Deploy the contract.
    return await init_starknet.deploy(
        source=CONTRACT_FILE,
    )

@pytest_asyncio.fixture
async def join_all_players(init_contract):
    await init_contract.join_game(saltedHashAddress=PLAYER1, index=0).invoke()
    await init_contract.join_game(saltedHashAddress=PLAYER2, index=1).invoke()
    await init_contract.join_game(saltedHashAddress=PLAYER3, index=0).invoke()
    await init_contract.join_game(saltedHashAddress=PLAYER4, index=3).invoke()
    return init_contract

@pytest_asyncio.fixture
async def started_game(join_all_players):
    await join_all_players.start_game(
      realOnesMerkleRoot=REALONESMERKLEROOT,
      taskMerkleRoot=COMPLETETASKMERKLEROOT,
      killMerkleRoot=KILLMERKLEROOT
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
        realOnesMerkleRoot=PLAYER1,
        locationMerkleRoots={}
      ).invoke()

@pytest.mark.asyncio
async def test_fails_call_action_while_not_started(init_contract):
    contract = init_contract

    # Join the game
    await contract.join_game(saltedHashAddress=PLAYER1, index=0).invoke()

    # Start the game
    with pytest.raises(Exception):
      await contract.register_action(
          actionType=COMPLETE_TASK_ACTION_TYPE,
          actionProof=COMPLETETASKMERKLEROOT, 
          actionHash=3, 
          playerProof=1, 
          playerHash=1
        ).invoke()

@pytest.mark.asyncio
async def test_fails_too_many_players(join_all_players):
    contract = join_all_players

    # Join the game
    with pytest.raises(Exception): 
      await contract.join_game(saltedHashAddress=0x123, index=4).invoke()

@pytest.mark.asyncio
async def test_fails_not_player(started_game):
    contract = started_game

    # Non player calls action
    with pytest.raises(Exception):
      await contract.register_action(
          actionType=COMPLETE_TASK_ACTION_TYPE,
          actionProof=COMPLETETASKMERKLEROOT, 
          actionHash=3, 
          playerProof=1, 
          playerHash=1
        ).invoke()

@pytest.mark.asyncio
async def test_fails_invalid_action_type(started_game):
    contract = started_game

    # Call with invalid action type
    with pytest.raises(Exception):
      await contract.register_action(
          actionType=0,
          actionProof=COMPLETETASKMERKLEROOT, 
          actionHash=3, 
          playerProof=REALONESMERKLEROOT, 
          playerHash=PLAYER3
        ).invoke()

@pytest.mark.asyncio
async def test_fails_end_round(started_game):
    contract = started_game

    # Register action
    await contract.register_action(
        actionType=COMPLETE_TASK_ACTION_TYPE,
        actionProof=COMPLETETASKMERKLEROOT, 
        actionHash=3, 
        playerProof=REALONESMERKLEROOT, 
        playerHash=PLAYER3
      ).invoke()

    # Ending round fails when not all players have submitted an action
    with pytest.raises(Exception):
      await contract.end_round().invoke()

# @pytest.mark.asyncio
# async def test_success_call_vote(started_game):
#     contract = started_game

#     await contract.call_vote(PLAYER1).invoke()

#     # State changed to voting successfully
#     state = await contract.view_game_state().call()
#     assert state.result.gameState == GAMESTATE_VOTING

@pytest.mark.asyncio
async def test_success_realones_win(started_game):
    contract = started_game

    # -------
    # ROUND 1
    # -------

    # Complete task to add 1 pt
    await contract.register_action(
        actionType=COMPLETE_TASK_ACTION_TYPE,
        actionProof=COMPLETETASKMERKLEROOT, 
        actionHash=3, 
        playerProof=REALONESMERKLEROOT, 
        playerHash=PLAYER3
      ).invoke()

    # Complete task to add 1 pt
    await contract.register_action(
        actionType=COMPLETE_TASK_ACTION_TYPE,
        actionProof=COMPLETETASKMERKLEROOT, 
        actionHash=3, 
        playerProof=REALONESMERKLEROOT, 
        playerHash=PLAYER2
      ).invoke()

    # Complete task to add 1 pt
    await contract.register_action(
        actionType=COMPLETE_TASK_ACTION_TYPE,
        actionProof=COMPLETETASKMERKLEROOT, 
        actionHash=3, 
        playerProof=REALONESMERKLEROOT, 
        playerHash=PLAYER4
      ).invoke()

    # Imposter pretends to complete task, should not add points
    await contract.register_action(
        actionType=COMPLETE_TASK_ACTION_TYPE,
        actionProof=COMPLETETASKMERKLEROOT, 
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
    assert total_points.result.total_points == 3

    # -------
    # ROUND 2
    # -------

    # Complete task to add 1 pt
    await contract.register_action(
        actionType=COMPLETE_TASK_ACTION_TYPE,
        actionProof=COMPLETETASKMERKLEROOT, 
        actionHash=3, 
        playerProof=REALONESMERKLEROOT, 
        playerHash=PLAYER3
      ).invoke()

    # Complete task to add 1 pt
    await contract.register_action(
        actionType=COMPLETE_TASK_ACTION_TYPE,
        actionProof=COMPLETETASKMERKLEROOT, 
        actionHash=3, 
        playerProof=REALONESMERKLEROOT, 
        playerHash=PLAYER2
      ).invoke()

    # Complete task to add 1 pt
    await contract.register_action(
        actionType=COMPLETE_TASK_ACTION_TYPE,
        actionProof=DONOTHINGMERKLEROOT, 
        actionHash=3, 
        playerProof=REALONESMERKLEROOT, 
        playerHash=PLAYER4
      ).invoke()

    # Imposter pretends to complete task, should not add points
    await contract.register_action(
        actionType=COMPLETE_TASK_ACTION_TYPE,
        actionProof=COMPLETETASKMERKLEROOT, 
        actionHash=3, 
        playerProof=1, 
        playerHash=PLAYER1
      ).invoke()

    # Check points did not change before round ended
    total_points = await contract.view_total_points().call()
    assert total_points.result.total_points == 3

    # Check number of total points
    await contract.end_round().invoke()
    total_points = await contract.view_total_points().call()
    assert total_points.result.total_points == MAX_POINTS

    # Real Ones win
    state = await contract.view_game_state().call()
    assert state.result.gameState == GAMESTATE_ENDED

@pytest.mark.asyncio
async def test_success_imposters_win(started_game):
    contract = started_game

    # -------
    # ROUND 1
    # -------

    await contract.register_action(
        actionType=COMPLETE_TASK_ACTION_TYPE,
        actionProof=COMPLETETASKMERKLEROOT, 
        actionHash=3, 
        playerProof=REALONESMERKLEROOT, 
        playerHash=PLAYER3
      ).invoke()
    await contract.register_action(
        actionType=COMPLETE_TASK_ACTION_TYPE,
        actionProof=COMPLETETASKMERKLEROOT, 
        actionHash=3, 
        playerProof=REALONESMERKLEROOT, 
        playerHash=PLAYER2
      ).invoke()
    await contract.register_action(
        actionType=COMPLETE_TASK_ACTION_TYPE,
        actionProof=DONOTHINGMERKLEROOT, 
        actionHash=3, 
        playerProof=REALONESMERKLEROOT, 
        playerHash=PLAYER4
      ).invoke()
    # Imposter kills
    await contract.register_action(
        actionType=DO_NOTHING_ACTION_TYPE,
        actionProof=KILLMERKLEROOT, 
        actionHash=3, 
        playerProof=1, 
        playerHash=PLAYER1
      ).invoke()
    await contract.end_round().invoke()

    # -------
    # ROUND 2
    # -------

    await contract.register_action(
        actionType=COMPLETE_TASK_ACTION_TYPE,
        actionProof=DONOTHINGMERKLEROOT, 
        actionHash=3, 
        playerProof=REALONESMERKLEROOT, 
        playerHash=PLAYER3
      ).invoke()
    await contract.register_action(
        actionType=COMPLETE_TASK_ACTION_TYPE,
        actionProof=DONOTHINGMERKLEROOT, 
        actionHash=3, 
        playerProof=REALONESMERKLEROOT, 
        playerHash=PLAYER2
      ).invoke()
    await contract.register_action(
        actionType=COMPLETE_TASK_ACTION_TYPE,
        actionProof=DONOTHINGMERKLEROOT, 
        actionHash=3, 
        playerProof=REALONESMERKLEROOT, 
        playerHash=PLAYER4
      ).invoke()
    # Imposter kills
    await contract.register_action(
        actionType=DO_NOTHING_ACTION_TYPE,
        actionProof=KILLMERKLEROOT, 
        actionHash=3, 
        playerProof=1, 
        playerHash=PLAYER1
      ).invoke()
    await contract.end_round().invoke()

    # -------
    # ROUND 3
    # -------

    await contract.register_action(
        actionType=COMPLETE_TASK_ACTION_TYPE,
        actionProof=DONOTHINGMERKLEROOT, 
        actionHash=3, 
        playerProof=REALONESMERKLEROOT, 
        playerHash=PLAYER3
      ).invoke()
    await contract.register_action(
        actionType=COMPLETE_TASK_ACTION_TYPE,
        actionProof=DONOTHINGMERKLEROOT, 
        actionHash=3, 
        playerProof=REALONESMERKLEROOT, 
        playerHash=PLAYER2
      ).invoke()
    await contract.register_action(
        actionType=COMPLETE_TASK_ACTION_TYPE,
        actionProof=DONOTHINGMERKLEROOT, 
        actionHash=3, 
        playerProof=REALONESMERKLEROOT, 
        playerHash=PLAYER4
      ).invoke()
    # Imposter kills
    await contract.register_action(
        actionType=DO_NOTHING_ACTION_TYPE,
        actionProof=KILLMERKLEROOT, 
        actionHash=3, 
        playerProof=1, 
        playerHash=PLAYER1
      ).invoke()
    await contract.end_round().invoke()

    # Check that game ended
    gameState = await contract.view_game_state().call()
    assert gameState.result.gameState == GAMESTATE_ENDED
    players = await contract.view_players().call()
    assert (
        players.result.players[0].state 
        + players.result.players[1].state 
        + players.result.players[2].state 
        + players.result.players[3].state
      ) >= 3