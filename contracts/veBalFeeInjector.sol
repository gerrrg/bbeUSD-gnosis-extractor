// SPDX-License-Identifier: MIT

pragma solidity 0.8.6;

import "@chainlink/contracts/src/v0.8/ConfirmedOwner.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "interfaces/ILinearPool.sol";



// list of LinearPool Interfaces
// recipient (where to send coinz to)
//  Owner (who can call stuff)
/**
 * @title bb-e-usd ARB
 * @author 0xtritum.eth
 * @notice Handles a 1 time permissioned arbitrag of bb-eusd
 */
contract bbeUSD_arb is ConfirmedOwner, Pausable {

  function do_arb(address[] linearPoolTokens) public onlyOwner {
    for(i=0; i<linearPoolTokens.length; i++) {
       ILinearPool token = ILinearPool(linearPoolTokens[i]);
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
    emit ERC20Swept(token, payee, balance);
    SafeERC20.safeTransfer(IERC20(token), payee, balance);
  }

  // TODO add internal balance sweep function
}
