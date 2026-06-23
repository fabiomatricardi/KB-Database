<template>
  <aside class="sidebar">
    <div class="sidebar-header">
      <h1>ArticleDatabase</h1>
      <p>BM25 Search &amp; Scan</p>
    </div>

    <div
      v-for="item in navItems"
      :key="item.id"
      class="nav-item"
      :class="{ active: activeView === item.id }"
      @click="$emit('navigate', item.id)"
    >
      <i :class="item.icon"></i>
      <span>{{ item.label }}</span>
    </div>

    <div class="sidebar-footer">
      <span class="version">v0.3.2</span>
    </div>
  </aside>
</template>

<script setup>
defineProps({
  activeView: String,
})

defineEmits(['navigate'])

const navItems = [
  { id: 'search', label: 'Search', icon: 'pi pi-search' },
  { id: 'deepsearch', label: 'Deep Search', icon: 'pi pi-directions' },
  { id: 'chat', label: 'Chat', icon: 'pi pi-comments' },
  { id: 'scan', label: 'Scan & Extract', icon: 'pi pi-cloud-download' },
  { id: 'graph', label: 'Knowledge Graph', icon: 'pi pi-chart' },
  { id: 'settings', label: 'Settings', icon: 'pi pi-cog' },
]
</script>
