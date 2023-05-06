### Pasted in a bunch of lower addresses.  Since this is a one off POC just pushing stuff that way.  sorry.

from brownie import Contract, chain
import json
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
BBEDOLA="0x133d241f225750d2c92948e464a5a80111920331"
DOLA="0x865377367054516e17014CcdED1e7d814EDC9ce4"
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
bbedola = Contract.from_abi("ISable", BBEDOLA, IComposableStable)

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
    bbedola.address.lower(): "bbeDOLA"
}

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
    "usdt": usdt.balanceOf(msig),
    "usdc": usdc.balanceOf(msig),
    "dai": dai.balanceOf(msig)
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
RolesToAllow = [bbeusdc.getActionId(bbeusdc.unpause.signature), bbedola.getActionId(bbeusdc.unpause.signature)] ### All Linear Pool Tokens here have the same action id
eulerProxy = Contract.from_abi("Proxy", "0x055DE1CCbCC9Bc5291569a0b6aFFdF8b5707aB16", EulerProxy)
eulerProxy.installModules(["0xbb0D4bb654a21054aF95456a3B29c63e8D1F4c0a"], {"from": EULER_ADMIN}) ## fix rate provider

### Allow dao multisig to unpause in atomic tx
txs.append(authorizer.grantRoles(RolesToAllow, msig, {"from": msig}))

### Unpause and arb the pools.
swapKind = 1 ## 0=GIVEN_IN, 1=GIVEN_OUT
for lt in linearTokens:
    txs.append(lt.unpause({"from": msig}))
    assetIn = lt.getWrappedToken()
    poolId = lt.getPoolId()
    assetOut = Contract(lt.getMainToken())
    userdata = b""
    tokenAmount = initial_liquid_dollars_by_pool[assetOut.symbol()]/1.0006

    singleswap = (poolId, swapKind, assetIn, assetOut, tokenAmount, userdata)

    txs.append(vault.swap(singleswap, INTERNAL_TO_EXTERNAL, 10**50, now+(60*60*24*3), {"from": msig}))


### Handle Dola pool
EXTERNAL_TO_EXTERNAL = (MULTISIG, False, MULTISIG, False)

bbeusd.transfer(msig, 50000*10**18, {"from": vault.address})
txs.append(bbedola.unpause({"from": msig}))
assetIn = bbeusd.address
poolId = bbedola.getPoolId()
assetOut = DOLA
userdata = b""
(tokenAmount, foo, bar, foobar) = vault.getPoolTokenInfo(bbedola.getPoolId(), DOLA)

singleswap = (poolId, 0, assetIn, assetOut, bbeusd.balanceOf(msig), userdata)
### Jack up a-factor to increase output.  This will have to be done by the maxis over multiple days to work in pause
bbedola.startAmplificationParameterUpdate(400, chain.time()+(60*60*24), {"from": "0xf4A80929163C5179Ca042E1B292F5EFBBE3D89e6"})
chain.sleep(60 * 60 * 24 * 1)
chain.mine()
bbedola.startAmplificationParameterUpdate(800, chain.time()+(60*60*24), {"from": "0xf4A80929163C5179Ca042E1B292F5EFBBE3D89e6"})
chain.sleep(60 * 60 * 24 * 1)
chain.mine()
bbedola.startAmplificationParameterUpdate(1600, chain.time()+(60*60*24), {"from": "0xf4A80929163C5179Ca042E1B292F5EFBBE3D89e6"})
chain.sleep(60 * 60 * 24 * 1)
chain.mine()
bbedola.startAmplificationParameterUpdate(3200, chain.time()+(60*60*24), {"from": "0xf4A80929163C5179Ca042E1B292F5EFBBE3D89e6"})
chain.sleep(60 * 60 * 24 * 1)
chain.mine()
now = chain.time()
tx= vault.swap(singleswap, EXTERNAL_TO_EXTERNAL, 100*10**18, now + (60 * 60 * 24 * 3), {"from": msig})
dola=Contract(DOLA)
print(f"DOLA msig balance:{dola.balanceOf(msig)/10**18}")
assert False

txs.append(authorizer.revokeRoles(RolesToAllow, msig, {"from": msig}))


###################################################################################

### Report
for lptoken in linearTokens:
    print(f"\n\nReport for {lptoken.symbol()}")
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
            print(f"Initial Msig Balance: {mibalance}, Current: {mebalance}, Delta:{mdelta} ")



### Generate multisig payload
with open("scripts/txbuilder_calldata.json", "r") as f:
    endjson = json.load(f)
endjson["meta"]["createdFromSafeAddress"] = msig
txtemplate = endjson["transactions"][0]
txlist = []

# Pack all the input data from our txs into txjson format
for tx in txs:
    calldata = str(tx.input)
    j = txtemplate
    j["data"] = calldata
    txlist.append(dict(j))
endjson["transactions"] = txlist
with open("permissionedArb-daoMultisig.json", "w") as f:
    json.dump(endjson, f, indent=3)



assert False, "Done" ## drop to interactive console/don't throw stupid main error
