'use client';
import { ethers } from 'ethers';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

// Web3 Functions
export async function connectWallet() {
  if (!window.ethereum) throw new Error('Install MetaMask');
  const provider = new ethers.BrowserProvider(window.ethereum);
  const signer = await provider.getSigner();
  const address = await signer.getAddress();
  return { provider, signer, address };
}

export async function switchToAvalanche(provider: any) {
  const network = await provider.getNetwork();
  if (network.chainId !== 43113n) {
    await window.ethereum.request({
      method: 'wallet_switchEthereumChain',
      params: [{ chainId: '0xa869' }],
    });
    return new ethers.BrowserProvider(window.ethereum);
  }
  return provider;
}

export async function payUSDC(signer: any, config: any, amountUSD: number) {
  const usdcUnits = Math.ceil(amountUSD * 1000000);
  const finalUnits = usdcUnits > 0 ? usdcUnits : 1;
  const ERC20_ABI = ['function transfer(address to, uint256 amount) returns (bool)'];
  const contract = new ethers.Contract(config.contract, ERC20_ABI, signer);
  const tx = await contract.transfer(config.receiver, finalUnits);
  return await tx.wait(1);
}

// API Functions
export async function fetchConfig() {
  const res = await fetch(`${API_BASE}/`);
  return res.json();
}

export async function fetchModels(endpoint: string) {
  const res = await fetch(`${API_BASE}${endpoint}`);
  return res.json();
}

export async function generate(endpoint: string, txHash: string, payload: any) {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Payment-Tx': txHash },
    body: JSON.stringify(payload),
  });
  return res.json();
}