%lang starknet

from starkware.cairo.common.cairo_builtins import HashBuiltin
from starkware.cairo.common.alloc import alloc
from starkware.cairo.common.hash import hash2
from starkware.cairo.common.math import assert_le

namespace MerkleTreeHelper:
    # hashes all nodes until it returns a root
    # [1, 2, 3, 4] -> [a, b] -> [r]
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
        let (output_array : felt*) = alloc()

        let (output_array_len, output_array) = create_next_nodes(
            start=0,
            input_array_len=input_array_len, 
            input_array=input_array, 
            output_array_len=0, 
            output_array=output_array)

        # return as root when exactly one in array
        if output_array_len == 1:
            return (1, output_array)
        else:
            return get_root(output_array_len, output_array)
        end
    end

    # hashes all nodes to next level in tree
    # [1, 2, 3, 4] -> [a, b]
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
        alloc_locals
        
        with_attr error_message("Inputs must have at least a length of two"):
            assert_le(2, input_array_len)
        end

        local index : felt
        assert index = input_array_len - start

        let (hash) = hash2{hash_ptr=pedersen_ptr}(
            x=input_array[index - 1], 
            y=input_array[index - 2])
        assert output_array[output_array_len] = hash

        if index != 2:
            return create_next_nodes(
                start + 2,
                input_array_len, 
                input_array, 
                output_array_len + 1, 
                output_array)
        else:
            return (output_array_len + 1, output_array)
        end
    end
end