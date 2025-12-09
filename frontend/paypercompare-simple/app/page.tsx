'use client';
import Link from 'next/link';

export default function Home() {
  return (
    <div style={{ fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif', background: '#FAFAFA', minHeight: '100vh' }}>
      
      {/* Landing Page */}
      <nav style={{ padding: '2rem', display: 'flex', justifyContent: 'space-between' }}>
        <div style={{ fontWeight: 800, fontSize: '1.2rem' }}>⚡ Pay Per Compare x402</div>
      </nav>

      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', padding: '4rem 2rem', minHeight: '70vh', justifyContent: 'center' }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', background: 'rgba(232,65,66,0.1)', color: '#E84142', padding: '8px 16px', borderRadius: '30px', fontSize: '0.85rem', fontWeight: 700, marginBottom: '2rem', border: '1px solid rgba(232,65,66,0.2)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
          <span style={{ width: '8px', height: '8px', background: '#E84142', borderRadius: '50%', boxShadow: '0 0 8px #E84142' }}></span>
          Built on Avalanche Testnet
        </div>

        <h1 style={{ fontSize: '3.5rem', lineHeight: 1.1, marginBottom: '1.5rem', maxWidth: '900px', fontWeight: 900, background: 'linear-gradient(135deg, #1A1A1A 0%, #4B5563 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
          Run and compare 100+ Open Source and Closed Source models at the cheapest cost.
        </h1>

        <p style={{ fontSize: '1.25rem', color: '#757575', maxWidth: '600px', marginBottom: '2.5rem', lineHeight: 1.6 }}>
          Access Image and Video generation models instantly. Pay per generation with USDC. No monthly subscriptions.
        </p>

        {/* Workspace Selection */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '2rem', maxWidth: '1200px', width: '100%', marginTop: '3rem' }}>
          
          <Link href="/model/image" style={{ textDecoration: 'none' }}>
            <div style={{ background: 'white', border: '1px solid #E5E5E5', borderRadius: '20px', padding: '2.5rem', color: '#1A1A1A', transition: 'all 0.3s', cursor: 'pointer', minHeight: '250px', display: 'flex', flexDirection: 'column', gap: '1rem' }} 
                 onMouseOver={(e) => { e.currentTarget.style.transform = 'translateY(-8px)'; e.currentTarget.style.boxShadow = '0 20px 40px -10px rgba(0,0,0,0.1)'; }}
                 onMouseOut={(e) => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.boxShadow = 'none'; }}>
              <span style={{ position: 'absolute', top: '20px', right: '20px', fontSize: '0.75rem', padding: '4px 8px', background: '#F3F4F6', borderRadius: '6px', fontWeight: 600 }}>Popular</span>
              <div style={{ width: '60px', height: '60px', background: '#F3F4F6', borderRadius: '16px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '24px' }}>🖼️</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 700 }}>Image Models</div>
              <div style={{ color: '#757575', lineHeight: 1.5, fontSize: '0.95rem', flex: 1 }}>Compare SDXL, Flux, Ideogram and more side-by-side.</div>
              <div style={{ marginTop: 'auto', fontWeight: 600, fontSize: '0.9rem', color: '#2563EB' }}>Enter Studio →</div>
            </div>
          </Link>

          <Link href="/model/video" style={{ textDecoration: 'none' }}>
            <div style={{ background: 'white', border: '1px solid #E5E5E5', borderRadius: '20px', padding: '2.5rem', color: '#1A1A1A', transition: 'all 0.3s', cursor: 'pointer', minHeight: '250px', display: 'flex', flexDirection: 'column', gap: '1rem' }}
                 onMouseOver={(e) => { e.currentTarget.style.transform = 'translateY(-8px)'; e.currentTarget.style.boxShadow = '0 20px 40px -10px rgba(0,0,0,0.1)'; }}
                 onMouseOut={(e) => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.boxShadow = 'none'; }}>
              <span style={{ position: 'absolute', top: '20px', right: '20px', fontSize: '0.75rem', padding: '4px 8px', background: '#F3F4F6', borderRadius: '6px', fontWeight: 600 }}>Beta</span>
              <div style={{ width: '60px', height: '60px', background: '#F3F4F6', borderRadius: '16px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '24px' }}>🎥</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 700 }}>Video Models</div>
              <div style={{ color: '#757575', lineHeight: 1.5, fontSize: '0.95rem', flex: 1 }}>Generate videos with Runway, Luma, and Kling.</div>
              <div style={{ marginTop: 'auto', fontWeight: 600, fontSize: '0.9rem', color: '#2563EB' }}>Enter Studio →</div>
            </div>
          </Link>

          <Link href="/model/tts" style={{ textDecoration: 'none' }}>
            <div style={{ background: 'white', border: '1px solid #E5E5E5', borderRadius: '20px', padding: '2.5rem', color: '#1A1A1A', transition: 'all 0.3s', cursor: 'pointer', minHeight: '250px', display: 'flex', flexDirection: 'column', gap: '1rem' }}
                 onMouseOver={(e) => { e.currentTarget.style.transform = 'translateY(-8px)'; e.currentTarget.style.boxShadow = '0 20px 40px -10px rgba(0,0,0,0.1)'; }}
                 onMouseOut={(e) => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.boxShadow = 'none'; }}>
              <span style={{ position: 'absolute', top: '20px', right: '20px', fontSize: '0.75rem', padding: '4px 8px', background: '#ECFDF5', color: '#059669', borderRadius: '6px', fontWeight: 600 }}>New</span>
              <div style={{ width: '60px', height: '60px', background: '#F3F4F6', borderRadius: '16px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '24px' }}>🗣️</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 700 }}>Text to Speech</div>
              <div style={{ color: '#757575', lineHeight: 1.5, fontSize: '0.95rem', flex: 1 }}>Convert text to lifelike audio using Minimax, ElevenLabs, and more.</div>
              <div style={{ marginTop: 'auto', fontWeight: 600, fontSize: '0.9rem', color: '#2563EB' }}>Enter Studio →</div>
            </div>
          </Link>

        </div>
      </div>

      <footer style={{ padding: '2rem', textAlign: 'center', color: '#aaa', fontSize: '0.8rem' }}>
        &copy; 2025 x402 Platform.
      </footer>
    </div>
  );
}