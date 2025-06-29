// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title ISynthetic
 * @dev Interface for synthetic CQT asset management
 */
interface ISynthetic {
    
    struct SyntheticAsset {
        string symbol;
        address underlyingAsset;
        uint256 collateralRatio;
        uint256 liquidationThreshold;
        bool active;
        uint256 totalSupply;
    }
    
    struct Position {
        uint256 collateralAmount;
        uint256 syntheticAmount;
        uint256 liquidationPrice;
        uint256 lastUpdateTime;
        bool active;
    }
    
    /**
     * @dev Create new synthetic asset
     * @param symbol Symbol of synthetic asset
     * @param underlyingAsset Address of underlying asset
     * @param collateralRatio Required collateral ratio (in basis points)
     * @param liquidationThreshold Liquidation threshold (in basis points)
     * @return assetId Unique asset identifier
     */
    function createSyntheticAsset(
        string memory symbol,
        address underlyingAsset,
        uint256 collateralRatio,
        uint256 liquidationThreshold
    ) external returns (bytes32 assetId);
    
    /**
     * @dev Mint synthetic tokens by providing collateral
     * @param assetId Synthetic asset identifier
     * @param collateralAmount Amount of collateral to provide
     * @param syntheticAmount Amount of synthetic tokens to mint
     * @return positionId Unique position identifier
     */
    function mintSynthetic(
        bytes32 assetId,
        uint256 collateralAmount,
        uint256 syntheticAmount
    ) external returns (bytes32 positionId);
    
    /**
     * @dev Burn synthetic tokens and withdraw collateral
     * @param positionId Position identifier
     * @param syntheticAmount Amount of synthetic tokens to burn
     * @return collateralReturned Amount of collateral returned
     */
    function burnSynthetic(
        bytes32 positionId,
        uint256 syntheticAmount
    ) external returns (uint256 collateralReturned);
    
    /**
     * @dev Add collateral to existing position
     * @param positionId Position identifier
     * @param collateralAmount Amount of collateral to add
     */
    function addCollateral(bytes32 positionId, uint256 collateralAmount) external;
    
    /**
     * @dev Remove collateral from position
     * @param positionId Position identifier
     * @param collateralAmount Amount of collateral to remove
     */
    function removeCollateral(bytes32 positionId, uint256 collateralAmount) external;
    
    /**
     * @dev Liquidate undercollateralized position
     * @param positionId Position identifier
     * @return liquidationReward Reward for liquidator
     */
    function liquidatePosition(bytes32 positionId) external returns (uint256 liquidationReward);
    
    /**
     * @dev Get synthetic asset information
     * @param assetId Asset identifier
     * @return asset Synthetic asset information
     */
    function getSyntheticAsset(bytes32 assetId) external view returns (SyntheticAsset memory asset);
    
    /**
     * @dev Get position information
     * @param positionId Position identifier
     * @return position Position information
     */
    function getPosition(bytes32 positionId) external view returns (Position memory position);
    
    /**
     * @dev Calculate current collateral ratio for position
     * @param positionId Position identifier
     * @return collateralRatio Current collateral ratio
     */
    function calculateCollateralRatio(bytes32 positionId) external view returns (uint256 collateralRatio);
    
    /**
     * @dev Check if position can be liquidated
     * @param positionId Position identifier
     * @return canLiquidate True if position can be liquidated
     */
    function canLiquidatePosition(bytes32 positionId) external view returns (bool canLiquidate);
    
    /**
     * @dev Get all positions by user
     * @param user Address of the user
     * @return positionIds Array of position identifiers
     */
    function getUserPositions(address user) external view returns (bytes32[] memory positionIds);
    
    /**
     * @dev Get all synthetic assets
     * @return assetIds Array of asset identifiers
     */
    function getAllSyntheticAssets() external view returns (bytes32[] memory assetIds);
    
    /**
     * @dev Update oracle price for synthetic asset
     * @param assetId Asset identifier
     * @param newPrice New price of underlying asset
     */
    function updateOraclePrice(bytes32 assetId, uint256 newPrice) external;
    
    /**
     * @dev Get current oracle price
     * @param assetId Asset identifier
     * @return price Current price of underlying asset
     */
    function getOraclePrice(bytes32 assetId) external view returns (uint256 price);
    
    /**
     * @dev Calculate liquidation price for position
     * @param positionId Position identifier
     * @return liquidationPrice Price at which position will be liquidated
     */
    function calculateLiquidationPrice(bytes32 positionId) external view returns (uint256 liquidationPrice);
    
    /**
     * @dev Get global synthetic system statistics
     * @return totalCollateral Total collateral in system
     * @return totalSynthetic Total synthetic tokens minted
     * @return globalCollateralRatio Global collateral ratio
     */
    function getGlobalStats() external view returns (
        uint256 totalCollateral,
        uint256 totalSynthetic,
        uint256 globalCollateralRatio
    );
    
    // Events
    event SyntheticAssetCreated(bytes32 indexed assetId, string symbol, address indexed underlyingAsset);
    event SyntheticMinted(bytes32 indexed positionId, address indexed user, uint256 collateralAmount, uint256 syntheticAmount);
    event SyntheticBurned(bytes32 indexed positionId, address indexed user, uint256 syntheticAmount, uint256 collateralReturned);
    event CollateralAdded(bytes32 indexed positionId, uint256 collateralAmount);
    event CollateralRemoved(bytes32 indexed positionId, uint256 collateralAmount);
    event PositionLiquidated(bytes32 indexed positionId, address indexed liquidator, uint256 liquidationReward);
    event OraclePriceUpdated(bytes32 indexed assetId, uint256 newPrice);
}
