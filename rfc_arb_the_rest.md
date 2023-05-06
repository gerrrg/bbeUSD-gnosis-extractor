# bb-e-usd Permissioned Arbitrage

## TL;DR
- We have found a way to recover any funds not withdrawn from the paused pools before they  unpause on their own and are pillaged by the dark forrest on June 8th.
- This RFC explains how and why it is necessary and asks for feedback about when it should happen and  any other input.
- Assuming governance agrees to execute on this proposal before the pool unpauses, what currently seems to be 99.9% of all remaining liquid funds in bb-e-usd will likely be recovered removing some urgency to withdraw during gas heavy times.

 
## Background
Inverse Finance has a significant amount of bb-e-usd, estimated to be burnable for over $250k locked in a smart contract.  They can not easily burn/withdraw.

Over the last few days, a group of ballers have worked together to figure out a way to recover these funds.

It involves use the leftover Euler eTokens from TempleDAO's bb-e-usd burn, which currently sit in their multisig, and using them to arb the remaining liquid dollars out of bb-e-usd.

This is not possible while the pool is paused, but the pause on the pool is time limited and will expire on June 8th.  Governance can allow the pool to be unpaused early.

## The Solution and a Proof of Concept on Fork
The code for the PoC on fork can be found [here](https://github.com/BalancerMaxis/bbeUSD-gnosis-extractor/blob/main/scripts/unpauseAndArb_fork.py). 

Here is what it does:

Setup Steps:
1. Transfers the all eDAI and eUSDC from the temple multisig to the Balancer DAO multisig(Vault internal balance transfer).
   - Temple has agreed to help and is reviewing a payload to make this transfer.
2. Reverts back to the old e-token logic on the Euler proxy from the Euler multisig so that a rate can be pulled.
   - Euler is deploying a patch this week that will provide a rate from the onchain bb-e-usd without this step.

Atomic Transaction from the Balancer DAO Multisig:
1. Grants the DAO multisig permission to unpause the pool.
2. For each of bb-e-usdc and bb-e-dai
   1. Unpause the pool.
   2. Swap as much of eDAI or eUSDC as required from internal balances to 99.9% of the liquid DAI or USDC in the pool
   3. The pool can not be repaused as it is in a grace period after the end of the pause window.
3. Removes the DAO multisig's unpause permissions (the Emergency DAO handles pausing/unpausing)

The POC currently results in 763k DAI and 732k USDC being transferred to the DAO multisig.  This number will go down as more dollars are withdrawn from bb-e-usd and the linear pools it is made up of.

## What this means
Before the pool unpauses on its own, and with support from Euler and Temple and authorization by veBAL voters(a BIP), the Balancer DAO Multisig can arb a vast majority of the money left in bb-e-usd out in an atomic transaction before anyone else can get to it.

If there are depositors in the pool beyond Inverse, this money will need to be distributed.  As a result, anyone who has not exited the pool on their own before this happens will some how or another be able to claim the funds.  Depending on the number of addresses this may be via the Claims page or simply via airdrop. 

The goal is to atomically distribute all funds in the same transaction, such that the DAO Multisig never takes custody.

No need to withdraw your 5000 bb-e-usd at 100 gwei ser.

## The question at hand.... Wen?

The big question is when do we do this?

The pause window ends on June 8th.  The DAO multisig executes on Tuesdays for the most part.  This means that the payload should be executed at the latest on June 2nd.

If there is an overwhelming consensus to execute sooner, this could be done as soon as a distribution system has been completed and reviewed.  It should be very similar to the one used to calculate the Euler distribution.

Barring strong interest in expedited execution, and following at least a week of time for discussion.  A BIP will be put forward asking governance permission to unpause the pools and complete the arbitrage and distribute the proceeds as simulated on fork with execution on or around June 2nd.