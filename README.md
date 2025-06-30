# CQT Arbitration Trading Bot README

## Overview
The CQT Arbitration Trading Bot is an innovative DeFi solution designed to perform cross-chain arbitrage and manage liquidity distribution across Polygon and Base networks. It leverages zero-knowledge (ZK) technology, ERC-4337 account abstraction, Polygon AggLayer, and Coinbase Developer Platform (CDP) tools (OnchainKit, Bundler and Paymaster, Agent Kit). The bot is deployed on Polygon with CQT/WETH and CQT/WMATIC pools (7.5T CQT each) and on Base with a live CQT/USDC pool (pending significant liquidity). A built-in liquidity provider (BLP) and micro miner AI enhance self-sustainability, with a Rust wrapper ensuring security and performance.

- **Purpose**: Optimize arbitrage opportunities and liquidity across chains using mined native coins and arbitrage profits.
- **Current Status**: Deployed on Polygon and Base, with active development on BLP and micro miner integration.
- **Last Updated**: June 30, 2025, 05:04 AM EDT.

## Project Details
- **Deployment Wallet**: `0xCc380FD8bfbdF0c020de64075b86C84c2BB0AE79` (holds 39.23T CQT, 1 MATIC on Polygon, and Base ETH for gas).
- **Wallet Contract**: `0xF60d96CFA71c6fe7FE18cA028041CA7f42b543bd` (to be deployed).
- **LP Addresses**:
  - **Polygon**:
    - CQT/WETH: `0xb1e0b26...` (10.609.80–10.737.90 CQT = 1 WETH)
    - CQT/WMATIC: `0x0b3cd8a...` (1.53109–2.05436 CQT = 1 WMATIC)
  - **Base**: CQT/USDC (Uniswap pool, address to be confirmed via https://dexscreener.com/base/0xd874aeaef376229c8d41d392c9ce272bd41e57d6a82fbd7920652ff89317314a)
- **Token Addresses**:
  - CQT (Base): `0x9d1075b41cd80ab08179f36bc17a7ff8708748ba`
  - USDC (Base): `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`
- **Networks**:
  - Polygon: `https://polygon-rpc.com`
  - Base: `https://mainnet.base.org`

## Features
- **Arbitrage**: Executes trades based on price discrepancies (e.g., Polygon’s $0.2325–$0.235 USD vs. Base’s $0.10 USD for 1 CQT).
- **Liquidity Management**: Distributes 15T CQT on Polygon, with Base pending, using a BLP powered by arbitrage profits.
- **Cross-Chain Support**: Integrates Polygon AggLayer for Base-Polygon transactions.
- **Account Abstraction**: Uses CDP Bundler and Paymaster for gasless operations.
- **Automation**: Employs Agent Kit and a micro miner AI to seed liquidity with mined ETH and MATIC.
- **Monitoring**: Real-time analysis with LSTM predictions.
- **Security**: Rust wrapper prevents vulnerabilities in critical components.
- **UI**: OnchainKit-powered React dashboard for visualization.

## Prerequisites
- **Node.js**: v16 or higher
- **Python**: v3.8 or higher
- **Rust**: v1.75 or higher
- **Dependencies**:
  - `npm install @openzeppelin/contracts @nomiclabs/hardhat-waffle hardhat @coinbase/onchainkit chart.js react react-dom`
  - `pip install tensorflow web3 thegraph-python redis requests`
  - `cargo install --locked web3 tokio serde serde_json rustc-serialize`
- **CDP Configuration**: Register with `projectId=eb262ee5-9b74-4fa6-8891-0ae680cfea10`, obtain API keys.
- **Wallet**: Private key for `0xCc380FD8bfbdF0c020de64075b86C84c2BB0AE79` (securely in `hardhat.config.js`).

## Installation
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd cqt-arbitrage-bot
   ```
2. Install Node.js dependencies:
   ```bash
   npm install
   ```
3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   (Create `requirements.txt` with listed packages if absent.)
4. Install Rust dependencies:
   ```bash
   cargo build --release
   ```
5. Configure `hardhat.config.js` with the private key:
   ```javascript
   accounts: ["<private-key-for-0xCc380FD8bfbdF0c020de64075b86C84c2BB0AE79>"]
   ```
6. Set CDP API keys in environment variables (e.g., `export CDP_API_KEY=<your-key>`).

## Codebase Structure
- **contracts/**:
  - `CryptoQuestEcosystemArbitrage.sol`: Main contract with BLP and micro miner hooks.
  - `ZKProofVerifier.sol`: ZK proof logic.
  - `DilithiumSignature.sol`: Quantum-resistant signatures.
  - `ICQT.sol`, `IStaking.sol`, `ISynthetic.sol`, `Staking.sol`, `Synthetic.sol`: Supporting contracts.
- **scripts/**: `deploy.sh`, `addLiquidity.js`.
- **tests/**: `SuperStressEnhanced.t.sol`, `NuclearStress.t.sol`, `DeFiApocalypse.t.sol`.
- **pipeline/**: `CryptoQuestPipeline.py` with micro miner AI.
- **rust/**: `cqt-bot-wrapper` for secure logic (miner, BLP, arbitrage).
- **ui/**: `index.jsx` for the React dashboard.
- **docs/**: `final_report.md`.

## Usage
1. **Run Tests**:
   ```bash
   forge test --match-contract SuperStressEnhanced -vvv
   forge test --match-contract NuclearStress -vvv
   forge test --match-contract DeFiApocalypse -vvv
   cargo test
   ```
2. **Deploy the Bot**:
   ```bash
   ./deploy.sh
   ```
   - Audits, deploys, funds Polygon pools (7.5T CQT each), sets up Base pool, launches arbitrage.
3. **Monitor Pipeline**:
   ```bash
   python pipeline/cryptoQuestPipeline.py --v3Pools "0xb1e0b26...,0x0b3cd8a...,<base-pool-address>" --crossChain "polygon:0x1F98431c8aD98523631AE4a59f267346ea31F984,base:0x33128a8fC17869897dcE68Ed026d694621f6FDfD" --agent-api https://api.cdp.coinbase.com/agent-kit
   ```
4. **Launch UI**:
   - Run `index.jsx` with a backend API.

## Deployment Timeline
- **June 28, 2025 (2:07 PM EDT)**: Initial Polygon and Base deployment.
- **June 29, 2025**: Final testing and Base pool sealing.
- **June 30–July 1, 2025**: Activate BLP, micro miner, and Rust wrapper.

## Validation
- Re-run Forge and Cargo tests for multi-network and security.
- Validate pipeline with Base CQT data and Agent Kit.
- Verify wallet balances on PolygonScan and BaseScan.

## Integrations
- **Polygon AggLayer**: Enables cross-chain liquidity (full ZK post-Q3 2025).
- **Coinbase CDP**:
  - **OnchainKit**: Powers UI.
  - **Bundler and Paymaster**: Gasless transactions.
  - **Agent Kit**: AI automation.
- **Rust Wrapper**: Secures miner, BLP, and arbitrage.

## Innovations
- **BLP**: Funds all pools with 20% arbitrage profits.
- **Micro Miner AI**: Mines ETH and MATIC to seed reserves.
- **Rust Security**: Prevents vulnerabilities with FFI to Python/Solidity.

## Recommendations
- **Short-Term**: Confirm Base pool address, seed with 0.01 ETH and 1 MATIC.
- **Long-Term**: Scale with AggLayer’s multistack support.
- **Security**: Audit Rust and Solidity code.

## Contributing
- Fork, branch, and submit pull requests.
- Report issues via the issue tracker.

## License
MIT License (see LICENSE file).

## Contact
Support jacquedegraff81@gmail.com `<support@CreoDAMO>

--
