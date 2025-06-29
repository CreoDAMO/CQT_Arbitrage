// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

/**
 * @title ICQT
 * @dev Interface for CQT token with additional functionality
 */
interface ICQT is IERC20 {
    
    /**
     * @dev Mint new CQT tokens
     * @param to Address to mint tokens to
     * @param amount Amount of tokens to mint
     */
    function mint(address to, uint256 amount) external;
    
    /**
     * @dev Burn CQT tokens
     * @param from Address to burn tokens from
     * @param amount Amount of tokens to burn
     */
    function burn(address from, uint256 amount) external;
    
    /**
     * @dev Get total supply across all networks
     * @return totalSupply Total CQT supply
     */
    function getTotalSupply() external view returns (uint256 totalSupply);
    
    /**
     * @dev Lock tokens for cross-chain transfer
     * @param amount Amount to lock
     * @param targetNetwork Target network identifier
     * @return lockId Unique lock identifier
     */
    function lockForBridge(uint256 amount, uint256 targetNetwork) external returns (bytes32 lockId);
    
    /**
     * @dev Unlock tokens from cross-chain transfer
     * @param lockId Lock identifier
     * @param recipient Address to receive unlocked tokens
     */
    function unlockFromBridge(bytes32 lockId, address recipient) external;
    
    /**
     * @dev Check if address is authorized minter
     * @param account Address to check
     * @return authorized True if authorized
     */
    function isMinter(address account) external view returns (bool authorized);
    
    /**
     * @dev Check if address is authorized burner
     * @param account Address to check
     * @return authorized True if authorized
     */
    function isBurner(address account) external view returns (bool authorized);
    
    /**
     * @dev Get locked balance for cross-chain operations
     * @param account Address to check
     * @return locked Amount of locked tokens
     */
    function getLockedBalance(address account) external view returns (uint256 locked);
    
    /**
     * @dev Add authorized minter
     * @param minter Address to authorize
     */
    function addMinter(address minter) external;
    
    /**
     * @dev Remove authorized minter
     * @param minter Address to deauthorize
     */
    function removeMinter(address minter) external;
    
    /**
     * @dev Add authorized burner
     * @param burner Address to authorize
     */
    function addBurner(address burner) external;
    
    /**
     * @dev Remove authorized burner
     * @param burner Address to deauthorize
     */
    function removeBurner(address burner) external;
    
    /**
     * @dev Pause all token operations
     */
    function pause() external;
    
    /**
     * @dev Unpause all token operations
     */
    function unpause() external;
    
    /**
     * @dev Check if token operations are paused
     * @return paused True if paused
     */
    function isPaused() external view returns (bool paused);
    
    // Events
    event TokensMinted(address indexed to, uint256 amount);
    event TokensBurned(address indexed from, uint256 amount);
    event TokensLocked(address indexed owner, uint256 amount, uint256 targetNetwork, bytes32 lockId);
    event TokensUnlocked(bytes32 indexed lockId, address indexed recipient, uint256 amount);
    event MinterAdded(address indexed minter);
    event MinterRemoved(address indexed minter);
    event BurnerAdded(address indexed burner);
    event BurnerRemoved(address indexed burner);
    event TokensPaused();
    event TokensUnpaused();
}
