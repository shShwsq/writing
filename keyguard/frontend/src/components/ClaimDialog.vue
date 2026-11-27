<script setup lang="ts">
import { ref } from 'vue'
import { claimKey } from '../api'

const props = defineProps<{
  claimId: string
  masked: string
  initialKey?: string
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'revealed', claimId: string, key: string): void
}>()

const name = ref('')
const loading = ref(false)
const error = ref('')
const revealedKey = ref(props.initialKey ?? '')
const copied = ref(false)

async function submit() {
  if (loading.value) return
  if (!name.value.trim()) {
    error.value = '留下代号 / 姓名吧'
    return
  }
  loading.value = true
  error.value = ''
  try {
    const res = await claimKey(props.claimId, name.value.trim())
    revealedKey.value = res.key
    emit('revealed', props.claimId, res.key)
  } catch (e) {
    error.value = e instanceof Error ? e.message : '领取失败'
  } finally {
    loading.value = false
  }
}

function legacyCopy(text: string) {
  const ta = document.createElement('textarea')
  ta.value = text
  ta.style.position = 'fixed'
  ta.style.opacity = '0'
  document.body.appendChild(ta)
  ta.select()
  const ok = document.execCommand('copy')
  document.body.removeChild(ta)
  return ok
}

async function copy() {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(revealedKey.value)
    } else if (!legacyCopy(revealedKey.value)) {
      throw new Error('copy failed')
    }
    copied.value = true
    setTimeout(() => (copied.value = false), 1500)
  } catch {
    alert('自动复制失败，请手动选中密钥复制')
  }
}
</script>

<template>
  <div class="overlay">
    <div class="modal">
      <div class="tag">KEY DETECTED</div>
      <template v-if="!revealedKey">
        <h1 class="title">Congratulations!</h1>
        <div class="masked">{{ masked }}</div>
        <input
          v-model="name"
          class="name-input"
          maxlength="50"
          placeholder="你的代号 / 姓名"
          @keydown.enter="submit"
        />
        <div v-if="error" class="err">{{ error }}</div>
        <div class="row">
          <button class="cta" :disabled="loading" @click="submit">
            {{ loading ? '验证中…' : '领取密钥' }}
          </button>
          <button class="ghost" @click="emit('close')">取消</button>
        </div>
      </template>
      <template v-else>
        <h1 class="title">恭喜获得密钥</h1>
        <div class="key-box" title="点击复制" @click="copy">
          {{ revealedKey }}
          <span class="copy-tip">{{ copied ? '已复制 ✓' : '点击复制' }}</span>
        </div>
        <button class="cta" @click="emit('close')">完成</button>
      </template>
    </div>
  </div>
</template>

<style scoped>
.masked {
  font-size: 15px;
  color: var(--cyan);
  letter-spacing: 2px;
  border: 1px dashed var(--cyan);
  border-radius: 999px;
  display: inline-block;
  padding: 4px 16px;
  background: var(--cyan-soft);
  margin-bottom: 14px;
}
.name-input {
  width: 100%;
  background: var(--panel-2);
  border: 1px solid var(--line);
  border-radius: 4px;
  color: var(--text);
  font-size: 14px;
  padding: 10px 12px;
  outline: none;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.name-input:focus { border-color: var(--cyan); box-shadow: 0 0 12px rgba(0, 229, 199, 0.25); }
.err { color: var(--danger); font-size: 12px; margin-top: 8px; }
.row { display: flex; gap: 12px; margin-top: 18px; }
.key-box {
  border: 1px solid var(--cyan);
  border-radius: 6px;
  background: var(--cyan-soft);
  color: var(--cyan);
  font-size: 13px;
  letter-spacing: 1px;
  padding: 14px;
  word-break: break-all;
  cursor: pointer;
  margin-bottom: 14px;
  box-shadow: 0 0 18px rgba(0, 229, 199, 0.2);
}
.copy-tip {
  display: block;
  margin-top: 8px;
  font-size: 11px;
  color: var(--muted);
  letter-spacing: 2px;
}
</style>
