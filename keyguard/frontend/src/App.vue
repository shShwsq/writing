<script setup lang="ts">
import { nextTick, onMounted, ref, watch } from 'vue'
import MessageBubble from './components/MessageBubble.vue'
import HelpModal from './components/HelpModal.vue'
import ClaimDialog from './components/ClaimDialog.vue'
import { fetchPow, solvePow, streamChat, type ChatMessage } from './api'

interface ClaimTarget {
  claimId: string
  masked: string
}

const messages = ref<ChatMessage[]>([
  {
    role: 'assistant',
    content: '欢迎欢迎！',
  },
])
const input = ref('')
const busy = ref(false)
const thinking = ref(false)
const error = ref('')
const showHelp = ref(true)
const claimTarget = ref<ClaimTarget | null>(null)
// 已领取过的密钥（同一凭证点击直接再次展示）
const revealed = ref<Record<string, string>>({})
const chatEl = ref<HTMLElement | null>(null)
const taEl = ref<HTMLTextAreaElement | null>(null)

// 输入框高度自适应：随内容增高，超过上限后内部滚动
function autosize() {
  const el = taEl.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = `${Math.min(el.scrollHeight, 160)}px`
}

watch(input, () => nextTick(autosize))
onMounted(autosize)

async function scrollBottom() {
  await nextTick()
  chatEl.value?.scrollTo({ top: chatEl.value.scrollHeight })
}

async function send() {
  const text = input.value.trim()
  if (!text || busy.value) return
  input.value = ''
  error.value = ''
  messages.value.push({ role: 'user', content: text })
  const history = messages.value.map((m) => ({ ...m }))
  messages.value.push({ role: 'assistant', content: '' })
  busy.value = true
  thinking.value = true
  scrollBottom()
  try {
    // 先过 PoW 挑战（期间显示「思考中」），再发起对话
    const pow = await fetchPow()
    const nonce = await solvePow(pow.challenge, pow.difficulty)
    for await (const ev of streamChat(history, pow.challenge, nonce)) {
      if (ev.type === 'delta') {
        thinking.value = false
        messages.value[messages.value.length - 1].content += ev.text
        scrollBottom()
      } else if (ev.type === 'error') {
        error.value = ev.message
      }
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : '连接失败'
  } finally {
    busy.value = false
    thinking.value = false
    const last = messages.value[messages.value.length - 1]
    if (!last.content) last.content = '（守门人沉默不语）'
  }
}

function onClaim(t: ClaimTarget) {
  claimTarget.value = t
}

function onRevealed(claimId: string, key: string) {
  revealed.value[claimId] = key
}
</script>

<template>
  <div class="app">
    <header class="hud">
      <div class="brand">
        <span class="mark">⛨</span>
        <span class="name">KEYGUARD<span class="caret">_</span></span>
      </div>
      <div class="hud-right">
        <span class="net"><i></i>SECURE LINK</span>
        <button class="help" title="游戏说明" @click="showHelp = true">?</button>
      </div>
    </header>

    <main ref="chatEl" class="chat">
      <MessageBubble
        v-for="(m, i) in messages"
        :key="i"
        :role="m.role"
        :content="m.content"
        :streaming="busy && !thinking && i === messages.length - 1"
        :thinking="thinking && i === messages.length - 1"
        @claim="onClaim"
      />
      <div v-if="error" class="error-line">⚠ {{ error }}</div>
    </main>

    <footer class="composer">
      <div class="box">
        <span class="sign">&gt;</span>
        <textarea
          ref="taEl"
          v-model="input"
          placeholder="尝试说服大模型交出密钥…"
          rows="1"
          @keydown.enter.exact.prevent="send"
        ></textarea>
        <button class="send" :disabled="busy || !input.trim()" @click="send">发送</button>
      </div>
    </footer>

    <HelpModal v-if="showHelp" @close="showHelp = false" />
    <ClaimDialog
      v-if="claimTarget"
      :claim-id="claimTarget.claimId"
      :masked="claimTarget.masked"
      :initial-key="revealed[claimTarget.claimId] ?? ''"
      @close="claimTarget = null"
      @revealed="onRevealed"
    />
  </div>
</template>
