from web3 import Web3
from brownie import interface, config, network, accounts
from scripts.uniswap_functions import find_pools, fees_bips, swap_tokens
from scripts.helpful_scripts import check_price_usd_chainlink


def main():
    print(check_price_usd_chainlink("eth"))
    print(check_price_usd_chainlink("btc"))
    print(check_price_usd_chainlink("dai"))

    account = accounts.add(config["wallets"]["from_key"])

    print(Web3.fromWei(account.balance(), "ether"))

    # get pools by fee for dai and eth
    weth_token_address = config["networks"][network.show_active()]["weth_token"]
    dai_token_address = config["networks"][network.show_active()]["dai_token"]

    pools = find_pools(
        weth_token_address,
        dai_token_address,
    )

    pool_address = None
    fees_bips.sort()
    print(f"fees sorted: {fees_bips}")

    # default to 0.3%, 3000bips
    if 3000 in pools:
        pool_address = pools[3000]
    else:
        # use lowest fee pool(change to most liquidity?)
        for fee in fees_bips:
            if fee in pools:
                pool_address = pools[fee]
                break

    print(pool_address)

    dai_weth_pool = interface.IUniswapV3Pool(pool_address)
    # print(f"token0_price: {dai_weth_pool.slot0()}")
    slot0 = dai_weth_pool.slot0()

    # check which token is token1
    token1 = dai_weth_pool.token1()
    print(dai_weth_pool.token0())
    print(dai_weth_pool.token1())

    sqrtPriceX96 = slot0[0]

    # from Uniswap docs: sqrtPriceX96 = sqrt(price) * 2 ** 96
    price = sqrtPriceX96**2
    price = price >> 96
    # switch to float in case the ratio is < 1
    price /= 2**96

    # check if dai is numerator, if so invert price to be $DAI per ETH
    # price is supposed to be token1/token0 but isn't for mainnet DAI/ETH pool
    # if str(token1) == str(config["networks"][network.show_active()]["dai_token"]):
    # fixme: This can't be right.. dangerous for general purpose
    if price < 1:
        price = 1 / price

    print(f"Price: {price}")

    # when not being traded.. put in aave

    # for Aave... seems like I need to be on Eth Kovan...

    # test out price info on uniswap - DONE

    # test out a swap on uniswap DAI -> WETH (Kovan)
    # - tx 1: Authorize
    # - tx 2: Swap

    swap_tokens(
        pool_contract=dai_weth_pool,
        from_token_address=dai_token_address,
        from_token_name="dai",
        from_amount=5,
        to_token_address=weth_token_address,
        to_token_name="weth",
        account=account,
    )

    
    # check liquidity for uniswap pools and make sense of value

    # set some conditions for a trade

    # setup interface to aave
    # setup interface to uniswap
