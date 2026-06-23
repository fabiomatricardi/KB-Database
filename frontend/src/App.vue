<template>
  <div class="layout">
    <Sidebar :activeView="activeView" @navigate="activeView = $event" />
    <main class="main-content">
      <SearchView v-if="activeView === 'search'" />
      <DeepSearchView v-if="activeView === 'deepsearch'" />
      <ChatView v-if="activeView === 'chat'" />
      <ScanView v-if="activeView === 'scan'" />
      <GraphView v-if="activeView === 'graph'" />
      <SettingsPanel v-if="activeView === 'settings'" />
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import Sidebar from './components/Sidebar.vue'
import SearchView from './components/SearchView.vue'
import DeepSearchView from './components/DeepSearchView.vue'
import ChatView from './components/ChatView.vue'
import ScanView from './components/ScanView.vue'
import GraphView from './components/GraphView.vue'
import SettingsPanel from './components/SettingsPanel.vue'

const activeView = ref('search')
</script>
