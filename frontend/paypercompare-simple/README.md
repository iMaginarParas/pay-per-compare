# Pay Per Compare x402 - Simple Version

Minimal 5-file Next.js app for Web3-powered AI generation.

## Structure

```
├── app/
│   ├── page.tsx              # Landing + navigation (1)
│   └── model/
│       ├── image/page.tsx    # Image generation (2)
│       ├── video/page.tsx    # Video generation (3)
│       └── tts/page.tsx      # TTS generation (4)
└── lib/
    └── web3.tsx              # Web3 + API utils (5)
```

## Quick Start

```bash
npm install
cp .env.example .env.local
npm run dev
```

Open http://localhost:3000

## What's Included

✅ Landing page with workspace selection
✅ Image generation (12 models max)
✅ Video generation (4 models max, image upload)
✅ Text-to-Speech (5 models max)
✅ MetaMask wallet connection
✅ USDC payments on Avalanche Testnet
✅ All Web3 logic in one file

## Tech

- Next.js 14 App Router
- TypeScript
- Ethers.js v6
- Inline styling (no Tailwind)

## API Setup

Set `NEXT_PUBLIC_API_BASE` in `.env.local` to your backend URL.

Expected endpoints:
- `GET /` - Config
- `GET /models` - Image models
- `GET /video-models` - Video models
- `GET /tts-models` - TTS models
- `POST /generate` - Generate images
- `POST /generate-video` - Generate videos
- `POST /generate-tts` - Generate audio

## Build

```bash
npm run build
npm start
```