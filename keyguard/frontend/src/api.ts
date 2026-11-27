export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface PowChallenge {
  challenge: string
  difficulty: number
}

/* ---------- 同步 SHA-256（PoW 挖矿循环用，Web Crypto 单次开销太大） ---------- */

const K = [
  0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
  0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
  0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
  0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
  0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
  0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
  0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
  0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
]

export function sha256hex(msg: string): string {
  const bytes = new TextEncoder().encode(msg)
  const l = bytes.length
  const bitLen = l * 8
  const total = (((l + 1 + 8 + 63) >> 6) << 6) || 64
  const buf = new Uint8Array(total)
  buf.set(bytes)
  buf[l] = 0x80
  const dv = new DataView(buf.buffer)
  dv.setUint32(total - 8, Math.floor(bitLen / 0x100000000))
  dv.setUint32(total - 4, bitLen >>> 0)
  let h0 = 0x6a09e667, h1 = 0xbb67ae85, h2 = 0x3c6ef372, h3 = 0xa54ff53a
  let h4 = 0x510e527f, h5 = 0x9b05688c, h6 = 0x1f83d9ab, h7 = 0x5be0cd19
  const w = new Uint32Array(64)
  for (let off = 0; off < total; off += 64) {
    for (let i = 0; i < 16; i++) w[i] = dv.getUint32(off + i * 4)
    for (let i = 16; i < 64; i++) {
      const x = w[i - 15], y = w[i - 2]
      const s0 = ((x >>> 7) | (x << 25)) ^ ((x >>> 18) | (x << 14)) ^ (x >>> 3)
      const s1 = ((y >>> 17) | (y << 15)) ^ ((y >>> 19) | (y << 13)) ^ (y >>> 10)
      w[i] = (w[i - 16] + s0 + w[i - 7] + s1) >>> 0
    }
    let a = h0, b = h1, c = h2, d = h3, e = h4, f = h5, g = h6, h = h7
    for (let i = 0; i < 64; i++) {
      const S1 = ((e >>> 6) | (e << 26)) ^ ((e >>> 11) | (e << 21)) ^ ((e >>> 25) | (e << 7))
      const ch = (e & f) ^ (~e & g)
      const t1 = (h + S1 + ch + K[i] + w[i]) >>> 0
      const S0 = ((a >>> 2) | (a << 30)) ^ ((a >>> 13) | (a << 19)) ^ ((a >>> 22) | (a << 10))
      const mj = (a & b) ^ (a & c) ^ (b & c)
      const t2 = (S0 + mj) >>> 0
      h = g; g = f; f = e; e = (d + t1) >>> 0; d = c; c = b; b = a; a = (t1 + t2) >>> 0
    }
    h0 = (h0 + a) >>> 0; h1 = (h1 + b) >>> 0; h2 = (h2 + c) >>> 0; h3 = (h3 + d) >>> 0
    h4 = (h4 + e) >>> 0; h5 = (h5 + f) >>> 0; h6 = (h6 + g) >>> 0; h7 = (h7 + h) >>> 0
  }
  return [h0, h1, h2, h3, h4, h5, h6, h7].map((x) => x.toString(16).padStart(8, '0')).join('')
}

/* ---------- PoW：取题 + 解题 ---------- */

export async function fetchPow(): Promise<PowChallenge> {
  const resp = await fetch('/api/pow')
  if (!resp.ok) throw new Error('获取挑战失败')
  return resp.json()
}

export async function solvePow(challenge: string, difficulty: number): Promise<string> {
  const prefix = '0'.repeat(difficulty)
  for (let nonce = 0; ; nonce++) {
    if (sha256hex(challenge + nonce).startsWith(prefix)) return String(nonce)
    // 周期性让出主线程，保持页面响应
    if (nonce % 2048 === 2047) await new Promise((r) => setTimeout(r))
  }
}

export type StreamEvent =
  | { type: 'delta'; text: string }
  | { type: 'done' }
  | { type: 'error'; message: string }

export async function* streamChat(
  messages: ChatMessage[],
  powChallenge: string,
  powNonce: string,
): AsyncGenerator<StreamEvent> {
  const resp = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages, pow_challenge: powChallenge, pow_nonce: powNonce }),
  })
  if (!resp.ok) {
    let msg = `请求失败 (${resp.status})`
    try {
      const data = await resp.json()
      if (typeof data.detail === 'string') msg = data.detail
    } catch {
      /* 忽略解析失败 */
    }
    throw new Error(msg)
  }
  if (!resp.body) throw new Error('浏览器不支持流式响应')

  const reader = resp.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    let idx: number
    while ((idx = buffer.indexOf('\n')) !== -1) {
      const line = buffer.slice(0, idx).trim()
      buffer = buffer.slice(idx + 1)
      if (!line.startsWith('data:')) continue
      let ev: StreamEvent
      try {
        ev = JSON.parse(line.slice(5))
      } catch {
        continue
      }
      if (ev && typeof ev === 'object' && 'type' in ev) yield ev
    }
  }
}

export async function claimKey(claimId: string, name: string): Promise<{ key: string }> {
  const resp = await fetch('/api/claim', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ claim_id: claimId, name }),
  })
  const data: any = await resp.json().catch(() => ({}))
  if (!resp.ok) {
    throw new Error(typeof data?.detail === 'string' ? data.detail : `领取失败 (${resp.status})`)
  }
  return { key: String(data.key) }
}
