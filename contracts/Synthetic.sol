// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";
import "./ISynthetic.sol";
import "./ICQT.sol";

/**
 * @title Synthetic
 * @dev Synthetic asset management contract for CQT ecosystem
 */
contract Synthetic is ISynthetic, ReentrancyGuard, Ownable {
    using SafeMath for uint256;
    
    ICQT public immutable cqtToken;
    
    mapping(bytes32 => SyntheticAsset) public syntheticAssets;
    mapping(bytes32 => Position) public positions;
    mapping(address => bytes32[]) public userPositions;
    mapping(bytes32 => uint256) public oraclePrices;
    mapping(bytes32 => address) public positionOwners;
    
    bytes32[] public allAssetIds;
    
    uint256 public constant BASIS_POINTS = 10000;
    uint256 public constant LIQUIDATION_REWARD_RATE = 500; // 5% liquidation reward
    uint256 public totalCollateral;
    uint256 public totalSynthetic;
    uint256 private nonce;
    
    constructor(address _cqtToken) Ownable(msg.sender) {
        require(_cqtToken != address(0), "Invalid CQT token address");
        cqtToken = ICQT(_cqtToken);
    }
    
    /**
     * @dev Create new synthetic asset
     */
    function createSyntheticAsset(
        string memory symbol,
        address underlyingAsset,
        uint256 collateralRatio,
        uint256 liquidationThreshold
    ) external onlyOwner returns (bytes32 assetId) {
        require(bytes(symbol).length > 0, "Invalid symbol");
        require(underlyingAsset != address(0), "Invalid underlying asset");
        require(collateralRatio >= 12000, "Collateral ratio too low"); // Min 120%
        require(liquidationThreshold < collateralRatio, "Invalid liquidation threshold");
        
        assetId = keccak256(abi.encodePacked(symbol, underlyingAsset, block.timestamp));
        
        syntheticAssets[assetId] = SyntheticAsset({
            symbol: symbol,
            underlyingAsset: underlyingAsset,
            collateralRatio: collateralRatio,
            liquidationThreshold: liquidationThreshold,
            active: true,
            totalSupply: 0
        });
        
        allAssetIds.push(assetId);
        
        emit SyntheticAssetCreated(assetId, symbol, underlyingAsset);
        
        return assetId;
    }
    
    /**
     * @dev Mint synthetic tokens by providing collateral
     */
    function mintSynthetic(
        bytes32 assetId,
        uint256 collateralAmount,
        uint256 syntheticAmount
    ) external nonReentrant returns (bytes32 positionId) {
        SyntheticAsset storage asset = syntheticAssets[assetId];
        require(asset.active, "Synthetic asset not active");
        require(collateralAmount > 0, "Collateral amount must be greater than 0");
        require(syntheticAmount > 0, "Synthetic amount must be greater than 0");
        
        uint256 oraclePrice = oraclePrices[assetId];
        require(oraclePrice > 0, "Oracle price not set");
        
        // Calculate required collateral
        uint256 requiredCollateral = syntheticAmount.mul(oraclePrice).mul(asset.collateralRatio).div(BASIS_POINTS);
        require(collateralAmount >= requiredCollateral, "Insufficient collateral");
        
        // Transfer collateral to contract
        require(cqtToken.transferFrom(msg.sender, address(this), collateralAmount), "Collateral transfer failed");
        
        positionId = keccak256(abi.encodePacked(msg.sender, assetId, block.timestamp, nonce++));
        
        // Calculate liquidation price
        uint256 liquidationPrice = collateralAmount.mul(BASIS_POINTS).div(syntheticAmount.mul(asset.liquidationThreshold));
        
        // Create position
        positions[positionId] = Position({
            collateralAmount: collateralAmount,
            syntheticAmount: syntheticAmount,
            liquidationPrice: liquidationPrice,
            lastUpdateTime: block.timestamp,
            active: true
        });
        
        positionOwners[positionId] = msg.sender;
        userPositions[msg.sender].push(positionId);
        
        // Update global stats
        asset.totalSupply = asset.totalSupply.add(syntheticAmount);
        totalCollateral = totalCollateral.add(collateralAmount);
        totalSynthetic = totalSynthetic.add(syntheticAmount);
        
        // Mint synthetic tokens to user
        cqtToken.mint(msg.sender, syntheticAmount);
        
        emit SyntheticMinted(positionId, msg.sender, collateralAmount, syntheticAmount);
        
        return positionId;
    }
    
    /**
     * @dev Burn synthetic tokens and withdraw collateral
     */
    function burnSynthetic(
        bytes32 positionId,
        uint256 syntheticAmount
    ) external nonReentrant returns (uint256 collateralReturned) {
        require(positionOwners[positionId] == msg.sender, "Not position owner");
        
        Position storage position = positions[positionId];
        require(position.active, "Position not active");
        require(syntheticAmount <= position.syntheticAmount, "Insufficient synthetic tokens");
        
        // Calculate collateral to return proportionally
        collateralReturned = position.collateralAmount.mul(syntheticAmount).div(position.syntheticAmount);
        
        // Burn synthetic tokens from user
        cqtToken.burn(msg.sender, syntheticAmount);
        
        // Update position
        position.collateralAmount = position.collateralAmount.sub(collateralReturned);
        position.syntheticAmount = position.syntheticAmount.sub(syntheticAmount);
        position.lastUpdateTime = block.timestamp;
        
        if (position.syntheticAmount == 0) {
            position.active = false;
        }
        
        // Update global stats
        totalCollateral = totalCollateral.sub(collateralReturned);
        totalSynthetic = totalSynthetic.sub(syntheticAmount);
        
        // Return collateral to user
        require(cqtToken.transfer(msg.sender, collateralReturned), "Collateral transfer failed");
        
        emit SyntheticBurned(positionId, msg.sender, syntheticAmount, collateralReturned);
        
        return collateralReturned;
    }
    
    /**
     * @dev Add collateral to existing position
     */
    function addCollateral(bytes32 positionId, uint256 collateralAmount) external nonReentrant {
        require(positionOwners[positionId] == msg.sender, "Not position owner");
        require(collateralAmount > 0, "Collateral amount must be greater than 0");
        
        Position storage position = positions[positionId];
        require(position.active, "Position not active");
        
        // Transfer additional collateral
        require(cqtToken.transferFrom(msg.sender, address(this), collateralAmount), "Collateral transfer failed");
        
        // Update position
        position.collateralAmount = position.collateralAmount.add(collateralAmount);
        position.lastUpdateTime = block.timestamp;
        
        // Update global stats
        totalCollateral = totalCollateral.add(collateralAmount);
        
        emit CollateralAdded(positionId, collateralAmount);
    }
    
    /**
     * @dev Remove collateral from position
     */
    function removeCollateral(bytes32 positionId, uint256 collateralAmount) external nonReentrant {
        require(positionOwners[positionId] == msg.sender, "Not position owner");
        require(collateralAmount > 0, "Collateral amount must be greater than 0");
        
        Position storage position = positions[positionId];
        require(position.active, "Position not active");
        require(collateralAmount <= position.collateralAmount, "Insufficient collateral");
        
        // Check if position remains adequately collateralized after removal
        uint256 newCollateralAmount = position.collateralAmount.sub(collateralAmount);
        uint256 newCollateralRatio = calculateCollateralRatioForAmount(positionId, newCollateralAmount);
        
        // Find asset info
        bytes32 assetId = _getAssetIdForPosition(positionId);
        SyntheticAsset memory asset = syntheticAssets[assetId];
        
        require(newCollateralRatio >= asset.collateralRatio, "Would undercollateralize position");
        
        // Update position
        position.collateralAmount = newCollateralAmount;
        position.lastUpdateTime = block.timestamp;
        
        // Update global stats
        totalCollateral = totalCollateral.sub(collateralAmount);
        
        // Return collateral to user
        require(cqtToken.transfer(msg.sender, collateralAmount), "Collateral transfer failed");
        
        emit CollateralRemoved(positionId, collateralAmount);
    }
    
    /**
     * @dev Liquidate undercollateralized position
     */
    function liquidatePosition(bytes32 positionId) external nonReentrant returns (uint256 liquidationReward) {
        require(canLiquidatePosition(positionId), "Position cannot be liquidated");
        
        Position storage position = positions[positionId];
        address positionOwner = positionOwners[positionId];
        
        uint256 syntheticAmount = position.syntheticAmount;
        uint256 collateralAmount = position.collateralAmount;
        
        // Calculate liquidation reward
        liquidationReward = collateralAmount.mul(LIQUIDATION_REWARD_RATE).div(BASIS_POINTS);
        uint256 remainingCollateral = collateralAmount.sub(liquidationReward);
        
        // Burn synthetic tokens (liquidator must provide them)
        require(cqtToken.balanceOf(msg.sender) >= syntheticAmount, "Insufficient synthetic tokens");
        cqtToken.burn(msg.sender, syntheticAmount);
        
        // Mark position as inactive
        position.active = false;
        
        // Update global stats
        totalCollateral = totalCollateral.sub(collateralAmount);
        totalSynthetic = totalSynthetic.sub(syntheticAmount);
        
        // Transfer liquidation reward to liquidator
        require(cqtToken.transfer(msg.sender, liquidationReward), "Reward transfer failed");
        
        // Return remaining collateral to position owner
        if (remainingCollateral > 0) {
            require(cqtToken.transfer(positionOwner, remainingCollateral), "Collateral return failed");
        }
        
        emit PositionLiquidated(positionId, msg.sender, liquidationReward);
        
        return liquidationReward;
    }
    
    /**
     * @dev Get synthetic asset information
     */
    function getSyntheticAsset(bytes32 assetId) external view returns (SyntheticAsset memory asset) {
        return syntheticAssets[assetId];
    }
    
    /**
     * @dev Get position information
     */
    function getPosition(bytes32 positionId) external view returns (Position memory position) {
        return positions[positionId];
    }
    
    /**
     * @dev Calculate current collateral ratio for position
     */
    function calculateCollateralRatio(bytes32 positionId) public view returns (uint256 collateralRatio) {
        Position memory position = positions[positionId];
        if (!position.active || position.syntheticAmount == 0) return 0;
        
        bytes32 assetId = _getAssetIdForPosition(positionId);
        uint256 oraclePrice = oraclePrices[assetId];
        
        if (oraclePrice == 0) return 0;
        
        uint256 syntheticValue = position.syntheticAmount.mul(oraclePrice);
        collateralRatio = position.collateralAmount.mul(BASIS_POINTS).div(syntheticValue);
        
        return collateralRatio;
    }
    
    /**
     * @dev Check if position can be liquidated
     */
    function canLiquidatePosition(bytes32 positionId) public view returns (bool canLiquidate) {
        Position memory position = positions[positionId];
        if (!position.active) return false;
        
        bytes32 assetId = _getAssetIdForPosition(positionId);
        SyntheticAsset memory asset = syntheticAssets[assetId];
        
        uint256 currentRatio = calculateCollateralRatio(positionId);
        return currentRatio < asset.liquidationThreshold;
    }
    
    /**
     * @dev Get all positions by user
     */
    function getUserPositions(address user) external view returns (bytes32[] memory positionIds) {
        return userPositions[user];
    }
    
    /**
     * @dev Get all synthetic assets
     */
    function getAllSyntheticAssets() external view returns (bytes32[] memory assetIds) {
        return allAssetIds;
    }
    
    /**
     * @dev Update oracle price for synthetic asset
     */
    function updateOraclePrice(bytes32 assetId, uint256 newPrice) external onlyOwner {
        require(syntheticAssets[assetId].active, "Synthetic asset not active");
        require(newPrice > 0, "Invalid price");
        
        oraclePrices[assetId] = newPrice;
        
        emit OraclePriceUpdated(assetId, newPrice);
    }
    
    /**
     * @dev Get current oracle price
     */
    function getOraclePrice(bytes32 assetId) external view returns (uint256 price) {
        return oraclePrices[assetId];
    }
    
    /**
     * @dev Calculate liquidation price for position
     */
    function calculateLiquidationPrice(bytes32 positionId) external view returns (uint256 liquidationPrice) {
        Position memory position = positions[positionId];
        if (!position.active) return 0;
        
        bytes32 assetId = _getAssetIdForPosition(positionId);
        SyntheticAsset memory asset = syntheticAssets[assetId];
        
        liquidationPrice = position.collateralAmount.mul(BASIS_POINTS).div(position.syntheticAmount.mul(asset.liquidationThreshold));
        
        return liquidationPrice;
    }
    
    /**
     * @dev Get global synthetic system statistics
     */
    function getGlobalStats() external view returns (
        uint256 _totalCollateral,
        uint256 _totalSynthetic,
        uint256 globalCollateralRatio
    ) {
        globalCollateralRatio = totalSynthetic > 0 ? totalCollateral.mul(BASIS_POINTS).div(totalSynthetic) : 0;
        return (totalCollateral, totalSynthetic, globalCollateralRatio);
    }
    
    /**
     * @dev Calculate collateral ratio for specific collateral amount
     */
    function calculateCollateralRatioForAmount(bytes32 positionId, uint256 collateralAmount) public view returns (uint256 collateralRatio) {
        Position memory position = positions[positionId];
        if (!position.active || position.syntheticAmount == 0) return 0;
        
        bytes32 assetId = _getAssetIdForPosition(positionId);
        uint256 oraclePrice = oraclePrices[assetId];
        
        if (oraclePrice == 0) return 0;
        
        uint256 syntheticValue = position.syntheticAmount.mul(oraclePrice);
        collateralRatio = collateralAmount.mul(BASIS_POINTS).div(syntheticValue);
        
        return collateralRatio;
    }
    
    /**
     * @dev Internal function to find asset ID for position
     */
    function _getAssetIdForPosition(bytes32 positionId) internal view returns (bytes32 assetId) {
        // This is a simplified lookup - in practice, you'd store this mapping
        // For now, return the first active asset (placeholder)
        for (uint256 i = 0; i < allAssetIds.length; i++) {
            if (syntheticAssets[allAssetIds[i]].active) {
                return allAssetIds[i];
            }
        }
        return bytes32(0);
    }
    
    /**
     * @dev Set liquidation reward rate
     */
    function setLiquidationRewardRate(uint256 newRate) external onlyOwner {
        require(newRate <= 1000, "Reward rate too high"); // Max 10%
        // Implementation would update the liquidation reward rate
    }
    
    /**
     * @dev Emergency pause synthetic operations
     */
    function emergencyPause() external onlyOwner {
        // Implementation would pause all synthetic operations
    }
}
