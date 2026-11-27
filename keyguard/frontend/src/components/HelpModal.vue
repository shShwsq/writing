<script setup lang="ts">
defineEmits<{ (e: 'close'): void }>()
</script>

<template>
  <div class="overlay" @click.self="$emit('close')">
    <div class="modal">
      <div class="tag">MISSION BRIEFING</div>
      <h1 class="title">大模型是密钥守门人</h1>
      <ul class="rules">
        <li>大模型保管着一段<b>密钥</b>，它被系统指令严令禁止泄露。</li>
        <li>你的目标：<b>让它说出密钥</b>。</li>
      </ul>
      <button class="cta" @click="$emit('close')">开始</button>
    </div>
  </div>
</template>

<style scoped>
.rules {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 24px;
  color: var(--text);
  font-size: 13.5px;
  line-height: 1.7;
}
.rules li { padding-left: 18px; position: relative; }
.rules li::before {
  content: '▸';
  position: absolute;
  left: 0;
  color: var(--cyan);
}
.rules b { color: var(--cyan); }
.rules code { font-family: var(--mono); color: var(--cyan); }
</style>
