'use client';
import { useState, useEffect } from 'react';
import Link from 'next/link';
import { connectWallet, switchToAvalanche, payUSDC, fetchConfig, fetchModels, generate } from '@/lib/web3';

export default function TTSStudio() {
  const [models, setModels] = useState<any>({});
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [wallet, setWallet] = useState<any>(null);
  const [config, setConfig] = useState<any>(null);
  const [text, setText] = useState('');
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [btnText, setBtnText] = useState('Select Models First');

  useEffect(() => { loadData(); }, []);
  useEffect(() => { updateBtn(); }, [selected, wallet, text]);

  async function loadData() {
    const cfg = await fetchConfig();
    setConfig(cfg.payment_info);
    const data = await fetchModels('/tts-models');
    setModels(data.available_models);
  }

  function updateBtn() {
    if (selected.size === 0) return setBtnText('Select Models First');
    if (!text.length) return setBtnText('Type Text to Start');
    
    let cost = 0;
    selected.forEach(k => {
      const m = models[k];
      if (m?.cost_per_1000_tokens) cost += (text.length / 1000) * m.cost_per_1000_tokens;
    });
    const displayCost = cost < 0.0001 ? 0.0001 : cost;
    setBtnText(wallet ? `Pay $${displayCost.toFixed(6)} & Speak` : 'Connect Wallet');
  }

  function toggle(key: string) {
    setSelected(prev => {
      const s = new Set(prev);
      if (s.has(key)) s.delete(key);
      else if (s.size < 5) s.add(key);
      else alert('Max 5 voice models');
      return s;
    });
  }

  async function connect() {
    const w = await connectWallet();
    setWallet(w);
  }

  async function run() {
    if (!text.trim() || !wallet || !config) return alert('Enter text');
    setLoading(true);
    try {
      const provider = await switchToAvalanche(wallet.provider);
      const signer = await provider.getSigner();
      
      let cost = 0;
      selected.forEach(k => {
        const m = models[k];
        if (m?.cost_per_1000_tokens) cost += (text.length / 1000) * m.cost_per_1000_tokens;
      });
      
      const receipt = await payUSDC(signer, config, cost);
      const res = await generate('/generate-tts', receipt.hash, { text, models: Array.from(selected) });
      setResults(res.results);
    } catch (e: any) {
      alert(e.message);
    }
    setLoading(false);
  }

  const sortedKeys = Object.keys(models).sort((a, b) => (models[a]?.cost_per_1000_tokens || 0) - (models[b]?.cost_per_1000_tokens || 0));

  return (
    <div style={{ fontFamily: '-apple-system, sans-serif', background: '#FAFAFA', minHeight: '100vh', paddingBottom: '120px' }}>
      
      <div style={{ display: 'flex', justifyContent: 'space-between', padding: '1rem 2rem', background: 'white', borderBottom: '1px solid #E5E5E5', position: 'sticky', top: 0, zIndex: 50 }}>
        <Link href="/" style={{ fontWeight: 800, fontSize: '1.2rem', textDecoration: 'none', color: '#1A1A1A' }}>⚡ Pay Per Compare</Link>
        <button onClick={connect} disabled={!!wallet} style={{ padding: '0 1.5rem', height: '40px', borderRadius: '20px', border: '1px solid #E5E5E5', background: wallet ? '#EFF6FF' : 'white', color: wallet ? '#2563EB' : '#1A1A1A', fontWeight: 600, cursor: 'pointer' }}>
          {wallet ? `${wallet.address.slice(0, 5)}...${wallet.address.slice(-4)}` : 'Connect Wallet'}
        </button>
      </div>

      <div style={{ padding: '2rem' }}>
        <h2 style={{ fontSize: '0.85rem', color: '#757575', textTransform: 'uppercase', letterSpacing: '1.2px', fontWeight: 700, marginBottom: '1.5rem' }}>SELECT VOICE MODELS</h2>
        
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
          {sortedKeys.map(key => (
            <div key={key} onClick={() => toggle(key)} style={{ background: 'white', border: selected.has(key) ? '2px solid #2563EB' : '1px solid #E5E5E5', borderRadius: '16px', padding: '1.2rem', cursor: 'pointer', transition: 'all 0.2s', position: 'relative', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {selected.has(key) && <div style={{ position: 'absolute', top: '-8px', right: '-8px', background: '#2563EB', color: 'white', width: '24px', height: '24px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '14px' }}>✓</div>}
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontWeight: 700, fontSize: '1rem' }}>{key}</span>
                <span style={{ fontSize: '0.75rem', fontWeight: 600, background: '#F3F4F6', padding: '4px 8px', borderRadius: '20px' }}>${models[key]?.cost_per_1000_tokens}/1k chars</span>
              </div>
              <div style={{ fontSize: '0.8rem', color: '#757575', marginTop: 'auto', paddingTop: '0.8rem', borderTop: '1px solid #f0f0f0', display: 'flex', gap: '6px' }}>
                <span>🔊</span>
                <span style={{ fontWeight: 600, fontSize: '0.75rem' }}>MP3/WAV</span>
              </div>
            </div>
          ))}
        </div>

        {results.length > 0 && (
          <div style={{ overflowX: 'auto', paddingBottom: '2rem' }}>
            <div style={{ display: 'flex', gap: '1.5rem', width: 'max-content' }}>
              {results.map((r, i) => (
                <div key={i} style={{ width: '350px', borderRadius: '12px', overflow: 'hidden', background: 'white', boxShadow: '0 4px 12px rgba(0,0,0,0.08)', display: 'flex', flexDirection: 'column' }}>
                  {r.status === 'success' && r.audio_urls?.length > 0 ? (
                    <>
                      <div style={{ padding: '1.5rem', background: '#f9f9f9', display: 'flex', alignItems: 'center', justifyContent: 'center', flex: 1 }}>
                        <audio controls style={{ width: '100%', height: '40px' }}>
                          <source src={r.audio_urls[0]} type="audio/wav" />
                        </audio>
                      </div>
                      <div style={{ padding: '12px', display: 'flex', justifyContent: 'space-between', borderTop: '1px solid #eee' }}>
                        <strong>{r.model_name}</strong>
                        <a href={r.audio_urls[0]} download style={{ color: '#2563EB', fontSize: '0.8rem', textDecoration: 'none' }}>Download ⬇</a>
                      </div>
                    </>
                  ) : (
                    <div style={{ padding: '2rem', textAlign: 'center', color: '#EF4444', background: '#FEF2F2', minHeight: '150px', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                      <div>⚠ Failed</div>
                      <div style={{ fontSize: '0.8rem', marginTop: '5px' }}>{r.error_message || 'Unknown'}</div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <div style={{ position: 'fixed', bottom: 0, left: 0, width: '100%', background: 'white', borderTop: '1px solid #E5E5E5', padding: '1rem 2rem', display: 'flex', gap: '1rem', zIndex: 50 }}>
        <textarea value={text} onChange={(e) => setText(e.target.value)} placeholder="Enter text to convert to speech..." rows={2} style={{ flex: 1, padding: '0.5rem 1rem', border: '1px solid #E5E5E5', borderRadius: '1rem', outline: 'none', resize: 'none', fontFamily: 'inherit' }} />
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <span style={{ fontSize: '0.75rem', color: '#757575', textAlign: 'right' }}>{text.length} chars</span>
          <button onClick={run} disabled={loading || selected.size === 0 || !wallet || !text.length} style={{ padding: '0 2rem', height: '40px', background: '#2563EB', color: 'white', border: 'none', borderRadius: '20px', fontWeight: 600, cursor: 'pointer', opacity: (loading || selected.size === 0 || !wallet || !text.length) ? 0.5 : 1, whiteSpace: 'nowrap' }}>
            {btnText}
          </button>
        </div>
      </div>
    </div>
  );
}