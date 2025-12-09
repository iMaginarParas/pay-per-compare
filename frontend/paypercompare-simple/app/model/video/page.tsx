'use client';
import { useState, useEffect } from 'react';
import Link from 'next/link';
import { connectWallet, switchToAvalanche, payUSDC, fetchConfig, fetchModels, generate } from '@/lib/web3';

export default function VideoStudio() {
  const [models, setModels] = useState<any>({});
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [wallet, setWallet] = useState<any>(null);
  const [config, setConfig] = useState<any>(null);
  const [prompt, setPrompt] = useState('');
  const [image, setImage] = useState('');
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [btnText, setBtnText] = useState('Select Models First');

  useEffect(() => { loadData(); }, []);
  useEffect(() => { updateBtn(); }, [selected, wallet]);

  async function loadData() {
    const cfg = await fetchConfig();
    setConfig(cfg.payment_info);
    const data = await fetchModels('/video-models');
    setModels(data.available_models);
  }

  function updateBtn() {
    if (selected.size === 0) return setBtnText('Select Models First');
    const cost = Array.from(selected).reduce((sum, k) => sum + (models[k]?.cost_usd || 0), 0);
    setBtnText(wallet ? `Pay $${cost.toFixed(4)} & Generate (${selected.size})` : 'Connect Wallet');
  }

  function toggle(key: string) {
    setSelected(prev => {
      const s = new Set(prev);
      if (s.has(key)) s.delete(key);
      else if (s.size < 4) s.add(key);
      else alert('Max 4 video models');
      return s;
    });
  }

  async function connect() {
    const w = await connectWallet();
    setWallet(w);
  }

  function handleImageUpload(e: any) {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => setImage((ev.target?.result as string).split(',')[1]);
    reader.readAsDataURL(file);
  }

  async function run() {
    if (!prompt.trim() || !wallet || !config) return alert('Enter prompt');
    const requiresImage = Array.from(selected).some(k => models[k]?.type === 'image-to-video');
    if (requiresImage && !image) return alert('Upload an image for image-to-video models');
    
    setLoading(true);
    try {
      const provider = await switchToAvalanche(wallet.provider);
      const signer = await provider.getSigner();
      const cost = Array.from(selected).reduce((sum, k) => sum + (models[k]?.cost_usd || 0), 0);
      const receipt = await payUSDC(signer, config, cost);
      const res = await generate('/generate-video', receipt.hash, { prompt, models: Array.from(selected), image });
      setResults(res.results);
    } catch (e: any) {
      alert(e.message);
    }
    setLoading(false);
  }

  const sortedKeys = Object.keys(models).sort((a, b) => (models[a]?.cost_usd || 0) - (models[b]?.cost_usd || 0));

  return (
    <div style={{ fontFamily: '-apple-system, sans-serif', background: '#FAFAFA', minHeight: '100vh', paddingBottom: '100px' }}>
      
      <div style={{ display: 'flex', justifyContent: 'space-between', padding: '1rem 2rem', background: 'white', borderBottom: '1px solid #E5E5E5', position: 'sticky', top: 0, zIndex: 50 }}>
        <Link href="/" style={{ fontWeight: 800, fontSize: '1.2rem', textDecoration: 'none', color: '#1A1A1A' }}>⚡ Pay Per Compare</Link>
        <button onClick={connect} disabled={!!wallet} style={{ padding: '0 1.5rem', height: '40px', borderRadius: '20px', border: '1px solid #E5E5E5', background: wallet ? '#EFF6FF' : 'white', color: wallet ? '#2563EB' : '#1A1A1A', fontWeight: 600, cursor: 'pointer' }}>
          {wallet ? `${wallet.address.slice(0, 5)}...${wallet.address.slice(-4)}` : 'Connect Wallet'}
        </button>
      </div>

      <div style={{ padding: '2rem' }}>
        <h2 style={{ fontSize: '0.85rem', color: '#757575', textTransform: 'uppercase', letterSpacing: '1.2px', fontWeight: 700, marginBottom: '1.5rem' }}>SELECT VIDEO MODELS</h2>
        
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
          {sortedKeys.map(key => (
            <div key={key} onClick={() => toggle(key)} style={{ background: 'white', border: selected.has(key) ? '2px solid #2563EB' : '1px solid #E5E5E5', borderRadius: '16px', padding: '1.2rem', cursor: 'pointer', transition: 'all 0.2s', position: 'relative', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {selected.has(key) && <div style={{ position: 'absolute', top: '-8px', right: '-8px', background: '#2563EB', color: 'white', width: '24px', height: '24px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '14px' }}>✓</div>}
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontWeight: 700, fontSize: '1rem' }}>{key}</span>
                <span style={{ fontSize: '0.75rem', fontWeight: 600, background: '#F3F4F6', padding: '4px 8px', borderRadius: '20px' }}>${models[key]?.cost_usd}</span>
              </div>
              <div style={{ fontSize: '0.8rem', color: '#757575', marginTop: 'auto', paddingTop: '0.8rem', borderTop: '1px solid #f0f0f0', display: 'flex', gap: '6px' }}>
                <span>{models[key]?.type === 'image-to-video' ? '🖼️ ➔ 🎥' : '📝 ➔ 🎥'}</span>
                <span style={{ fontWeight: 600, fontSize: '0.75rem' }}>{models[key]?.type === 'image-to-video' ? 'Image Req.' : 'Text Only'}</span>
              </div>
            </div>
          ))}
        </div>

        {results.length > 0 && (
          <div style={{ overflowX: 'auto', paddingBottom: '2rem' }}>
            <div style={{ display: 'flex', gap: '1.5rem', width: 'max-content' }}>
              {results.map((r, i) => (
                <div key={i} style={{ width: '400px', borderRadius: '12px', overflow: 'hidden', background: 'white', boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }}>
                  {r.status === 'success' && r.video_urls?.length > 0 ? (
                    <>
                      <video controls autoPlay loop muted playsInline style={{ width: '100%', background: '#000' }}>
                        <source src={r.video_urls[0]} type="video/mp4" />
                      </video>
                      <div style={{ padding: '12px', display: 'flex', justifyContent: 'space-between' }}>
                        <strong>{r.model_name}</strong>
                        <a href={r.video_urls[0]} download style={{ color: '#2563EB', fontSize: '0.8rem', textDecoration: 'none' }}>Download ⬇</a>
                      </div>
                    </>
                  ) : (
                    <div style={{ padding: '2rem', textAlign: 'center', color: '#EF4444', background: '#FEF2F2', minHeight: '200px' }}>
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
        <label style={{ width: '40px', height: '40px', borderRadius: '50%', background: '#F3F4F6', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer' }}>
          📷
          <input type="file" accept="image/*" onChange={handleImageUpload} style={{ display: 'none' }} />
        </label>
        <input value={prompt} onChange={(e) => setPrompt(e.target.value)} placeholder="Enter your prompt..." style={{ flex: 1, height: '40px', padding: '0 1rem', border: '1px solid #E5E5E5', borderRadius: '20px', outline: 'none' }} />
        <button onClick={run} disabled={loading || selected.size === 0 || !wallet} style={{ padding: '0 2rem', height: '40px', background: '#2563EB', color: 'white', border: 'none', borderRadius: '20px', fontWeight: 600, cursor: 'pointer', opacity: (loading || selected.size === 0 || !wallet) ? 0.5 : 1, whiteSpace: 'nowrap' }}>
          {btnText}
        </button>
      </div>
    </div>
  );
}