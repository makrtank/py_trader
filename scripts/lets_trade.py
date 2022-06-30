from web3 import Web3
from brownie import interface, config, network, accounts
import scripts.uniswap_functions as uniswap
from scripts.helpful_scripts import check_price_usd_chainlink


def main():

    # list out prices from Chainlink and Uniswap pools by fee
    token_name = "weth"

    chainlink_price = check_price_usd_chainlink(token_name)
    uniswap_pools = uniswap.get_pools_prices_usd(token_name)
    print("Chainlink Oracle")
    print(f"Price:  {chainlink_price}")

    print("Uniswap Pools")
    for pool in uniswap_pools:
        print(f"Price:  {pool['price']}      Pool Fee: {pool['fee']}")

    # when not being traded.. put in aave

    # for Aave... seems like I need to be on Eth Kovan...

    # test out a swap on uniswap DAI -> WETH (Kovan)
    # - tx 1: Authorize
    # - tx 2: Swap

    # check liquidity for uniswap pools and make sense of value

    # set some conditions for a trade

    # setup interface to aave
    # setup interface to uniswap
