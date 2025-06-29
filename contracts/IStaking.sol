// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title IStaking
 * @dev Interface for CQT staking functionality
 */
interface IStaking {
    
    struct StakeInfo {
        uint256 amount;
        uint256 timestamp;
        uint256 lockPeriod;
        uint256 rewardRate;
        bool active;
    }
    
    struct RewardInfo {
        uint256 totalRewards;
        uint256 claimedRewards;
        uint256 pendingRewards;
        uint256 lastClaimTime;
    }
    
    /**
     * @dev Stake CQT tokens
     * @param amount Amount of CQT to stake
     * @param lockPeriod Lock period in seconds
     * @return stakeId Unique stake identifier
     */
    function stake(uint256 amount, uint256 lockPeriod) external returns (bytes32 stakeId);
    
    /**
     * @dev Unstake CQT tokens
     * @param stakeId Stake identifier
     */
    function unstake(bytes32 stakeId) external;
    
    /**
     * @dev Claim staking rewards
     * @param stakeId Stake identifier
     * @return rewardAmount Amount of rewards claimed
     */
    function claimRewards(bytes32 stakeId) external returns (uint256 rewardAmount);
    
    /**
     * @dev Get stake information
     * @param staker Address of the staker
     * @param stakeId Stake identifier
     * @return stakeInfo Stake information
     */
    function getStakeInfo(address staker, bytes32 stakeId) external view returns (StakeInfo memory stakeInfo);
    
    /**
     * @dev Get reward information
     * @param staker Address of the staker
     * @param stakeId Stake identifier
     * @return rewardInfo Reward information
     */
    function getRewardInfo(address staker, bytes32 stakeId) external view returns (RewardInfo memory rewardInfo);
    
    /**
     * @dev Calculate pending rewards
     * @param staker Address of the staker
     * @param stakeId Stake identifier
     * @return pendingRewards Amount of pending rewards
     */
    function calculatePendingRewards(address staker, bytes32 stakeId) external view returns (uint256 pendingRewards);
    
    /**
     * @dev Get total staked amount by user
     * @param staker Address of the staker
     * @return totalStaked Total amount staked
     */
    function getTotalStaked(address staker) external view returns (uint256 totalStaked);
    
    /**
     * @dev Get total rewards earned by user
     * @param staker Address of the staker
     * @return totalRewards Total rewards earned
     */
    function getTotalRewards(address staker) external view returns (uint256 totalRewards);
    
    /**
     * @dev Check if stake can be unstaked
     * @param staker Address of the staker
     * @param stakeId Stake identifier
     * @return canUnstake True if can unstake
     */
    function canUnstake(address staker, bytes32 stakeId) external view returns (bool canUnstake);
    
    /**
     * @dev Set reward rate for different lock periods
     * @param lockPeriod Lock period in seconds
     * @param rewardRate Annual reward rate (in basis points)
     */
    function setRewardRate(uint256 lockPeriod, uint256 rewardRate) external;
    
    /**
     * @dev Get reward rate for lock period
     * @param lockPeriod Lock period in seconds
     * @return rewardRate Annual reward rate
     */
    function getRewardRate(uint256 lockPeriod) external view returns (uint256 rewardRate);
    
    /**
     * @dev Emergency unstake (with penalty)
     * @param stakeId Stake identifier
     * @return penaltyAmount Amount of penalty
     */
    function emergencyUnstake(bytes32 stakeId) external returns (uint256 penaltyAmount);
    
    /**
     * @dev Get all stakes by user
     * @param staker Address of the staker
     * @return stakeIds Array of stake identifiers
     */
    function getUserStakes(address staker) external view returns (bytes32[] memory stakeIds);
    
    /**
     * @dev Get global staking statistics
     * @return totalStaked Total amount staked across all users
     * @return totalRewardsPaid Total rewards paid out
     * @return activeStakers Number of active stakers
     */
    function getGlobalStats() external view returns (
        uint256 totalStaked,
        uint256 totalRewardsPaid,
        uint256 activeStakers
    );
    
    // Events
    event Staked(address indexed staker, uint256 amount, uint256 lockPeriod, bytes32 stakeId);
    event Unstaked(address indexed staker, bytes32 stakeId, uint256 amount);
    event RewardsClaimed(address indexed staker, bytes32 stakeId, uint256 rewardAmount);
    event EmergencyUnstaked(address indexed staker, bytes32 stakeId, uint256 amount, uint256 penalty);
    event RewardRateUpdated(uint256 lockPeriod, uint256 rewardRate);
}
