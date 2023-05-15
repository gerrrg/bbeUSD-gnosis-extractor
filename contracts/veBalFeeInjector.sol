// SPDX-License-Identifier: MIT

pragma solidity 0.8.6;

import "@openzeppelin/contracts/access/Ownable.sol";
// import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@balancer/pkg/interfaces/contracts/solidity-utils/openzeppelin/IERC20.sol";
import "@balancer/pkg/interfaces/contracts/pool-linear/ILinearPool.sol";
import "@balancer/pkg/interfaces/contracts/vault/IVault.sol";
import "@balancer/pkg/interfaces/contracts/vault/IAsset.sol";


// list of LinearPool Interfaces
// recipient (where to send coinz to)
//  Owner (who can call stuff)
/**
 * @title bb-e-usd ARB
 * @author 0xtritum.eth
 * @notice Handles a 1 time permissioned arbitrag of bb-eusd
 */
contract bbeUSD_arb is Ownable {
    IVault vault = IVault(0xBA12222222228d8Ba445958a75a0704d566BF2C8);


    enum SwapKind { GIVEN_IN, GIVEN_OUT }

    function do_arb(address[] memory inputTokens, address[] memory outputTokens, uint256[] memory dustFactor, address payable recipient) public onlyOwner {
        for (uint i = 0; i < inputTokens.length; i++) {
            ILinearPool lt = ILinearPool(inputTokens[i]);
            IERC20 usdToken = IERC20(outputTokens[i]);
            (IERC20[] memory underlyingTokens,uint256[] memory balances,uint256 foo) = vault.getPoolTokens(lt.getPoolId());
            uint256 usdPoolBalance;
            for (uint j = 0; j < underlyingTokens.length; j++) {
                usdPoolBalance = 0;
                if (address(underlyingTokens[i]) == outputTokens[i]) {
                    usdPoolBalance = balances[i];
                }
            }
            require(usdPoolBalance > 0, "zero USD balance in linear pool");


            bytes32 poolId = lt.getPoolId();

            bytes memory userdata;
            uint256 tokenAmount = usdPoolBalance / dustFactor[i];

            IVault.SingleSwap memory singleswap = IVault.SingleSwap(lt.getPoolId(), IVault.SwapKind.GIVEN_IN, IAsset(address(lt.getWrappedToken())),  IAsset(address(lt.getMainToken())), tokenAmount, userdata);

            IVault.FundManagement memory IntToExt = IVault.FundManagement(address(this), true, recipient, false);
            vault.swap(singleswap, IntToExt, 10 ** 50, block.timestamp + (30));

        }
    }

    /**
     * @notice Withdraws the contract balance
   * @param amount The amount of eth (in wei) to withdraw
   * @param payee The address to pay
   */
    function withdraw(uint256 amount, address payable payee) external onlyOwner {
        if (payee == address(0)) {
            revert("zero address");
        }
        payee.transfer(amount);
    }




    /**
     * @notice Sweep the full contract's balance for a given ERC-20 token
   * @param token The ERC-20 token which needs to be swept
   * @param payee The address to pay
   */
    function sweep(address token, address payee) external onlyOwner {
        uint256 balance = IERC20(token).balanceOf(address(this));
        IERC20(token).transfer(payee,balance);
    }

    // TODO add internal balance sweep function
}
