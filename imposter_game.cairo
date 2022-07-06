%lang starknet

from starkware.cairo.common.cairo_builtins import HashBuiltin
from starkware.cairo.common.math import assert_lt
from starkware.cairo.common.bool import TRUE

#########
# STRUCTS
#########

struct MerkleRoots:
    member impostersMerkleRoot : felt
    member collectPointsMerkleRoot : felt
    member attackDelayMerkleRoot : felt
    member doNothingMerkleRoot : felt
end

##############
# STORAGE VARS
##############

# Max of 10 players
@storage_var
func players_hash(index : felt) -> (hash : felt):
end

@storage_var
func merkle_roots() -> (hash : MerkleRoots):
end

@storage_var
func points_collected() -> (total_points : felt):
end

#######
# VIEWS
#######

@view
func view_players_hash{
    syscall_ptr : felt*,
    pedersen_ptr : HashBuiltin*,
    range_check_ptr,
}() -> (players : (felt, felt, felt ,felt, felt, felt, felt, felt ,felt, felt)):
    let (player0) = players_hash.read(0)
    let (player1) = players_hash.read(1)
    let (player2) = players_hash.read(2)
    let (player3) = players_hash.read(3)
    let (player4) = players_hash.read(4)
    let (player5) = players_hash.read(5)
    let (player6) = players_hash.read(6)
    let (player7) = players_hash.read(7)
    let (player8) = players_hash.read(8)
    let (player9) = players_hash.read(9)
    return ((
        player0,
        player1,
        player2,
        player3,
        player4,
        player5,
        player6,
        player7,
        player8,
        player9,
    ))
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
    # with_attr error_message("Game is full"):
    #     assert_lt(9, index)
    # end
    let (player) = players_hash.read(index)
    if player != 0:
        join_game(saltedHashAddress, index + 1)
    else:
        players_hash.write(index, saltedHashAddress)
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
    # TODO check that appropriate number of players have joined before starting game
    merkle_roots.write(
        MerkleRoots(
            impostersMerkleRoot=impostersMerkleRoot,
            collectPointsMerkleRoot=collectPointsMerkleRoot,
            attackDelayMerkleRoot=attackDelayMerkleRoot,
            doNothingMerkleRoot=doNothingMerkleRoot
        )
    )
    return ()
end

@external
func do_action{
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
    # if action is verified against attackDelay1MerkleRoot, perform delayed attack
    return ()
end

###########
# INTERNALS
###########

func _collect_points{
    syscall_ptr : felt*,
    pedersen_ptr : HashBuiltin*,
    range_check_ptr,
}():
    let (currTotalPoints) = points_collected.read()
    points_collected.write(currTotalPoints + 1)
    return ()
end