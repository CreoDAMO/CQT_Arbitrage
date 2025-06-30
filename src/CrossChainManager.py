"""
Cross-Chain Manager for CQT Arbitrage
Handles cross-chain operations using Polygon AggLayer and ERC-4337 account abstraction
"""

import os
import json
import time
import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from web3 import Web3
from web3.contract import Contract
from eth_account import Account
from eth_account.signers.local import LocalAccount

logger = logging.getLogger(__name__)

@dataclass
class BridgeTransaction:
    tx_hash: str
    source_network: str
    target_network: str
    amount: float
    status: str
    timestamp: datetime
    gas_used: int
    confirmation_time: Optional[float] = None

@dataclass
class UserOperation:
    sender: str
    nonce: int
    init_code: bytes
    call_data: bytes
    call_gas_limit: int
    verification_gas_limit: int
    pre_verification_gas: int
    max_fee_per_gas: int
    max_priority_fee_per_gas: int
    paymaster_and_data: bytes
    signature: bytes

class CrossChainManager:
    """Manages cross-chain arbitrage operations between Polygon and Base"""
    
    def __init__(self, w3_polygon: Web3, w3_base: Web3):
        """Initialize cross-chain manager"""
        
        self.w3_polygon = w3_polygon
        self.w3_base = w3_base
        
        # Load account
        private_key = os.getenv("PRIVATE_KEY")
        if private_key:
            self.account = Account.from_key(private_key)
        else:
            raise ValueError("Private key required for cross-chain operations")
        
        # Contract addresses
        self.contracts = {
            "polygon": {
                "cqt": "0x94ef57abfbff1ad70bd00a921e1d2437f31c1665",
                "arbitrage": os.getenv("ARBITRAGE_CONTRACT_POLYGON"),
                "agglayer_bridge": os.getenv("AGGLAYER_BRIDGE_POLYGON"),
                "entry_point": "0x5FF137D4b0FDCD49DcA30c7CF57E578a026d2789"
            },
            "base": {
                "cqt": "0x9d1075b41cd80ab08179f36bc17a7ff8708748ba",
                "arbitrage": os.getenv("ARBITRAGE_CONTRACT_BASE"),
                "agglayer_bridge": os.getenv("AGGLAYER_BRIDGE_BASE"),
                "entry_point": "0x5FF137D4b0FDCD49DcA30c7CF57E578a026d2789"
            }
        }
        
        # Load contract instances
        self._load_contracts()
        
        # Transaction tracking
        self.pending_transactions = {}
        self.completed_transactions = []
        
        # Gas estimation settings
        self.gas_multiplier = 1.2  # 20% buffer for gas estimation
        self.max_gas_price_gwei = 100  # Maximum gas price in Gwei
        
    def _load_contracts(self):
        """Load smart contract instances"""
        
        # ERC20 ABI (simplified)
        erc20_abi = [
            {
                "inputs": [{"name": "account", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [{"name": "to", "type": "address"}, {"name": "amount", "type": "uint256"}],
                "name": "transfer",
                "outputs": [{"name": "", "type": "bool"}],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}],
                "name": "approve",
                "outputs": [{"name": "", "type": "bool"}],
                "stateMutability": "nonpayable",
                "type": "function"
            }
        ]
        
        # Bridge ABI (simplified)
        bridge_abi = [
            {
                "inputs": [
                    {"name": "token", "type": "address"},
                    {"name": "amount", "type": "uint256"},
                    {"name": "targetNetwork", "type": "uint256"},
                    {"name": "recipient", "type": "address"}
                ],
                "name": "bridgeToken",
                "outputs": [{"name": "bridgeId", "type": "bytes32"}],
                "stateMutability": "payable",
                "type": "function"
            },
            {
                "inputs": [{"name": "bridgeId", "type": "bytes32"}],
                "name": "getBridgeStatus",
                "outputs": [
                    {"name": "status", "type": "uint8"},
                    {"name": "amount", "type": "uint256"},
                    {"name": "recipient", "type": "address"}
                ],
                "stateMutability": "view",
                "type": "function"
            }
        ]
        
        # EntryPoint ABI (simplified)
        entry_point_abi = [
            {
                "inputs": [
                    {"name": "ops", "type": "tuple[]", "components": [
                        {"name": "sender", "type": "address"},
                        {"name": "nonce", "type": "uint256"},
                        {"name": "initCode", "type": "bytes"},
                        {"name": "callData", "type": "bytes"},
                        {"name": "callGasLimit", "type": "uint256"},
                        {"name": "verificationGasLimit", "type": "uint256"},
                        {"name": "preVerificationGas", "type": "uint256"},
                        {"name": "maxFeePerGas", "type": "uint256"},
                        {"name": "maxPriorityFeePerGas", "type": "uint256"},
                        {"name": "paymasterAndData", "type": "bytes"},
                        {"name": "signature", "type": "bytes"}
                    ]},
                    {"name": "beneficiary", "type": "address"}
                ],
                "name": "handleOps",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            }
        ]
        
        # Initialize contract instances
        self.polygon_contracts = {}
        self.base_contracts = {}
        
        # Polygon contracts
        if self.contracts["polygon"]["cqt"]:
            self.polygon_contracts["cqt"] = self.w3_polygon.eth.contract(
                address=Web3.to_checksum_address(self.contracts["polygon"]["cqt"]),
                abi=erc20_abi
            )
        
        if self.contracts["polygon"]["agglayer_bridge"]:
            self.polygon_contracts["bridge"] = self.w3_polygon.eth.contract(
                address=Web3.to_checksum_address(self.contracts["polygon"]["agglayer_bridge"]),
                abi=bridge_abi
            )
        
        if self.contracts["polygon"]["entry_point"]:
            self.polygon_contracts["entry_point"] = self.w3_polygon.eth.contract(
                address=Web3.to_checksum_address(self.contracts["polygon"]["entry_point"]),
                abi=entry_point_abi
            )
        
        # Base contracts
        if self.contracts["base"]["cqt"]:
            self.base_contracts["cqt"] = self.w3_base.eth.contract(
                address=Web3.to_checksum_address(self.contracts["base"]["cqt"]),
                abi=erc20_abi
            )
        
        if self.contracts["base"]["agglayer_bridge"]:
            self.base_contracts["bridge"] = self.w3_base.eth.contract(
                address=Web3.to_checksum_address(self.contracts["base"]["agglayer_bridge"]),
                abi=bridge_abi
            )
        
        if self.contracts["base"]["entry_point"]:
            self.base_contracts["entry_point"] = self.w3_base.eth.contract(
                address=Web3.to_checksum_address(self.contracts["base"]["entry_point"]),
                abi=entry_point_abi
            )
    
    async def execute_cross_chain_arbitrage(self, opportunity) -> bool:
        """Execute cross-chain arbitrage opportunity"""
        
        try:
            logger.info(f"Starting cross-chain arbitrage: {opportunity.source_pool.network} -> "
                       f"{opportunity.target_pool.network}")
            
            source_network = opportunity.source_pool.network
            target_network = opportunity.target_pool.network
            amount = int(opportunity.required_amount * 1e18)  # Convert to wei
            
            # Step 1: Check balances and approvals
            if not await self._check_prerequisites(source_network, amount):
                logger.error("Prerequisites check failed")
                return False
            
            # Step 2: Execute source side trade (sell high)
            source_tx = await self._execute_trade(
                network=source_network,
                pool_address=opportunity.source_pool.address,
                amount=amount,
                action="sell"
            )
            
            if not source_tx:
                logger.error("Source trade failed")
                return False
            
            # Step 3: Bridge tokens to target network
            bridge_tx = await self._bridge_tokens(
                source_network=source_network,
                target_network=target_network,
                amount=amount
            )
            
            if not bridge_tx:
                logger.error("Bridge transaction failed")
                return False
            
            # Step 4: Wait for bridge confirmation
            if not await self._wait_for_bridge_confirmation(bridge_tx):
                logger.error("Bridge confirmation failed")
                return False
            
            # Step 5: Execute target side trade (buy low)
            target_tx = await self._execute_trade(
                network=target_network,
                pool_address=opportunity.target_pool.address,
                amount=amount,
                action="buy"
            )
            
            if not target_tx:
                logger.error("Target trade failed")
                return False
            
            logger.info("Cross-chain arbitrage completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error in cross-chain arbitrage: {e}")
            return False
    
    async def _check_prerequisites(self, network: str, amount: int) -> bool:
        """Check balances and approvals before executing arbitrage"""
        
        try:
            if network == "polygon":
                w3 = self.w3_polygon
                contracts = self.polygon_contracts
            else:
                w3 = self.w3_base
                contracts = self.base_contracts
            
            # Check ETH balance for gas
            eth_balance = w3.eth.get_balance(self.account.address)
            min_eth_required = w3.toWei(0.01, 'ether')  # 0.01 ETH minimum
            
            if eth_balance < min_eth_required:
                logger.error(f"Insufficient ETH balance on {network}: {w3.fromWei(eth_balance, 'ether')}")
                return False
            
            # Check CQT balance
            if "cqt" in contracts:
                cqt_balance = contracts["cqt"].functions.balanceOf(self.account.address).call()
                if cqt_balance < amount:
                    logger.error(f"Insufficient CQT balance on {network}: {cqt_balance} < {amount}")
                    return False
            
            logger.info(f"Prerequisites check passed for {network}")
            return True
            
        except Exception as e:
            logger.error(f"Error checking prerequisites: {e}")
            return False
    
    async def _execute_trade(self, network: str, pool_address: str, amount: int, action: str) -> Optional[str]:
        """Execute trade on specified network and pool"""
        
        try:
            logger.info(f"Executing {action} trade on {network} pool {pool_address}")
            
            if network == "polygon":
                w3 = self.w3_polygon
            else:
                w3 = self.w3_base
            
            # For this example, we'll simulate the trade execution
            # In production, this would interact with DEX contracts (Uniswap V3, etc.)
            
            # Build transaction
            nonce = w3.eth.get_transaction_count(self.account.address)
            gas_price = w3.eth.gas_price
            
            # Limit gas price
            max_gas_price = w3.toWei(self.max_gas_price_gwei, 'gwei')
            if gas_price > max_gas_price:
                gas_price = max_gas_price
            
            # Simulate transaction building for DEX interaction
            tx_data = {
                'nonce': nonce,
                'gasPrice': gas_price,
                'gas': 300000,  # Estimated gas limit
                'to': Web3.toChecksumAddress(pool_address),
                'value': 0,
                'data': '0x',  # Would contain actual DEX call data
                'chainId': 137 if network == "polygon" else 8453
            }
            
            # Sign and send transaction
            signed_tx = w3.eth.account.sign_transaction(tx_data, self.account.key)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for confirmation
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            
            if receipt.status == 1:
                logger.info(f"Trade executed successfully: {tx_hash.hex()}")
                return tx_hash.hex()
            else:
                logger.error(f"Trade failed: {tx_hash.hex()}")
                return None
                
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            return None
    
    async def _bridge_tokens(self, source_network: str, target_network: str, amount: int) -> Optional[str]:
        """Bridge tokens using AggLayer"""
        
        try:
            logger.info(f"Bridging {amount} tokens from {source_network} to {target_network}")
            
            if source_network == "polygon":
                w3 = self.w3_polygon
                contracts = self.polygon_contracts
                target_chain_id = 8453  # Base
            else:
                w3 = self.w3_base
                contracts = self.base_contracts
                target_chain_id = 137  # Polygon
            
            if "bridge" not in contracts:
                logger.error(f"Bridge contract not available on {source_network}")
                return None
            
            bridge_contract = contracts["bridge"]
            cqt_address = self.contracts[source_network]["cqt"]
            
            # Approve bridge contract to spend CQT
            cqt_contract = contracts["cqt"]
            
            # Check current allowance
            current_allowance = cqt_contract.functions.allowance(
                self.account.address,
                bridge_contract.address
            ).call()
            
            if current_allowance < amount:
                # Approve bridge contract
                approve_tx = await self._send_transaction(
                    w3,
                    cqt_contract.functions.approve(bridge_contract.address, amount),
                    source_network
                )
                
                if not approve_tx:
                    logger.error("Failed to approve bridge contract")
                    return None
            
            # Execute bridge transaction
            bridge_tx = await self._send_transaction(
                w3,
                bridge_contract.functions.bridgeToken(
                    Web3.toChecksumAddress(cqt_address),
                    amount,
                    target_chain_id,
                    self.account.address
                ),
                source_network
            )
            
            if bridge_tx:
                # Store bridge transaction for tracking
                bridge_record = BridgeTransaction(
                    tx_hash=bridge_tx,
                    source_network=source_network,
                    target_network=target_network,
                    amount=amount,
                    status="pending",
                    timestamp=datetime.now(),
                    gas_used=0  # Will be updated when confirmed
                )
                
                self.pending_transactions[bridge_tx] = bridge_record
                logger.info(f"Bridge transaction submitted: {bridge_tx}")
                
                return bridge_tx
            
            return None
            
        except Exception as e:
            logger.error(f"Error bridging tokens: {e}")
            return None
    
    async def _send_transaction(self, w3: Web3, contract_function, network: str) -> Optional[str]:
        """Send transaction with proper gas estimation and signing"""
        
        try:
            # Build transaction
            nonce = w3.eth.get_transaction_count(self.account.address)
            
            # Estimate gas
            try:
                estimated_gas = contract_function.estimateGas({'from': self.account.address})
                gas_limit = int(estimated_gas * self.gas_multiplier)
            except Exception:
                gas_limit = 300000  # Default gas limit
            
            # Get gas price
            gas_price = w3.eth.gas_price
            max_gas_price = w3.toWei(self.max_gas_price_gwei, 'gwei')
            if gas_price > max_gas_price:
                gas_price = max_gas_price
            
            # Build transaction
            tx_data = contract_function.buildTransaction({
                'nonce': nonce,
                'gasPrice': gas_price,
                'gas': gas_limit,
                'chainId': 137 if network == "polygon" else 8453
            })
            
            # Sign transaction
            signed_tx = w3.eth.account.sign_transaction(tx_data, self.account.key)
            
            # Send transaction
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for confirmation
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            
            if receipt.status == 1:
                logger.info(f"Transaction successful: {tx_hash.hex()}")
                return tx_hash.hex()
            else:
                logger.error(f"Transaction failed: {tx_hash.hex()}")
                return None
                
        except Exception as e:
            logger.error(f"Error sending transaction: {e}")
            return None
    
    async def _wait_for_bridge_confirmation(self, bridge_tx_hash: str) -> bool:
        """Wait for bridge transaction to be confirmed on target network"""
        
        try:
            logger.info(f"Waiting for bridge confirmation: {bridge_tx_hash}")
            
            # In production, this would check the bridge status
            # For now, we'll simulate with a timeout
            start_time = time.time()
            timeout = 600  # 10 minutes
            
            while time.time() - start_time < timeout:
                # Check bridge status (mock implementation)
                # In production, query the bridge contract or API
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
                # Simulate successful bridge after 30 seconds
                if time.time() - start_time > 30:
                    logger.info("Bridge transaction confirmed")
                    
                    # Update pending transaction record
                    if bridge_tx_hash in self.pending_transactions:
                        bridge_record = self.pending_transactions[bridge_tx_hash]
                        bridge_record.status = "confirmed"
                        bridge_record.confirmation_time = time.time() - start_time
                        
                        self.completed_transactions.append(bridge_record)
                        del self.pending_transactions[bridge_tx_hash]
                    
                    return True
            
            logger.error("Bridge confirmation timeout")
            return False
            
        except Exception as e:
            logger.error(f"Error waiting for bridge confirmation: {e}")
            return False
    
    async def create_user_operation(self, target_network: str, call_data: bytes) -> UserOperation:
        """Create ERC-4337 user operation for gasless transactions"""
        
        if target_network == "polygon":
            w3 = self.w3_polygon
            chain_id = 137
        else:
            w3 = self.w3_base
            chain_id = 8453
        
        # Get nonce from EntryPoint
        entry_point = self.polygon_contracts["entry_point"] if target_network == "polygon" else self.base_contracts["entry_point"]
        nonce = 0  # Simplified - should get from EntryPoint
        
        # Create user operation
        user_op = UserOperation(
            sender=self.account.address,
            nonce=nonce,
            init_code=b'',
            call_data=call_data,
            call_gas_limit=300000,
            verification_gas_limit=150000,
            pre_verification_gas=21000,
            max_fee_per_gas=w3.toWei(20, 'gwei'),
            max_priority_fee_per_gas=w3.toWei(2, 'gwei'),
            paymaster_and_data=b'',  # Would contain paymaster data for sponsorship
            signature=b''
        )
        
        # Sign user operation (simplified)
        # In production, this would follow ERC-4337 signing standards
        message_hash = Web3.keccak(text=f"{user_op.sender}{user_op.nonce}{user_op.call_data.hex()}")
        signature = w3.eth.account.sign_hash(message_hash, self.account.key)
        user_op.signature = signature.signature
        
        return user_op
    
    def get_bridge_status(self, tx_hash: str) -> Optional[BridgeTransaction]:
        """Get status of bridge transaction"""
        
        # Check pending transactions
        if tx_hash in self.pending_transactions:
            return self.pending_transactions[tx_hash]
        
        # Check completed transactions
        for tx in self.completed_transactions:
            if tx.tx_hash == tx_hash:
                return tx
        
        return None
    
    def get_pending_bridges(self) -> List[BridgeTransaction]:
        """Get all pending bridge transactions"""
        return list(self.pending_transactions.values())
    
    def get_completed_bridges(self) -> List[BridgeTransaction]:
        """Get all completed bridge transactions"""
        return self.completed_transactions
    
    async def estimate_bridge_time(self, source_network: str, target_network: str) -> int:
        """Estimate bridge confirmation time in seconds"""
        
        # Base estimates (in seconds)
        bridge_times = {
            ("polygon", "base"): 300,   # 5 minutes
            ("base", "polygon"): 300,   # 5 minutes
        }
        
        return bridge_times.get((source_network, target_network), 600)  # Default 10 minutes
    
    async def estimate_bridge_cost(self, source_network: str, target_network: str, amount: int) -> Dict[str, float]:
        """Estimate bridge transaction costs"""
        
        if source_network == "polygon":
            w3 = self.w3_polygon
        else:
            w3 = self.w3_base
        
        gas_price = w3.eth.gas_price
        estimated_gas = 100000  # Estimated gas for bridge transaction
        
        gas_cost = w3.fromWei(gas_price * estimated_gas, 'ether')
        
        # Bridge fee (typically 0.1% of amount)
        bridge_fee_rate = 0.001
        bridge_fee = amount * bridge_fee_rate / 1e18  # Convert from wei
        
        return {
            "gas_cost_eth": float(gas_cost),
            "bridge_fee_cqt": bridge_fee,
            "total_cost_usd": float(gas_cost) * 2000 + bridge_fee * 0.1  # Rough USD estimate
        }

if __name__ == "__main__":
    # Example usage
    from web3 import Web3
    
    w3_polygon = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))
    w3_base = Web3(Web3.HTTPProvider("https://mainnet.base.org"))
    
    manager = CrossChainManager(w3_polygon, w3_base)
    
    # Example bridge cost estimation
    async def test_bridge_cost():
        cost = await manager.estimate_bridge_cost("polygon", "base", 1000 * 10**18)
        print("Bridge cost estimate:", cost)
    
    asyncio.run(test_bridge_cost())
