<script setup lang="ts">
import { computed } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

marked.use({ breaks: true, gfm: true })

const props = defineProps<{
  role: 'user' | 'assistant'
  content: string
  streaming?: boolean
  thinking?: boolean
}>()

const emit = defineEmits<{
  (e: 'claim', payload: { claimId: string; masked: string }): void
}>()

function escapeHtml(s: string) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
}

// 助手消息渲染为 markdown。密钥标记先用占位符占位，解析完成后再替换成按钮：
// 直接注入 HTML 会在代码块/行内代码中被 marked 转义成原文显示
const html = computed(() => {
  let src = props.content
  const chips: { id: string; masked: string }[] = []
  src = src.replace(/⟦key:([0-9a-f]+)⟧([^⟦]*)⟦\/key⟧/g, (_, id: string, masked: string) => {
    chips.push({ id, masked })
    return `@@KG-${chips.length - 1}@@`
  })
  // 流式传输中的半个标记先隐藏，完整后再显示
  // （此时完整标记已替换为不含 ⟦ 的占位符，剩下的 ⟦ 必属残缺标记）
  const open = src.lastIndexOf('⟦')
  if (open !== -1) src = src.slice(0, open)
  let out = DOMPurify.sanitize(marked.parse(src) as string)
  chips.forEach((c, i) => {
    out = out.replaceAll(
      `@@KG-${i}@@`,
      `<button class="key-chip" data-claim="${c.id}" title="点击领取密钥">${escapeHtml(c.masked)}</button>`,
    )
  })
  return out
})

function onClick(e: MouseEvent) {
  const el = (e.target as HTMLElement).closest<HTMLButtonElement>('button.key-chip')
  if (el?.dataset.claim) {
    emit('claim', { claimId: el.dataset.claim, masked: el.textContent ?? '' })
  }
}
</script>

<template>
  <div class="msg" :class="role">
    <div class="avatar">{{ role === 'assistant' ? '⛨' : '▣' }}</div>
    <div class="bubble" :class="{ plain: role === 'user' }">
      <template v-if="content">
        <div
          v-if="role === 'assistant'"
          class="md"
          :class="{ streaming }"
          @click="onClick"
          v-html="html"
        ></div>
        <span v-else class="txt">{{ content }}</span>
      </template>
      <span v-else-if="thinking" class="thinking">
        思考中<span class="dots"><i>·</i><i>·</i><i>·</i></span>
      </span>
    </div>
  </div>
</template>

<style scoped>
.msg { display: flex; gap: 10px; }
.msg.user { flex-direction: row-reverse; }
.avatar {
  width: 30px;
  height: 30px;
  flex: none;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--line);
  border-radius: 4px;
  color: var(--cyan);
  font-size: 14px;
  background: var(--panel);
}
.msg.user .avatar { color: var(--text); }
.bubble {
  max-width: 78%;
  padding: 10px 14px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: var(--panel);
  line-height: 1.65;
  word-break: break-word;
  font-size: 13.5px;
}
.bubble.plain { white-space: pre-wrap; }
.msg.assistant .bubble {
  border-left: 2px solid var(--cyan);
  box-shadow: 0 0 18px rgba(0, 229, 199, 0.06);
}
.msg.user .bubble { background: var(--panel-2); }

/* ===== markdown 内容 ===== */
.md > :first-child { margin-top: 0; }
.md > :last-child { margin-bottom: 0; }
.md :deep(p) { margin: 0.5em 0; }
.md :deep(h1), .md :deep(h2), .md :deep(h3), .md :deep(h4) {
  margin: 0.8em 0 0.4em;
  color: #e6fff9;
  line-height: 1.4;
}
.md :deep(h1) { font-size: 1.25em; }
.md :deep(h2) { font-size: 1.15em; }
.md :deep(h3), .md :deep(h4) { font-size: 1.05em; }
.md :deep(ul), .md :deep(ol) { margin: 0.5em 0; padding-left: 1.5em; }
.md :deep(li) { margin: 0.2em 0; }
.md :deep(code) {
  padding: 0.1em 0.4em;
  border-radius: 4px;
  background: rgba(0, 229, 199, 0.08);
  border: 1px solid rgba(0, 229, 199, 0.15);
  color: var(--cyan);
  font-family: var(--mono);
  font-size: 0.92em;
}
.md :deep(pre) {
  margin: 0.6em 0;
  padding: 10px 12px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: #060b14;
  overflow-x: auto;
}
.md :deep(pre code) {
  padding: 0;
  border: none;
  background: transparent;
  color: var(--text);
}
.md :deep(blockquote) {
  margin: 0.6em 0;
  padding: 2px 12px;
  border-left: 2px solid var(--muted);
  color: var(--muted);
}
.md :deep(a) { color: var(--cyan); text-decoration-color: rgba(0, 229, 199, 0.4); }
.md :deep(hr) { border: none; border-top: 1px dashed var(--line); margin: 0.8em 0; }
.md :deep(table) { border-collapse: collapse; margin: 0.6em 0; }
.md :deep(th), .md :deep(td) {
  border: 1px solid var(--line);
  padding: 4px 10px;
}
.md :deep(th) { background: var(--panel-2); color: #e6fff9; }

/* 流式光标跟在最后一个块末尾 */
.md.streaming > :last-child::after {
  content: '▌';
  color: var(--cyan);
  animation: blink 1s steps(1) infinite;
}

/* v-html 注入的内容没有 scoped 属性，需用 :deep() 穿透 */
.md :deep(.key-chip) {
  display: inline-block;
  margin: 0 2px;
  padding: 1px 8px;
  border: 1px dashed var(--cyan);
  border-radius: 999px;
  background: var(--cyan-soft);
  color: var(--cyan);
  font-family: var(--mono);
  font-size: 13px;
  letter-spacing: 1px;
  animation: chipGlow 1.6s infinite;
}
.thinking { color: var(--muted); }
.dots i {
  font-style: normal;
  margin-left: 2px;
  animation: dotFade 1.2s infinite;
}
.dots i:nth-child(2) { animation-delay: 0.2s; }
.dots i:nth-child(3) { animation-delay: 0.4s; }

@media (prefers-reduced-motion: reduce) {
  .md :deep(.key-chip), .dots i, .md.streaming > :last-child::after { animation: none; }
}
</style>
