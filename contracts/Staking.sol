// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";
import "./IStaking.sol";
import "./ICQT.sol";

/**
 * @title Staking
 * @dev CQT token staking contract with flexible lock periods and rewards
 */
contract Staking is IStaking, ReentrancyGuard, Ownable {
    using SafeMath for uint256;
    
    ICQT public immutable cqtToken;
    
    mapping(address => mapping(bytes32 => StakeInfo)) public stakes;
    mapping(address => mapping(bytes32 => RewardInfo)) public rewards;
    mapping(address => bytes32[]) public userStakes;
    mapping(uint256 => uint256) public rewardRates; // lockPeriod => annual rate in basis points
    
    uint256 public totalStaked;
    uint256 public totalRewardsPaid;
    uint256 public activeStakers;
    uint256 public constant BASIS_POINTS = 10000;
    uint256 public constant SECONDS_PER_YEAR = 31536000;
    uint256 public emergencyPenaltyRate = 2000; // 20% penalty for emergency unstaking
    
    uint256 private nonce;
    
    constructor(address _cqtToken) Ownable(msg.sender) {
        require(_cqtToken != address(0), "Invalid CQT token address");
        cqtToken = ICQT(_cqtToken);
        
        // Set default reward rates
        rewardRates[30 days] = 500;    // 5% APY for 30 days
        rewardRates[90 days] = 800;    // 8% APY for 90 days
        rewardRates[180 days] = 1200;  // 12% APY for 180 days
        rewardRates[365 days] = 1500;  // 15% APY for 365 days
    }
    
    /**
     * @dev Stake CQT tokens
     */
    function stake(uint256 amount, uint256 lockPeriod) external nonReentrant returns (bytes32 stakeId) {
        require(amount > 0, "Amount must be greater than 0");
        require(rewardRates[lockPeriod] > 0, "Invalid lock period");
        require(cqtToken.balanceOf(msg.sender) >= amount, "Insufficient CQT balance");
        
        stakeId = keccak256(abi.encodePacked(msg.sender, block.timestamp, nonce++));
        
        // Transfer CQT tokens to contract
        require(cqtToken.transferFrom(msg.sender, address(this), amount), "Transfer failed");
        
        // Create stake
        stakes[msg.sender][stakeId] = StakeInfo({
            amount: amount,
            timestamp: block.timestamp,
            lockPeriod: lockPeriod,
            rewardRate: rewardRates[lockPeriod],
            active: true
        });
        
        // Initialize rewards
        rewards[msg.sender][stakeId] = RewardInfo({
            totalRewards: 0,
            claimedRewards: 0,
            pendingRewards: 0,
            lastClaimTime: block.timestamp
        });
        
        // Add to user stakes
        userStakes[msg.sender].push(stakeId);
        
        // Update global stats
        totalStaked = totalStaked.add(amount);
        if (userStakes[msg.sender].length == 1) {
            activeStakers = activeStakers.add(1);
        }
        
        emit Staked(msg.sender, amount, lockPeriod, stakeId);
        
        return stakeId;
    }
    
    /**
     * @dev Unstake CQT tokens
     */
    function unstake(bytes32 stakeId) external nonReentrant {
        StakeInfo storage stakeInfo = stakes[msg.sender][stakeId];
        require(stakeInfo.active, "Stake not active");
        require(canUnstake(msg.sender, stakeId), "Lock period not ended");
        
        uint256 amount = stakeInfo.amount;
        
        // Claim pending rewards first
        _claimRewards(msg.sender, stakeId);
        
        // Mark stake as inactive
        stakeInfo.active = false;
        
        // Update global stats
        totalStaked = totalStaked.sub(amount);
        
        // Transfer CQT tokens back to user
        require(cqtToken.transfer(msg.sender, amount), "Transfer failed");
        
        emit Unstaked(msg.sender, stakeId, amount);
    }
    
    /**
     * @dev Claim staking rewards
     */
    function claimRewards(bytes32 stakeId) external nonReentrant returns (uint256 rewardAmount) {
        require(stakes[msg.sender][stakeId].active, "Stake not active");
        
        return _claimRewards(msg.sender, stakeId);
    }
    
    /**
     * @dev Emergency unstake with penalty
     */
    function emergencyUnstake(bytes32 stakeId) external nonReentrant returns (uint256 penaltyAmount) {
        StakeInfo storage stakeInfo = stakes[msg.sender][stakeId];
        require(stakeInfo.active, "Stake not active");
        
        uint256 amount = stakeInfo.amount;
        penaltyAmount = amount.mul(emergencyPenaltyRate).div(BASIS_POINTS);
        uint256 returnAmount = amount.sub(penaltyAmount);
        
        // Claim pending rewards first
        _claimRewards(msg.sender, stakeId);
        
        // Mark stake as inactive
        stakeInfo.active = false;
        
        // Update global stats
        totalStaked = totalStaked.sub(amount);
        
        // Transfer tokens (minus penalty) back to user
        require(cqtToken.transfer(msg.sender, returnAmount), "Transfer failed");
        
        emit EmergencyUnstaked(msg.sender, stakeId, returnAmount, penaltyAmount);
        
        return penaltyAmount;
    }
    
    /**
     * @dev Get stake information
     */
    function getStakeInfo(address staker, bytes32 stakeId) external view returns (StakeInfo memory stakeInfo) {
        return stakes[staker][stakeId];
    }
    
    /**
     * @dev Get reward information
     */
    function getRewardInfo(address staker, bytes32 stakeId) external view returns (RewardInfo memory rewardInfo) {
        RewardInfo memory info = rewards[staker][stakeId];
        info.pendingRewards = calculatePendingRewards(staker, stakeId);
        return info;
    }
    
    /**
     * @dev Calculate pending rewards
     */
    function calculatePendingRewards(address staker, bytes32 stakeId) public view returns (uint256 pendingRewards) {
        StakeInfo memory stakeInfo = stakes[staker][stakeId];
        RewardInfo memory rewardInfo = rewards[staker][stakeId];
        
        if (!stakeInfo.active) return 0;
        
        uint256 timeSinceLastClaim = block.timestamp.sub(rewardInfo.lastClaimTime);
        uint256 annualReward = stakeInfo.amount.mul(stakeInfo.rewardRate).div(BASIS_POINTS);
        pendingRewards = annualReward.mul(timeSinceLastClaim).div(SECONDS_PER_YEAR);
        
        return pendingRewards;
    }
    
    /**
     * @dev Get total staked amount by user
     */
    function getTotalStaked(address staker) external view returns (uint256 totalStakedByUser) {
        bytes32[] memory stakeIds = userStakes[staker];
        
        for (uint256 i = 0; i < stakeIds.length; i++) {
            if (stakes[staker][stakeIds[i]].active) {
                totalStakedByUser = totalStakedByUser.add(stakes[staker][stakeIds[i]].amount);
            }
        }
        
        return totalStakedByUser;
    }
    
    /**
     * @dev Get total rewards earned by user
     */
    function getTotalRewards(address staker) external view returns (uint256 totalRewards) {
        bytes32[] memory stakeIds = userStakes[staker];
        
        for (uint256 i = 0; i < stakeIds.length; i++) {
            totalRewards = totalRewards.add(rewards[staker][stakeIds[i]].totalRewards);
            totalRewards = totalRewards.add(calculatePendingRewards(staker, stakeIds[i]));
        }
        
        return totalRewards;
    }
    
    /**
     * @dev Check if stake can be unstaked
     */
    function canUnstake(address staker, bytes32 stakeId) public view returns (bool) {
        StakeInfo memory stakeInfo = stakes[staker][stakeId];
        return stakeInfo.active && (block.timestamp >= stakeInfo.timestamp.add(stakeInfo.lockPeriod));
    }
    
    /**
     * @dev Set reward rate for different lock periods
     */
    function setRewardRate(uint256 lockPeriod, uint256 rewardRate) external onlyOwner {
        require(rewardRate <= 5000, "Reward rate too high"); // Max 50% APY
        rewardRates[lockPeriod] = rewardRate;
        
        emit RewardRateUpdated(lockPeriod, rewardRate);
    }
    
    /**
     * @dev Get reward rate for lock period
     */
    function getRewardRate(uint256 lockPeriod) external view returns (uint256 rewardRate) {
        return rewardRates[lockPeriod];
    }
    
    /**
     * @dev Get all stakes by user
     */
    function getUserStakes(address staker) external view returns (bytes32[] memory stakeIds) {
        return userStakes[staker];
    }
    
    /**
     * @dev Get global staking statistics
     */
    function getGlobalStats() external view returns (
        uint256 _totalStaked,
        uint256 _totalRewardsPaid,
        uint256 _activeStakers
    ) {
        return (totalStaked, totalRewardsPaid, activeStakers);
    }
    
    /**
     * @dev Set emergency penalty rate
     */
    function setEmergencyPenaltyRate(uint256 newRate) external onlyOwner {
        require(newRate <= 5000, "Penalty rate too high"); // Max 50%
        emergencyPenaltyRate = newRate;
    }
    
    /**
     * @dev Internal function to claim rewards
     */
    function _claimRewards(address staker, bytes32 stakeId) internal returns (uint256 rewardAmount) {
        RewardInfo storage rewardInfo = rewards[staker][stakeId];
        
        rewardAmount = calculatePendingRewards(staker, stakeId);
        
        if (rewardAmount > 0) {
            // Update reward info
            rewardInfo.totalRewards = rewardInfo.totalRewards.add(rewardAmount);
            rewardInfo.claimedRewards = rewardInfo.claimedRewards.add(rewardAmount);
            rewardInfo.lastClaimTime = block.timestamp;
            rewardInfo.pendingRewards = 0;
            
            // Update global stats
            totalRewardsPaid = totalRewardsPaid.add(rewardAmount);
            
            // Mint reward tokens to user
            cqtToken.mint(staker, rewardAmount);
            
            emit RewardsClaimed(staker, stakeId, rewardAmount);
        }
        
        return rewardAmount;
    }
    
    /**
     * @dev Withdraw penalty tokens (only owner)
     */
    function withdrawPenaltyTokens(uint256 amount) external onlyOwner {
        require(amount <= cqtToken.balanceOf(address(this)).sub(totalStaked), "Insufficient penalty tokens");
        require(cqtToken.transfer(owner(), amount), "Transfer failed");
    }
    
    /**
     * @dev Emergency pause (only owner)
     */
    function emergencyPause() external onlyOwner {
        // Implementation would pause all staking operations
        // This is a placeholder for emergency functionality
    }
}
