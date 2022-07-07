%lang starknet

from starkware.cairo.common.cairo_builtins import HashBuiltin
from starkware.cairo.common.math import assert_lt, assert_le
from starkware.cairo.common.bool import TRUE, FALSE

###########
# CONSTANTS
###########

const MIN_PLAYERS = 4
const MAX_PLAYERS = 8

#########
# STRUCTS
#########

struct MerkleRoots:
    member impostersMerkleRoot : felt
    member collectPointsMerkleRoot : felt
    member attackDelayMerkleRoot : felt
    member doNothingMerkleRoot : felt
end

#######
# ENUMS
#######

struct GameStateEnum:
    member NOTSTARTED : felt
    member STARTED : felt
    member ENDED : felt
end

##############
# STORAGE VARS
##############

@storage_var
func game_state() -> (state : felt):
end

@storage_var
func players_hash(index : felt) -> (hash : felt):
end

@storage_var
func player_count() -> (count : felt):
end

@storage_var
func merkle_roots() -> (hash : MerkleRoots):
end

@storage_var
func points_collected() -> (total_points : felt):
end

@storage_var
func actions(round : felt, player : felt) -> (action_desc : felt):
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
    return ()
end

#######
# VIEWS
#######

@view
func view_players_hash{
    syscall_ptr : felt*,
    pedersen_ptr : HashBuiltin*,
    range_check_ptr,
}() -> (players : (felt, felt, felt ,felt, felt, felt, felt, felt)):
    let (player0) = players_hash.read(0)
    let (player1) = players_hash.read(1)
    let (player2) = players_hash.read(2)
    let (player3) = players_hash.read(3)
    let (player4) = players_hash.read(4)
    let (player5) = players_hash.read(5)
    let (player6) = players_hash.read(6)
    let (player7) = players_hash.read(7)
    return ((
        player0,
        player1,
        player2,
        player3,
        player4,
        player5,
        player6,
        player7,
    ))
end

@view
func view_player_count{
    syscall_ptr : felt*,
    pedersen_ptr : HashBuiltin*,
    range_check_ptr,
}() -> (player_count : felt):
    let (count) = player_count.read()
    return (count)
end

@view
func view_total_points{
    syscall_ptr : felt*,
    pedersen_ptr : HashBuiltin*,
    range_check_ptr,
}() -> (total_points : felt):
    let (total_points) = points_collected.read()
    return (total_points)
end

###########
# EXTERNALS
###########

@external
func join_game{
    syscall_ptr : felt*,
    pedersen_ptr : HashBuiltin*,
    range_check_ptr,
}(saltedHashAddress : felt, index : felt):
    let (count) = player_count.read()
    with_attr error_message("Game is full"):
        assert_lt(count, MAX_PLAYERS)
    end

    let (player) = players_hash.read(index)
    if player != 0:
        # call recursively to iterate through array to find empty slot
        join_game(saltedHashAddress, index + 1)
    else:
        players_hash.write(index, saltedHashAddress)
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
    impostersMerkleRoot : felt, 
    collectPointsMerkleRoot : felt, 
    attackDelayMerkleRoot : felt, 
    doNothingMerkleRoot : felt
):
    let (count) = player_count.read()
    with_attr error_message("Not enough players"):
        assert_le(MIN_PLAYERS, count)
    end

    merkle_roots.write(
        MerkleRoots(
            impostersMerkleRoot=impostersMerkleRoot,
            collectPointsMerkleRoot=collectPointsMerkleRoot,
            attackDelayMerkleRoot=attackDelayMerkleRoot,
            doNothingMerkleRoot=doNothingMerkleRoot
        )
    )

    game_state.write(GameStateEnum.STARTED)
    return ()
end


# @external
# func move()

# effects: 
#   - doing a task increases the total points, unless imposter
#   - takes up two turns
@external
func complete_task{
    syscall_ptr : felt*,
    pedersen_ptr : HashBuiltin*,
    range_check_ptr,
}(
    actionProof : felt, 
    actionHash : felt,
    playerProof : felt,
    playerHash : felt
):
    # if action is verified against collectPointsMerkleRoot, do collect points
    let (isCompleteTask) = _is_complete_task_action(actionProof, actionHash)
    if isCompleteTask == TRUE:
        _complete_task()
        return ()
    end

    # if action is verified against attackDelay1MerkleRoot, perform delayed attack
    

    return ()
end

# @external
# func do_action()

###########
# INTERNALS
###########

func _merkle_verify{
    syscall_ptr : felt*,
    pedersen_ptr : HashBuiltin*,
    range_check_ptr,
}(root : felt, proof : felt, leaf : felt) -> (valid : felt):
    # TODO replace with merkle proof verifier
    if root == proof:
        return (TRUE)
    else:
        return (FALSE)
    end
end

func _is_complete_task_action{
    syscall_ptr : felt*,
    pedersen_ptr : HashBuiltin*,
    range_check_ptr,
}(actionProof : felt, actionLeaf : felt) -> (canCollect : felt):
    let (merkleRoots) = merkle_roots.read()
    let (verified) = _merkle_verify(merkleRoots.collectPointsMerkleRoot, actionProof, actionLeaf)
    return (verified)
end

func _complete_task{
    syscall_ptr : felt*,
    pedersen_ptr : HashBuiltin*,
    range_check_ptr,
}():
    let (currTotalPoints) = points_collected.read()
    points_collected.write(currTotalPoints + 1)
    return ()
end