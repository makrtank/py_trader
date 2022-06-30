from brownie import network, config, interface
from web3 import Web3, constants
from scripts.helpful_scripts import check_price_usd_chainlink, approve_erc20
import math

fees_bips = [
    10000,
    3000,
    500,
    100,
]  # 1%, 0.3%, 0.05%, 0.01%, may change in the future from goverance votes
# Returns list of Pool dicts
# Pool
#   fee
#   token0 address
#   token1 address
#   price


def get_pools_prices_usd(token_name, usd_ref="dai"):
    # check vs usdc or dai
    # todo: add USDC token addresses to brownie-config
    assert usd_ref in ["dai", "usdc"], "Only DAI and USDC supported for USD reference"

    # check if token address known
    token_address = config["networks"][network.show_active()][f"{token_name}_token"]
    usd_ref_token_address = config["networks"][network.show_active()][
        f"{usd_ref}_token"
    ]

    # find pools
    pool_addresses = find_pool_addresses(token_address, usd_ref_token_address)
    pools = get_pools(pool_addresses)
    pool_list = []
    # get ratio, token0, token1 from each pool
    for fee in pools:
        slot0 = pools[fee].slot0()
        # check which token is token1
        pool_info = {}
        pool_info["fee"] = fee
        pool_info["token0"] = pools[fee].token0()
        pool_info["token1"] = pools[fee].token1()

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
        pool_info["price"] = price
        print(f"pool_info: {pool_info}")
        pool_list.append(pool_info)
    return pool_list


def get_pools(_pool_addresses):
    pools = {}
    for fee in _pool_addresses:
        pools[fee] = interface.IUniswapV3Pool(_pool_addresses[fee])

    return pools


def find_pool_addresses(token_address0, token_address1):
    uniswap_factory = interface.IUniswapV3Factory(
        config["networks"][network.show_active()]["uniswap_v3_factory_address"]
    )

    # from here: https://www.reddit.com/r/UniSwap/comments/atddo2/effective_way_to_get_all_uniswap_exchange/
    """
    events = uniswap_factory.events.NewExchange.createFilter(
        fromBlock=6627917
    ).get_all_entries()
    token_exchange = {e.args.token: e.args.exchange for e in events}

    for token, exchange in token_exchange.items():
        print(token, exchange)
    """
    address_by_fee = {}

    for fee in fees_bips:
        pool_address = uniswap_factory.getPool(token_address0, token_address1, fee)

        if str(pool_address) != constants.ADDRESS_ZERO:
            print(f"Fee: {fee}, Addr: {pool_address}")
            address_by_fee[fee] = pool_address

    return address_by_fee


# return to_amount?
def swap_tokens(
    pool_contract,
    from_token_address,
    from_token_name,
    from_amount,
    to_token_address,
    to_token_name,
    account,
):

    # get pool info:

    """
    function slot0()
        external
        view
        returns (
            uint160 sqrtPriceX96,
            int24 tick,
            uint16 observationIndex,
            uint16 observationCardinality,
            uint16 observationCardinalityNext,
            uint8 feeProtocol,
            bool unlocked
        );
    """
    pool_info = pool_contract.slot0()
    sqrtPriceX96 = pool_info[0]
    pool_fee = pool_info[5]

    # Follow along on this but for python/brownie
    # https://docs.uniswap.org/sdk/guides/creating-a-trade

    # create quoter
    quoter = interface.IUniswapQuoter(
        config["networks"][network.show_active()]["uniswap_V3_quoter_address"]
    )
    sqrtPriceX96_limit = int(sqrtPriceX96 * math.sqrt(1.01))
    try:
        amount_out_quote = quoter.quoteExactInputSingle.call(
            from_token_address,
            to_token_address,
            pool_fee,
            Web3.toWei(from_amount, "ether"),
            0,
        )
    except ValueError:
        print("caught ValueError")
    finally:
        print(amount_out_quote)

    return

    # check contract token0 and token1
    token1_address = str(pool_contract.token1())

    # set zeroForOne accordingly, true -> token0 to token1, false -> token1 to token0
    zeroForOne = True if token1_address == to_token_address else False

    # set price limit, if zeroForOne is minimum price, if !zeroForOne is maximum price
    # from docs:
    """
    sqrtPriceLimitX96: We set this to zero - which makes this parameter inactive. 
    In production, this value can be used to set the limit for the price the swap 
    will push the pool to, which can help protect against price impact or for 
    setting up logic in a variety of price-relevant mechanisms.
    """

    # attempted implementation but didn't match current ratio by a factor of numerator(?)

    oracle_price_from_token = check_price_usd_chainlink(from_token_name)
    oracle_price_to_token = check_price_usd_chainlink(to_token_name)
    """
    print(f"oracle_from: {oracle_price_from_token}")
    print(f"oracle_to: {oracle_price_to_token}")
    numerator = oracle_price_to_token if zeroForOne else oracle_price_from_token
    denominator = oracle_price_from_token if zeroForOne else oracle_price_to_token
    print(f"inital price limit numerator: {numerator}")
    # change to sqrtX96 format
    # sqrt(price) * 2 ** 96

    numerator = Web3.toWei(numerator, "ether") << 192
    numerator *= 10**-18
    price_limit_sqrt_x96 = int(math.sqrt(numerator / denominator))
    print(f"price_limit_sqrt_x96: {price_limit_sqrt_x96}")
    print(f"price_sqrt_x96: {pool_contract.slot0()[0]}")
    """

    # fails error code SPL with 0, try pool_contract.slot0()[0] * .99 (just a test number since after all the math)
    price_limit_sqrt_x96 = int(pool_contract.slot0()[0] * 0.99)

    # approve use of from_token
    # approve_erc20(amount, spender, erc20_address, account)
    tx_approve = approve_erc20(
        amount=Web3.toWei(from_amount, "ether"),
        spender=pool_contract,
        erc20_address=from_token_address,
        account=account,
    )
    tx_approve.wait(1)

    tx_swap = pool_contract.swap(
        account,
        zeroForOne,
        Web3.toWei(from_amount, "ether"),
        price_limit_sqrt_x96,
        bytes(0),
        {"from": account, "gas_limit": 30000000, "allow_revert": True},
    )

    tx_swap.wait(1)

    # setup callback listener
    # callback = interface.IUniswapV3SwapCallback()
    pass


def main():

    get_pools_prices_usd("weth")
