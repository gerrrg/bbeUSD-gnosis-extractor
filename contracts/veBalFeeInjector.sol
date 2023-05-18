/// GERG -- dirname: why is this directory called bbeUSD-gnosis-extractor?
/// GERG -- filename: why is this called veBalFeeInjector? It appears to do no action that relates to that name.
/// GERG -- files: why is there a file called interfaces.sol in this directory that is for IFeeDistributor?
// SPDX-License-Identifier: MIT

pragma solidity 0.8.6;

import "@openzeppelin/contracts/access/Ownable.sol";
import "interfaces/balancer/solidity-utils/openzeppelin/IERC20.sol";
import "interfaces/balancer/pool-linear/ILinearPool.sol";
import "interfaces/balancer/vault/IVault.sol";
import "interfaces/balancer/vault/IAsset.sol";

/// GERG -- threat (theft): `recipient` can be decided by owner at time of execution. Hard-code this like you did with the vault.
/// GERG -- threat (theft): `payee` can be decided by owner at time of execution. Hard-code this like you did with the vault.
/// GERG -- threat (stuck funds): IERC20.transfer() can fail. use SafeERC20 library
/// GERG -- threat (stuck funds): <payable>.transfer(amount) can fail. use (bool sent, bytes memory data) = <payable>.call{value: amount}("");
/// GERG -- threat (denial of service): low index pool not having token or having 0 balance will block downstream recovery

/// GERG -- style: why are these comments here? they are self-evident and/or oddly placed
// list of LinearPool Interfaces
// recipient (where to send coinz to)
//  Owner (who can call stuff)

/// GERG -- style: filename != @title != contract name. These should all be the same.
/// GERG -- typo: 0xtritum.eth is available for registration: https://app.ens.domains/0xtritum.eth/register
/// GERG -- style: big mike tells the reader nothing. use github name, ens, or whatever. something useful
/// GERG -- typo: arbitrag -> arbitrage
/// GERG -- typo: bb-eusd -> bb-e-usd
/// GERG -- clarity: NatSpec should explain what this contract does
/**
 * @title bb-e-usd ARB
 * @author 0xtritum.eth + big mike
 * @notice Handles a 1 time permissioned arbitrag of bb-eusd
 */
/// GERG -- accuracy: @notice claims it's a single use contract with no logic to enforce this

/// GERG -- style: contracts should use ProperCase and no underscores
contract bbeUSD_arb is Ownable {
    IVault constant vault = IVault(0xBA12222222228d8Ba445958a75a0704d566BF2C8);

    /// GERG -- style: Add NatSpec comments to this function. Explain what it does, and explain each argument.
    /// GERG -- style: functions should use camelCase and no underscores
    /// GERG -- gas: the following can be `calldata` instead of `memory`: inputTokens, outputTokens, dustFactor
    /// GERG -- threat: `recipient` should be hard-coded and not left up to owner's discretion at runtime
    function do_arb(address[] memory inputTokens, address[] memory outputTokens, uint256[] memory dustFactor, address payable recipient) public onlyOwner {
        /// GERG -- gas (petty): ++i is recommended (cheaper) over i++ in for loop
        for (uint i = 0; i < inputTokens.length; i++) {

            /// GERG -- poorly named var: I assume lt stands for "linear token"? Make it more descriptive like linearPool
            ILinearPool lt = ILinearPool(inputTokens[i]);

            /// GERG -- unused var: were you planning on checking if `underlyingTokens[j] == usdToken[i]`?
            /// GERG -- unnecessary argument: why require argument outputTokens when you can just query them with getMainToken? Less room for error.
            IERC20 usdToken = IERC20(outputTokens[i]);

            /// GERG -- style: put spaces after your commas
            /// GERG -- gas: cache the result from lt.getPoolId locally instead of reading from storage three times
            /// GERG -- unused var: get rid of foo
            (IERC20[] memory underlyingTokens,uint256[] memory balances,uint256 foo) = vault.getPoolTokens(lt.getPoolId());
            /// GERG -- style: inconsistent use of uint and uint256 -- pick one
            uint256 usdPoolBalance;
            /// GERG -- gas (petty): ++j is recommended (cheaper) over j++ in for loop
            for (uint j = 0; j < underlyingTokens.length; j++) {
                if (address(underlyingTokens[j]) == outputTokens[i]) {
                    usdPoolBalance = balances[j];
                    break;
                }
            }

            /// GERG -- clarity: "output token not in pool or has 0 balance"
            /// GERG -- threat (denial of service): low index pool not having token or having 0 balance will block downstream recovery
            require(usdPoolBalance > 0, "zero USD balance in linear pool");

            /// GERG -- unused var: I had recommended caching this locally above; looks like you had that idea, but didn't use the local copy.
            bytes32 poolId = lt.getPoolId();
            /// GERG -- style: userData
            bytes memory userdata;
            /// GERG -- lint: remove space between ) and ;
            /// GERG -- design: why are you using a "dust factor"? Why not calculate how much will be collected in fees and consider those tokens lost? (lowerBound*swapFee)
            /// GERG -- design/math: if you're going to stay with the "dust factor," is this calculation what you actually want?
            uint256 tokenAmount = usdPoolBalance - (usdPoolBalance / dustFactor[i]) ;
            /// GERG -- style: camelCase singleSwap
            /// GERG -- lint: line too long
            /// GERG -- gas: use cached poolId
            IVault.SingleSwap memory singleswap = IVault.SingleSwap(lt.getPoolId(), IVault.SwapKind.GIVEN_OUT, IAsset(address(lt.getWrappedToken())),  IAsset(address(lt.getMainToken())), tokenAmount, userdata);
            /// GERG -- style: camelCase (intToExt)
            IVault.FundManagement memory IntToExt = IVault.FundManagement(address(this), true, recipient, false);
            /// GERG -- logic: where did 10 ** 50 come from?
            /// GERG -- logic: setting a deadline of block.timestamp from a contract will always pass the deadline check. Is this the intended behavior? Also, adding 30 does nothing.
            vault.swap(singleswap, IntToExt, 10 ** 50, block.timestamp + (30));

            /// GERG -- gas: why are you doing N single swaps when this could be a single batchSwap with N steps?
            ///              before loop:
            ///                 create empty array of assets (IAssets)
            ///                 create empty array of swaps (BatchSwapStep)
            ///                 create empty array of limits (uint256)
            ///              in loop:
            ///                 add in/out tokens to assets array
            ///                 populate BatchSwapStep array w/ indices of in/out tokens, of course
            ///                 populate limits
            ///              after loop:
            ///                 populate FundManagement struct
            ///                 set deadline (see comment above about block.timestamp being useless as a deadline)
            ///                 execute batchSwap
        }
    }

    /// GERG -- style: line up these comments
    /**
     * @notice Withdraws the contract balance
   * @param amount The amount of eth (in wei) to withdraw
   * @param payee The address to pay
   */
    /// GERG -- threat: `payee` should be hard-coded and not left up to owner's discretion at runtime
    function withdraw(uint256 amount, address payable payee) external onlyOwner {
        /// GERG -- concise: require(payee != address(0), "Do not transfer to 0 address")
        if (payee == address(0)) {
            revert("zero address");
        }
        payee.transfer(amount);
    }

    /// GERG -- threat: `payee` should be hard-coded and not left up to owner's discretion at runtime
    function sweep(address token, address payee) external onlyOwner {
        uint256 balance = IERC20(token).balanceOf(address(this));
        IERC20(token).transfer(payee,balance);
    }

    /// GERG -- threat: `payee` should be hard-coded and not left up to owner's discretion at runtime
    /// GERG -- style: functions should use camelCase and no underscores
    function internal_sweep(IAsset token, uint256 amount, address payable payee) external onlyOwner {
        /// GERG -- style: camelCase opList
        IVault.UserBalanceOp[] memory oplist = new IVault.UserBalanceOp[](1);

        /// GERG -- design: This should probably be WITHDRAW_INTERNAL so that payee doesn't need to do another manageUserBalance operation.
        oplist[0] = IVault.UserBalanceOp(IVault.UserBalanceOpKind.TRANSFER_INTERNAL, token, amount, address(this), payee);
        vault.manageUserBalance(oplist);
    }

}
