"""
Web3 Utility Functions
Compatibility layer for Web3.py API changes
"""

from web3 import Web3
from typing import Union

class Web3Utils:
    """Utility class to handle Web3.py version compatibility"""
    
    @staticmethod
    def to_checksum_address(address: str) -> str:
        """Convert address to checksum format"""
        try:
            return Web3.to_checksum_address(address)
        except AttributeError:
            # Fallback for older versions
            return Web3.toChecksumAddress(address)
    
    @staticmethod
    def to_wei(amount: Union[int, float], unit: str) -> int:
        """Convert amount to Wei"""
        try:
            return Web3.to_wei(amount, unit)
        except AttributeError:
            # Fallback for older versions
            return Web3.toWei(amount, unit)
    
    @staticmethod
    def from_wei(amount: int, unit: str) -> Union[int, float]:
        """Convert Wei to specified unit"""
        try:
            return Web3.from_wei(amount, unit)
        except AttributeError:
            # Fallback for older versions
            return Web3.fromWei(amount, unit)
    
    @staticmethod
    def is_connected(w3: Web3) -> bool:
        """Check if Web3 instance is connected"""
        try:
            return w3.is_connected()
        except AttributeError:
            # Fallback for older versions
            return w3.isConnected()
    
    @staticmethod
    def get_transaction_receipt(w3: Web3, tx_hash: str):
        """Get transaction receipt with proper error handling"""
        try:
            return w3.eth.get_transaction_receipt(tx_hash)
        except Exception:
            return w3.eth.getTransactionReceipt(tx_hash)