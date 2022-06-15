from brownie import network, interface, config


def check_price_usd_chainlink(token):
    # look up price feed address
    # check if it's in the config
    if token == "weth":
        token = "eth"
    feed_usd_name = f"{token}_usd_price_feed"
    if feed_usd_name in config["networks"][network.show_active()]:
        price_feed_address = config["networks"][network.show_active()][feed_usd_name]
        # print(price_feed_address)
    else:
        return -1

    price_feed = interface.AggregatorV3Interface(price_feed_address)
    lateset_price = price_feed.latestRoundData()[1]
    decimals = price_feed.decimals()
    # converted_price = Web3.fromWei(lateset_price, "ether")
    converted_price = lateset_price / 10**decimals
    """
    print(
        f"latest price: {lateset_price}, decimals: {decimals}, converted price: {converted_price}"
    )
    """
    return converted_price


def approve_erc20(amount, spender, erc20_address, account):
    print("Approving ERC20 token...")
    # ABI
    # Address
    erc20 = interface.IERC20(erc20_address)
    tx = erc20.approve(spender, amount, {"from": account})
    tx.wait(1)
    print("Approved!")
    return tx
