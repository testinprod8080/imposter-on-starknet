import os
import pytest
import pytest_asyncio

from starkware.starknet.testing.starknet import Starknet
from sympy import true

# The path to the contract source code.
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
CONTRACT_FILE = os.path.join(TEST_DIR, "./merkle_tree_helper_test_wrapper.cairo")

############
# TEST SETUP
############

@pytest_asyncio.fixture
async def init_contract():
  # Create a new Starknet class that simulates the StarkNet system.
  starknet = await Starknet.empty()

  # Deploy the contract.
  return await starknet.deploy(
      source=CONTRACT_FILE,
  )

############
# TEST CASES
############

@pytest.mark.asyncio
async def test_fail_missing_inputs(init_contract):
    contract = init_contract

    # Arrange
    input = [1]
    
    # Act
    with pytest.raises(Exception):
      await contract.create_next_nodes(
        start=0,
        input_array=input,
        output_array=[]
      ).invoke()

@pytest.mark.asyncio
async def test_fail_odd_number_of_inputs(init_contract):
    contract = init_contract

    # Arrange
    input = [1, 2, 3]
    
    # Act
    with pytest.raises(Exception):
      await contract.create_next_nodes(
        start=0,
        input_array=input,
        output_array=[]
      ).invoke()

@pytest.mark.asyncio
async def test_success(init_contract):
    contract = init_contract

    # Arrange
    input = [1, 2]
    expected = [1207699383798263883125605407307435965808923448511613904826718551574712750645]

    # Act
    result = await contract.create_next_nodes(
      start=0,
      input_array=input,
      output_array=[]
    ).invoke()

    # Assert
    node_array = result.result.new_output_array
    print("Nodes: " + str(node_array))
    assert len(node_array) == len(input)/2
    assert node_array[0] == expected[0]
