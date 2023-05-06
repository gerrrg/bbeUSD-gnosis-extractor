### Pasted in a bunch of lower addresses.  Since this is a one off POC just pushing stuff that way.  sorry.

from brownie import Contract
from eth_abi import encode_abi
import json
from bal_addresses import *
from prettytable import PrettyTable
import time

now = time.time()

### Init global tx list
txs = []


### Constants
MULTISIG = "0x10A19e7eE7d7F8a52822f6817de8ea18204F2e4f".lower() ### Should be able to unpause pools
WHALE = "0x4D6175d58C5AceEf30F546C0d5A557efFa53A950" ### Temple Multisig
EULER_ADMIN ="0x25Aa4a183800EcaB962d84ccC7ada58d4e126992" ### Euler msig that can change protocol settings
EULER_OG_ETOKEN_LOGIC="0xbb0D4bb654a21054aF95456a3B29c63e8D1F4c0a"
eUSDC = "0xeb91861f8a4e1c12333f42dce8fb0ecdc28da716".lower()
eUSDT = "0x4d19f33948b99800b6113ff3e83bec9b537c85d2".lower()
eDAI= "0xe025e3ca2be02316033184551d4d3aa22024d9dc".lower()
BBEUSDC = "0xd4e7c1f3da1144c9e2cfd1b015eda7652b4a4399"
BBEUSDT = "0x3c640f0d3036ad85afa2d5a9e32be651657b874f"
BBEDAI = "0xeb486af868aeb3b6e53066abc9623b1041b42bc0"
BBEUSD="0x50Cf90B954958480b8DF7958A9E965752F627124"
VAULT="0xBA12222222228d8Ba445958a75a0704d566BF2C8".lower()
with open("abis/ILinearPool.json", "r") as f:
    ILinearPool = json.load(f)
with open("abis/IComposableStable.json", "r") as f:
    IComposableStable = json.load(f)
with open("abis/eulerProxy.json", "r") as f:
    EulerProxy = json.load(f)


### Setup interfaces and situatuion
vault = Contract(VAULT)
authorizer = Contract.from_explorer("0xA331D84eC860Bf466b4CdCcFb4aC09a1B43F3aE6")
bbeusd = Contract(BBEUSD)

usdc = Contract.from_explorer("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48")
usdt = Contract.from_explorer("0xdAC17F958D2ee523a2206206994597C13D831ec7")
dai = Contract.from_explorer("0x6B175474E89094C44Da98b954EedeAC495271d0F")
bbeusd = Contract.from_abi("ComposableStablePool", BBEUSD, IComposableStable)
bbeusdc = Contract.from_abi(name="ILinearPool", address=BBEUSDC, abi=ILinearPool)
bbeusdt = Contract.from_abi(name="ILinearPool", address=BBEUSDT, abi=ILinearPool)
bbedai = Contract.from_abi(name="ILinearPool", address=BBEDAI, abi=ILinearPool)

whale = WHALE
msig = MULTISIG



### Helpers
token_name_by_address = {
    eUSDC: "eUSDC",
    eDAI: "eDAI",
    eUSDT: "eUSDT",
    usdc.address.lower(): "USDC",
    dai.address.lower(): "DAI",
    usdt.address.lower(): "USDT",
}


def dicts_to_table_string(dict_list, header=None):
    table = PrettyTable(header)
    for d in dict_list:
        table.add_row(list(d.values()))
    return str(table)


def transfer_internal_all(token, source, dest):
    amount = vault.getInternalBalance(source, [token])[0]
    oplist = [(2, token, amount, source, dest)]
    txs.append(vault.manageUserBalance(oplist, {'from': source}))



### Lists
linearTokens = [bbeusdc, bbedai]  ### bbeusdt
etokens = [eUSDC, eDAI] ### USDT is too smol and has other math problems not worth dealing with.


# Steal the whales etoken bags
for token in etokens:
    transfer_internal_all(token, whale, msig)

### Save initial msig state  for reporting

initial_msig_balances ={
    "bbeusd":  bbeusd.balanceOf(msig)/10**bbeusd.decimals(),
    "usdt": usdt.balanceOf(msig) / 10 ** usdt.decimals(),
    "usdc": usdc.balanceOf(msig) / 10 ** usdc.decimals(),
    "dai": dai.balanceOf(msig) / 10 ** dai.decimals()
}
for token in etokens:
    initial_msig_balances[token_name_by_address[token.lower()]] = vault.getInternalBalance(msig,[token])[0]/10**18



### Save initial pools state for reporting
initial_liquid_dollars_by_pool = {}
for lptoken in linearTokens:
    (tokens, balances, foo) = vault.getPoolTokens(lptoken.getPoolId())
    for i in range(len(tokens)):
        if tokens[i] == lptoken:
            continue
        if tokens[i] not in etokens and "-e-" not in token_name_by_address[tokens[i].lower()]:
            initial_liquid_dollars_by_pool[token_name_by_address[tokens[i].lower()]] = balances[i]


#### Print starting state:
print("Starting pool balances:\n")
print(initial_liquid_dollars_by_pool)
print("Starting msig balances:\n")
print(initial_msig_balances)


################################## DO IT ##########################################
INTERNAL_TO_EXTERNAL = (MULTISIG, True, MULTISIG, False)


### Setup stuff that happens before the atomic tx
RolesToAllow = [bbeusdc.getActionId(bbeusdc.unpause.signature)] ### All Linear Pool Tokens here have the same action id
authorizer.grantRoles(RolesToAllow, msig, {"from": msig})
eulerProxy = Contract.from_abi("Proxy", "0x055DE1CCbCC9Bc5291569a0b6aFFdF8b5707aB16", EulerProxy)
eulerProxy.installModules(["0xbb0D4bb654a21054aF95456a3B29c63e8D1F4c0a"], {"from": EULER_ADMIN}) ## fix rate provider

### Unpause and arb the pools.
swapKind = 1 ## 0=GIVEN_IN, 1=GIVEN_OUT
for lt in linearTokens:
    lt.unpause({"from": msig})
    assetIn = lt.getWrappedToken()
    poolId = lt.getPoolId()
    assetOut = Contract(lt.getMainToken())
    userdata = b""
    tokenAmount = initial_liquid_dollars_by_pool[assetOut.symbol()]/1.001

    singleswap = (poolId, swapKind, assetIn, assetOut, tokenAmount, userdata)

    txs.append(vault.swap(singleswap, INTERNAL_TO_EXTERNAL, 10**50, now+(60*60*24*3), {"from": msig}))

###################################################################################

### Report
for lptoken in linearTokens:
    print(f"Report for {lptoken.symbol()}")
    (tokens, balances, foo) = vault.getPoolTokens(lptoken.getPoolId())
    for i in range(len(tokens)):
        if tokens[i] == lptoken:
            continue
        if tokens[i].lower() not in etokens:
            usdtoken = Contract(tokens[i])
            decimals = usdtoken.decimals()
            tname = token_name_by_address[tokens[i].lower()]
            pibalance = initial_liquid_dollars_by_pool[tname] / 10 ** decimals
            pebalance = balances[i] / 10 ** decimals
            pdelta = pebalance - pibalance
            print(f"Initial Pool Balance: {pibalance}, Current: {pebalance}, Delta:{pdelta}")
            mibalance = initial_msig_balances[tname.lower()] / 10 ** decimals
            mebalance = usdtoken.balanceOf(msig) / 10 ** decimals
            mdelta = mebalance - mibalance
            print(f"Initial Msig Balance: {mibalance}, current: {mebalance}, Delta:{mdelta} ")















### Logic


#def main(multisig=msig):
#    bbeusd = Contract.from_explorer("0x50Cf90B954958480b8DF7958A9E965752F627124")
#    vault = Contract.from_explorer("0xBA12222222228d8Ba445958a75a0704d566BF2C8")
#    bbeusdId = bbeusd.getPoolId()
#    usdc = Contract.from_explorer("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48")
#    usdt = Contract.from_explorer("0xdAC17F958D2ee523a2206206994597C13D831ec7")
#    dai = Contract.from_explorer("0x6B175474E89094C44Da98b954EedeAC495271d0F")
#    exitKind = 255  # RecoveryMode Exit
#    txs = []
#
#    ## What we want to get out
#    recoveryTokens = [usdc.address, usdt.address, dai.address]
#
#    ## Save initial state
#    i_bbeusd = bbeusd.balanceOf(multisig)
#    i_usdc = usdc.balanceOf(multisig)
#    i_usdt = usdt.balanceOf(multisig)
#    i_dai = dai.balanceOf(multisig)
#
#    ## get the tokens in of the provided exit pool and withdraw emergency exit the pool.
#    pool = bbeusd
#    poolId = bbeusdId
#    types = ["uint8", "uint256"]
#
#    (pooltokens, amounts, whocares) = vault.getPoolTokens(poolId)
#    tokens = {}
#
#    ## WD top level tokens
#
#    encoded = encode_abi(types, [exitKind, bbeusd.balanceOf(multisig)])
#    txs.append(vault.exitPool(bbeusdId, multisig, multisig, (pooltokens, [0, 0, 0, 0], encoded.hex(), False),
#                              {'from': multisig}))
#
#    ## wd from linear pool tokens
#    for token in pooltokens:
#        tokens[token] = Contract.from_explorer(token)
#        token = tokens[token]
#        if token.address == bbeusd.address:
#            poolId = bbeusdId
#        else:
#            poolId = token.getPoolId()
#        print(f"processing {token.name()} at {token.address}")
#        encoded = encode_abi(types, [exitKind, token.balanceOf(multisig)])
#        (lineartokens, yyy, zzz) = vault.getPoolTokens(poolId)
#        if token != pool:
#            # The true at the end of this statement withdraws linear pool tokens to internal balances.
#            txs.append(vault.exitPool(poolId, multisig, multisig, (lineartokens, [0, 0, 0], encoded.hex(), True),
#                                      {'from': multisig}))
#
#    # wd from internal balances in vault back to address
#    oplist = []
#    for token in recoveryTokens:
#        amount = vault.getInternalBalance(multisig, [token])[0]
#        oplist.append((1, token, amount, multisig, multisig))
#
#    txs.append(vault.manageUserBalance(oplist, {'from': multisig}))
#
#    ### Generate multisig payload
#    with open("txbuilder_calldata.json", "r") as f:
#        endjson = json.load(f)
#    endjson["meta"]["createdFromSafeAddress"] = multisig
#    txtemplate = endjson["transactions"][0]
#    txlist = []
#
#    # Pack all the input data from our txs into txjson format
#    for tx in txs:
#        calldata = str(tx.input)
#        j = txtemplate
#        j["data"] = calldata
#        txlist.append(dict(j))
#    endjson["transactions"] = txlist
#    with open("eulerBreakoutOutput.json", "w") as f:
#        json.dump(endjson, f)
#
#    # Explain what Happened
#    usdc_in = (usdc.balanceOf(multisig) - i_usdc) / 10 ** usdc.decimals()
#    usdt_in = (usdt.balanceOf(multisig) - i_usdt) / 10 ** usdt.decimals()
#    dai_in = (dai.balanceOf(multisig) - i_dai) / 10 ** dai.decimals()
#    i_bbeusd = i_bbeusd / 10 ** bbeusd.decimals()
#    print(f"*** Final report.\nBPTS burnt: {i_bbeusd}\nUSDC in: {usdc_in}\nUSDT in: {usdt_in}\nDAI in: {dai_in}\n")
#
