const { ethers } = require("hardhat");

async function main() {
    console.log("Starting CQT Arbitrage System deployment...");
    
    const [deployer] = await ethers.getSigners();
    console.log("Deploying contracts with account:", deployer.address);
    
    const balance = await deployer.getBalance();
    console.log("Account balance:", ethers.utils.formatEther(balance), "ETH");
    
    // Deploy ZK Proof Verifier
    console.log("\n1. Deploying ZKProofVerifier...");
    const ZKProofVerifier = await ethers.getContractFactory("ZKProofVerifier");
    const zkVerifier = await ZKProofVerifier.deploy();
    await zkVerifier.deployed();
    console.log("ZKProofVerifier deployed to:", zkVerifier.address);
    
    // Deploy Dilithium Signature Verifier
    console.log("\n2. Deploying DilithiumSignature...");
    const DilithiumSignature = await ethers.getContractFactory("DilithiumSignature");
    const dilithium = await DilithiumSignature.deploy();
    await dilithium.deployed();
    console.log("DilithiumSignature deployed to:", dilithium.address);
    
    // EntryPoint address (use existing deployment or mock)
    const entryPointAddress = "0x5FF137D4b0FDCD49DcA30c7CF57E578a026d2789"; // Standard EntryPoint
    
    // AggLayer Bridge address (placeholder)
    const aggLayerBridgeAddress = "0x0000000000000000000000000000000000000001"; // Placeholder
    
    // Deploy main Arbitrage contract
    console.log("\n3. Deploying CryptoQuestEcosystemArbitrage...");
    const CryptoQuestEcosystemArbitrage = await ethers.getContractFactory("CryptoQuestEcosystemArbitrage");
    const arbitrage = await CryptoQuestEcosystemArbitrage.deploy(
        zkVerifier.address,
        dilithium.address,
        entryPointAddress,
        aggLayerBridgeAddress
    );
    await arbitrage.deployed();
    console.log("CryptoQuestEcosystemArbitrage deployed to:", arbitrage.address);
    
    // Deploy Staking contract (if CQT token exists)
    const cqtTokenAddress = process.env.NETWORK === "polygon" 
        ? "0x94ef57abfbff1ad70bd00a921e1d2437f31c1665"
        : "0x9d1075b41cd80ab08179f36bc17a7ff8708748ba";
    
    console.log("\n4. Deploying Staking contract...");
    const Staking = await ethers.getContractFactory("Staking");
    const staking = await Staking.deploy(cqtTokenAddress);
    await staking.deployed();
    console.log("Staking deployed to:", staking.address);
    
    // Deploy Synthetic contract
    console.log("\n5. Deploying Synthetic contract...");
    const Synthetic = await ethers.getContractFactory("Synthetic");
    const synthetic = await Synthetic.deploy(cqtTokenAddress);
    await synthetic.deployed();
    console.log("Synthetic deployed to:", synthetic.address);
    
    // Configure contracts
    console.log("\n6. Configuring contracts...");
    
    // Authorize the arbitrage contract as a verifier
    await zkVerifier.setAuthorizedVerifier(arbitrage.address, true);
    console.log("Authorized arbitrage contract as ZK verifier");
    
    // Authorize the arbitrage contract as a signer
    await dilithium.setAuthorizedSigner(arbitrage.address, true);
    console.log("Authorized arbitrage contract as Dilithium signer");
    
    // Set up reward rates for staking
    await staking.setRewardRate(30 * 24 * 3600, 500);   // 30 days, 5% APY
    await staking.setRewardRate(90 * 24 * 3600, 800);   // 90 days, 8% APY
    await staking.setRewardRate(180 * 24 * 3600, 1200); // 180 days, 12% APY
    await staking.setRewardRate(365 * 24 * 3600, 1500); // 365 days, 15% APY
    console.log("Configured staking reward rates");
    
    // Create synthetic assets (example)
    try {
        const ethAssetId = await synthetic.createSyntheticAsset(
            "sETH", 
            "0x0000000000000000000000000000000000000000", // ETH placeholder
            15000, // 150% collateral ratio
            12000  // 120% liquidation threshold
        );
        console.log("Created synthetic ETH asset");
    } catch (error) {
        console.log("Note: Synthetic asset creation may require additional permissions");
    }
    
    // Save deployment addresses
    const deploymentInfo = {
        network: process.env.HARDHAT_NETWORK || "localhost",
        deployer: deployer.address,
        contracts: {
            ZKProofVerifier: zkVerifier.address,
            DilithiumSignature: dilithium.address,
            CryptoQuestEcosystemArbitrage: arbitrage.address,
            Staking: staking.address,
            Synthetic: synthetic.address
        },
        cqtToken: cqtTokenAddress,
        entryPoint: entryPointAddress,
        aggLayerBridge: aggLayerBridgeAddress,
        deploymentTime: new Date().toISOString()
    };
    
    console.log("\n=== DEPLOYMENT SUMMARY ===");
    console.log(JSON.stringify(deploymentInfo, null, 2));
    
    // Verify contracts on network (if not localhost)
    if (process.env.HARDHAT_NETWORK !== "localhost" && process.env.HARDHAT_NETWORK !== "hardhat") {
        console.log("\n7. Verifying contracts...");
        
        try {
            await hre.run("verify:verify", {
                address: zkVerifier.address,
                constructorArguments: []
            });
            console.log("ZKProofVerifier verified");
        } catch (error) {
            console.log("ZKProofVerifier verification failed:", error.message);
        }
        
        try {
            await hre.run("verify:verify", {
                address: dilithium.address,
                constructorArguments: []
            });
            console.log("DilithiumSignature verified");
        } catch (error) {
            console.log("DilithiumSignature verification failed:", error.message);
        }
        
        try {
            await hre.run("verify:verify", {
                address: arbitrage.address,
                constructorArguments: [
                    zkVerifier.address,
                    dilithium.address,
                    entryPointAddress,
                    aggLayerBridgeAddress
                ]
            });
            console.log("CryptoQuestEcosystemArbitrage verified");
        } catch (error) {
            console.log("CryptoQuestEcosystemArbitrage verification failed:", error.message);
        }
    }
    
    console.log("\n✅ Deployment completed successfully!");
    console.log("You can now run the Python monitoring pipeline and web interface.");
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error("Deployment failed:", error);
        process.exit(1);
    });
