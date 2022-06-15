from brownie import config, accounts, network, interface
from scripts.uniswap_functions import find_pools, swap_tokens
from web3 import Web3


def test_swap_tokens():
    account = accounts.add(config["wallets"]["from_key"])

    # get pools by fee for dai and eth
    weth_token_address = config["networks"][network.show_active()]["weth_token"]
    dai_token_address = config["networks"][network.show_active()]["dai_token"]

    pools = find_pools(
        weth_token_address,
        dai_token_address,
    )

    # default to 0.3%, 3000bips
    pool_address = pools[3000]
    dai_weth_pool = interface.IUniswapV3Pool(pool_address)

    swap_tokens(
        pool_contract=dai_weth_pool,
        from_token_address=dai_token_address,
        from_token_name="dai",
        from_amount=500,
        to_token_address=weth_token_address,
        to_token_name="weth",
        account=account,
    )
