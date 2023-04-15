from brownie import Contract
from eth_abi import encode_abi
import json

multisig = "PUT YOUR WALLET/MULTISIG ADDRESS HERE"


### Logic
def main(multisig=multisig):
    bbeusd = Contract("0x50Cf90B954958480b8DF7958A9E965752F627124")
    vault = Contract("0xBA12222222228d8Ba445958a75a0704d566BF2C8")
    bbeusdId = "0x50cf90b954958480b8df7958a9e965752f62712400000000000000000000046f"
    usdc = Contract("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48")
    usdt = Contract("0xdAC17F958D2ee523a2206206994597C13D831ec7")
    dai = Contract("0x6B175474E89094C44Da98b954EedeAC495271d0F")
    exitKind = 255  # RecoveryMode Exit
    txs = []

    ## What we want to get out
    recoveryTokens = [usdc.address, usdt.address, dai.address]

    ## Save initial state
    i_bbeusd = bbeusd.balanceOf(multisig)
    i_usdc = usdc.balanceOf(multisig)
    i_usdt = usdt.balanceOf(multisig)
    i_dai = dai.balanceOf(multisig)

    ## get the tokens in of the provided exit pool and withdraw emergency exit the pool.
    pool = bbeusd
    poolId = bbeusdId
    types = ["uint8", "uint256"]

    (pooltokens, amounts, whocares) = vault.getPoolTokens(poolId)
    tokens = {}
    
    ## WD top level tokens

    encoded = encode_abi(types, [exitKind, bbeusd.balanceOf(multisig)])
    txs.append(vault.exitPool(bbeusdId, multisig, multisig, (pooltokens, [0,0,0,0], encoded.hex(), False), {'from': multisig}))

    ## wd from linear pool tokens
    for token in pooltokens:
        tokens[token] = Contract(token)
        token = tokens[token]
        if token.address == bbeusd.address:
            poolId = bbeusdId
        else:
            poolId = token.getPoolId()
        print (f"processing {token.name()} at {token.address}")
        encoded = encode_abi(types, [exitKind, token.balanceOf(multisig)])
        (lineartokens, yyy, zzz) = vault.getPoolTokens(poolId)
        if token != pool:
            # The true at the end of this statement withdraws linear pool tokens to internal balances.
            txs.append(vault.exitPool(poolId, multisig, multisig, (lineartokens, [0,0,0], encoded.hex(), True), {'from': multisig}))

    # wd from internal balances in vault back to address
    oplist = []
    for token in recoveryTokens:
        amount = vault.getInternalBalance(multisig, [token])[0]
        oplist.append((1, token, amount, multisig, multisig))

    txs.append(vault.manageUserBalance(oplist, {'from': multisig}))

    ### Generate multisig payload
    with open("txbuilder_calldata.json", "r") as f:
        endjson = json.load(f)
    endjson["meta"]["createdFromSafeAddress"] = multisig
    txtemplate = endjson["transactions"][0]
    txlist = []

    # Pack all the input data from our txs into txjson format
    for tx in txs:
        calldata = str(tx.input)
        j = txtemplate
        j["data"] = calldata
        txlist.append(dict(j))
    endjson["transactions"] = txlist
    with open("eulerBreakoutOutput.json", "w") as f:
        json.dump(endjson, f)

    # Explain what Happened
    usdc_in = (usdc.balanceOf(multisig) - i_usdc) / 10 ** usdc.decimals()
    usdt_in = (usdt.balanceOf(multisig) - i_usdt) / 10 ** usdt.decimals()
    dai_in = (dai.balanceOf(multisig) - i_dai) / 10 ** dai.decimals()
    i_bbeusd = i_bbeusd / 10 ** bbeusd.decimals()
    print(f"*** Final report.\nBPTS burnt: {i_bbeusd}\nUSDC in: {usdc_in}\nUSDT in: {usdt_in}\nDAI in: {dai_in}\n")

