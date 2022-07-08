%lang starknet

from starkware.cairo.common.cairo_builtins import HashBuiltin, BitwiseBuiltin
from starkware.cairo.common.bitwise import bitwise_and
from starkware.starknet.common.syscalls import get_caller_address
from starkware.cairo.common.math import assert_lt, assert_le, assert_not_zero, unsigned_div_rem
from starkware.cairo.common.bool import TRUE, FALSE

###########
# CONSTANTS
###########

const MIN_PLAYERS = 4

# TODO make configurable
const MAX_PLAYERS = 4
const MAX_POINTS = 3

#######
# ENUMS
#######

struct GameStateEnum:
    member NOTSTARTED : felt
    member STARTED : felt
    member VOTING : felt
    member ENDED : felt
end

struct ActionTypeEnum:
    member INVALID : felt
    member DONOTHING : felt
    member MOVE : felt
    member COMPLETETASK : felt
end

struct PlayerStateEnum:
    member ALIVE : felt
    member DEAD : felt
end

#########
# STRUCTS
#########

# struct LocationTaskMerkleRoots:
#     member locationRoot : felt
#     member taskRoot : felt
# end

# struct LocationMerkleRoots:
#     member upperleft : LocationTaskMerkleRoots
#     member uppermid : LocationTaskMerkleRoots
#     member upperright : LocationTaskMerkleRoots
#     member midleft : LocationTaskMerkleRoots
#     member mid : LocationTaskMerkleRoots
#     member midright : LocationTaskMerkleRoots
#     member lowerleft : LocationTaskMerkleRoots
#     member lowermid : LocationTaskMerkleRoots
#     member lowerright : LocationTaskMerkleRoots
# end

struct MerkleRoots:
    # 
    member notImpostersMerkleRoot : felt
    member taskMerkleRoot : felt
    member killMerkleRoot : felt
    # member locationMerkleRoots : LocationMerkleRoots
end

struct RoundKey:
    member round : felt
    member playerAddr : felt
end

struct PlayerAction:
    # member currentLocationRoot : felt
    member actionType : felt
    member actionProof : felt
    member actionHash : felt
    member playerProof : felt
    member playerHash : felt
end

struct PlayerInfo:
    member address : felt
    member state : felt
end

##############
# STORAGE VARS
##############

@storage_var
func game_state() -> (state : felt):
end

@storage_var
func merkle_roots() -> (hash : MerkleRoots):
end

@storage_var
func random_seed() -> (res : felt):
end

@storage_var
func current_round() -> (round : felt):
end

@storage_var
func points_collected() -> (total_points : felt):
end

@storage_var
func players(index : felt) -> (info : PlayerInfo):
end

@storage_var
func player_count() -> (count : felt):
end

@storage_var
func actions(roundKey : RoundKey) -> (action : PlayerAction):
end

#############
# CONSTRUCTOR
#############

@constructor
func constructor{
    syscall_ptr : felt*,
    pedersen_ptr : HashBuiltin*,
    range_check_ptr,
}():
    game_state.write(GameStateEnum.NOTSTARTED)
    # TODO make into input
    random_seed.write(120345)
    return ()
end

#######
# VIEWS
#######

@view
func view_players{
    syscall_ptr : felt*,
    pedersen_ptr : HashBuiltin*,
    range_check_ptr,
}() -> (
    players : (PlayerInfo, PlayerInfo, PlayerInfo, PlayerInfo)
):
    let (player0) = players.read(0)
    let (player1) = players.read(1)
    let (player2) = players.read(2)
    let (player3) = players.read(3)
    return ((
        player0,
        player1,
        player2,
        player3,
    ))
end

@view
func view_player_count{
    syscall_ptr : felt*,
    pedersen_ptr : HashBuiltin*,
    range_check_ptr,
}() -> (
    player_count : felt
):
    let (count) = player_count.read()
    return (count)
end

@view
func view_total_points{
    syscall_ptr : felt*,
    pedersen_ptr : HashBuiltin*,
    range_check_ptr,
}() -> (
    total_points : felt
):
    let (total_points) = points_collected.read()
    return (total_points)
end

@view
func view_game_state{
    syscall_ptr : felt*,
    pedersen_ptr : HashBuiltin*,
    range_check_ptr,
}() -> (
    gameState : felt
):
    let (gameState) = game_state.read()
    return (gameState)
end

@view
func view_round_actions{
    syscall_ptr : felt*,
    pedersen_ptr : HashBuiltin*,
    range_check_ptr,
}(
    round : felt
) -> (
    actions : (PlayerAction, PlayerAction, PlayerAction, PlayerAction)
):
    let (players) = view_players()
    let (action0) = actions.read(RoundKey(round, players[0].address))
    let (action1) = actions.read(RoundKey(round, players[1].address))
    let (action2) = actions.read(RoundKey(round, players[2].address))
    let (action3) = actions.read(RoundKey(round, players[3].address))
    return ((action0, action1, action2, action3))
end

###########
# EXTERNALS
###########

# ------------------------------
# Actions while game not started
# ------------------------------

# join game by adding address to player list store
@external
func join_game{
    syscall_ptr : felt*,
    pedersen_ptr : HashBuiltin*,
    range_check_ptr,
}(
    saltedHashAddress : felt, 
    index : felt
):
    _validate_pre_game_actions()

    let (count) = player_count.read()
    with_attr error_message("Game is full"):
        assert_lt(count, MAX_PLAYERS)
    end

    let (player) = players.read(index)
    if player.address != 0:
        # call recursively to iterate through array to find empty slot
        join_game(saltedHashAddress, index + 1)
    else:
        players.write(index, PlayerInfo(address=saltedHashAddress, state=PlayerStateEnum.ALIVE))
        player_count.write(count + 1)
    end

    return ()
end

@external
func start_game{
    syscall_ptr : felt*,
    pedersen_ptr : HashBuiltin*,
    range_check_ptr,
}(
    notImpostersMerkleRoot : felt, 
    taskMerkleRoot : felt,
    killMerkleRoot : felt
):
    _validate_pre_game_actions()

    let (count) = player_count.read()
    with_attr error_message("Not enough players. Only {count} players have joined"):
        assert_le(MIN_PLAYERS, count)
    end

    merkle_roots.write(
        MerkleRoots(
            notImpostersMerkleRoot=notImpostersMerkleRoot,
            taskMerkleRoot=taskMerkleRoot,
            killMerkleRoot=killMerkleRoot
        )
    )

    game_state.write(GameStateEnum.STARTED)
    current_round.write(1)
    # _set_start_location_for_all(0, locationMerkleRoots.mid.locationRoot)
    return ()
end

# --------------------------
# Actions after game started
# --------------------------

@external
func register_action{
    syscall_ptr : felt*,
    pedersen_ptr : HashBuiltin*,
    range_check_ptr,
}(
    actionType : felt,
    actionProof : felt, 
    actionHash : felt,
    playerProof : felt,
    playerHash : felt
):
    alloc_locals
    _validate_game_started()
    _validate_player_joined(playerHash)
    _validate_player_alive(playerHash)

    let (isCompleteTask) = _is_complete_task_action(actionProof, actionHash)
    let (isKillAction) = _is_kill_action(actionProof, actionHash)
    with_attr error_message("Cannot include this action because inputs cannot be validated"):
        local isCompleteTask = isCompleteTask
        local isKillAction = isKillAction
        assert_not_zero(isCompleteTask + isKillAction)
    end

    # Add action to current round's actions
    let (currRound) = current_round.read()
    actions.write(
        RoundKey(
            round=currRound, 
            playerAddr=playerHash),
        PlayerAction(
            actionType=actionType,
            actionProof=actionProof,
            actionHash=actionHash,
            playerProof=playerProof,
            playerHash=playerHash
        )
    )
    return ()
end

@external
func end_round{
    syscall_ptr : felt*,
    pedersen_ptr : HashBuiltin*,
    range_check_ptr,
    bitwise_ptr : BitwiseBuiltin*,
}():
    alloc_locals
    _validate_game_started()

    let (currRound) = current_round.read()
    let (playerActions) = view_round_actions(currRound)

    # TODO need to handle order of actions other than index
    local actions : (PlayerAction, PlayerAction, PlayerAction, PlayerAction) = playerActions
    _do_action(actions[0])
    _do_action(actions[1])
    _do_action(actions[2])
    _do_action(actions[3])

    # check win conditions
    _check_win_conditions()

    current_round.write(currRound + 1)
    return ()
end

#############
# VALIDATIONS
#############

func _validate_pre_game_actions{
    syscall_ptr : felt*,
    pedersen_ptr : HashBuiltin*,
    range_check_ptr,
}():
    let (state) = game_state.read()
    with_attr error_message("Can only start game if it has not started"):
        assert state = GameStateEnum.NOTSTARTED
    end

    return ()
end

func _validate_game_started{
    syscall_ptr : felt*,
    pedersen_ptr : HashBuiltin*,
    range_check_ptr,
}():
    let (state) = game_state.read()
    with_attr error_message("Can only perform this action when game has started"):
        assert state = GameStateEnum.STARTED
    end
    return ()
end

func _validate_player_joined{
    syscall_ptr : felt*,
    pedersen_ptr : HashBuiltin*,
    range_check_ptr,
}(
    playerHash : felt
):
    # verify player joined the game
    # TODO switch to using caller address
    # let (caller) = get_caller_address()
    with_attr error_message("You are not part of this game"):
        let (isPlayer, index) = _is_player(playerHash)
        assert isPlayer = TRUE
    end

    return ()
end

func _validate_player_alive{
    syscall_ptr : felt*,
    pedersen_ptr : HashBuiltin*,
    range_check_ptr,
}(
    playerHash : felt
):
    # verify player is alive
    # TODO switch to using caller address
    # let (caller) = get_caller_address()
    with_attr error_message("You must be alive to perform this task"):
        let (isPlayer, index) = _is_player(playerHash)
        let (player) = players.read(index)
        assert player.state = PlayerStateEnum.ALIVE
    end

    return ()
end

func _is_player{
    syscall_ptr : felt*,
    pedersen_ptr : HashBuiltin*,
    range_check_ptr,
}(
    playerAddr : felt
) -> (
    isPlayer : felt,
    index : felt
):
    let (players) = view_players()
    if players[0].address == playerAddr:
        return (TRUE, 0)
    end
    if players[1].address == playerAddr:
        return (TRUE, 1)
    end
    if players[2].address == playerAddr:
        return (TRUE, 2)
    end
    if players[3].address == playerAddr:
        return (TRUE, 3)
    end
    return (FALSE, 0)
end

###########
# INTERNALS
###########

func _merkle_verify(
    root : felt, 
    proof : felt, 
    leaf : felt
) -> (
    valid : felt
):
    # TODO replace with merkle proof verifier
    if root == proof:
        return (TRUE)
    else:
        return (FALSE)
    end
end

func _is_imposter{
    syscall_ptr : felt*,
    pedersen_ptr : HashBuiltin*,
    range_check_ptr,
}(
    playerProof : felt, 
    playerLeaf : felt
) -> (
    isImposter : felt
):
    let (merkleRoots) = merkle_roots.read()
    let (verified) = _merkle_verify(merkleRoots.notImpostersMerkleRoot, playerProof, playerLeaf)
    if verified == TRUE:
        return (FALSE)
    else:
        return (TRUE)
    end
end

func _is_complete_task_action{
    syscall_ptr : felt*,
    pedersen_ptr : HashBuiltin*,
    range_check_ptr,
}(
    actionProof : felt, 
    actionLeaf : felt
) -> (
    isCompleteTaskAction : felt
):
    let (merkleRoots) = merkle_roots.read()
    let (verified) = _merkle_verify(merkleRoots.taskMerkleRoot, actionProof, actionLeaf)
    return (verified)
end

func _is_kill_action{
    syscall_ptr : felt*,
    pedersen_ptr : HashBuiltin*,
    range_check_ptr,
}(
    actionProof : felt, 
    actionLeaf : felt
) -> (
    isKillAction : felt
):
    let (merkleRoots) = merkle_roots.read()
    let (verified) = _merkle_verify(merkleRoots.killMerkleRoot, actionProof, actionLeaf)
    return (verified)
end

func _do_action{
    syscall_ptr : felt*,
    pedersen_ptr : HashBuiltin*,
    range_check_ptr,
    bitwise_ptr : BitwiseBuiltin*,
}(
    action: PlayerAction
):
    let (isImposter) = _is_imposter(action.playerProof, action.playerHash)
    
    # if action is verified against taskMerkleRoot, add points
    let (isCompleteTask) = _is_complete_task_action(action.actionProof, action.actionHash)
    if isCompleteTask == TRUE:
        # if player is an imposter, do nothing
        if isImposter == TRUE:
            return ()
        end
        _increment_points()
        return ()
    end

    let (isKillAction) = _is_kill_action(action.actionProof, action.actionHash)
    if isKillAction == TRUE:
        if isImposter == TRUE:
            _kill_random_player(action.playerHash)
            return ()
        end
        return ()
    end

    return ()
end

func _kill_random_player{
    syscall_ptr : felt*,
    pedersen_ptr : HashBuiltin*,
    range_check_ptr,
    bitwise_ptr : BitwiseBuiltin*,
}(player : felt):
    # kill player except yourself
    let (randomNum) = _randint(MAX_PLAYERS)
    let (selected) = players.read(randomNum - 1)
    if selected.address != player:
        if selected.state == PlayerStateEnum.ALIVE:
            players.write(randomNum - 1, PlayerInfo(address=selected.address, state=PlayerStateEnum.DEAD))
            return ()
        else:
            _kill_random_player(player)
        end
    else:
        _kill_random_player(player)
    end
    return ()
end

func _increment_points{
    syscall_ptr : felt*,
    pedersen_ptr : HashBuiltin*,
    range_check_ptr,
}():
    let (currTotalPoints) = points_collected.read()
    if currTotalPoints == MAX_POINTS:
        return ()
    else:
        points_collected.write(currTotalPoints + 1)
    end
    
    return ()
end

func _check_win_conditions{
    syscall_ptr : felt*,
    pedersen_ptr : HashBuiltin*,
    range_check_ptr,
}():
    let (currTotalPoints) = points_collected.read()
    if currTotalPoints == MAX_POINTS:
        game_state.write(GameStateEnum.ENDED)
        return ()
    end

    return ()
end

# Thanks to @Codiumdium on matchbox discord
func _randint{
    syscall_ptr : felt*,
    pedersen_ptr : HashBuiltin*,
    range_check_ptr,
    bitwise_ptr : BitwiseBuiltin*,
}(max : felt) -> (number : felt):
    alloc_locals
    let (currSeed) = random_seed.read()
    let (result) = _hash2(x=max * currSeed, y=max + currSeed)
    let (result) = bitwise_and(result, 1023)
    let (_, number) = unsigned_div_rem(result, max)
    random_seed.write(currSeed + 1)
    return (number)
end

func _hash2{pedersen_ptr : HashBuiltin*}(x, y) -> (z : felt):
    # Create a copy of the reference and advance hash_ptr.
    let hash = pedersen_ptr
    let pedersen_ptr = pedersen_ptr + HashBuiltin.SIZE
    # Invoke the hash function.
    hash.x = x
    hash.y = y
    # Return the result of the hash.
    # The updated pointer is returned automatically.
    return (z=hash.result)
end

# # sets start location to mid location
# func _set_start_location_for_all{
#     syscall_ptr : felt*,
#     pedersen_ptr : HashBuiltin*,
#     range_check_ptr,
# }(index : felt, locationRoot : felt):
#     # end if already at last player
#     if index == MAX_PLAYERS - 1:
#         return ()
#     end

#     let (player) = players.read(index)   
#     if player.address != 0:

#         actions.write(
#             RoundKey(
#                 round=1, 
#                 playerAddr=player),
#             PlayerAction(
#                 currentLocationRoot=locationRoot,
#                 actionType=ActionTypeEnum.DONOTHING,
#                 actionProof=0,
#                 actionHash=0,
#                 playerProof=0,
#                 playerHash=0
#             )
#         )
#         tempvar syscall_ptr = syscall_ptr
#         tempvar pedersen_ptr = pedersen_ptr
#         tempvar range_check_ptr = range_check_ptr
#     else:
#         tempvar syscall_ptr = syscall_ptr
#         tempvar pedersen_ptr = pedersen_ptr
#         tempvar range_check_ptr = range_check_ptr
#     end
#     _set_start_location_for_all(index + 1, locationRoot)

#     return ()
# end