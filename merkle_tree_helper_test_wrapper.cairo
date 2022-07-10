%lang starknet

from starkware.cairo.common.cairo_builtins import HashBuiltin
from merkle_tree_helper import MerkleTreeHelper

@external
func get_root{
    syscall_ptr : felt*,
    pedersen_ptr : HashBuiltin*,
    range_check_ptr,
}(
    input_array_len : felt,
    input_array : felt*,
) -> (
    output_array_len : felt,
    output_array : felt*
):  
    return MerkleTreeHelper.get_root(input_array_len, input_array)
end

@external
func create_next_nodes{
    syscall_ptr : felt*,
    pedersen_ptr : HashBuiltin*,
    range_check_ptr,
}(
    start : felt,
    input_array_len : felt,
    input_array : felt*,
    output_array_len : felt,
    output_array : felt*
) -> (
    new_output_array_len : felt,
    new_output_array : felt*
):  
    return MerkleTreeHelper.create_next_nodes(
        start,
        input_array_len, 
        input_array,
        output_array_len,
        output_array)
end