<template>
  <div class="result-card" :class="{ 'expanded': isExpanded }">
    <div class="result-card-header" @click="isExpanded = !isExpanded">
      <div class="rank-badge" :class="{ high: rank <= 2, medium: rank <= 4 }">
        #{{ rank }}
      </div>
      <div class="card-info">
        <div class="card-title">{{ title }}</div>
        <div class="card-subtitle">{{ subtitle }}</div>
        <div v-if="tags && tags.length" class="card-tags">
          <span v-for="tag in tags" :key="tag" class="tag-badge" @click.stop="$emit('tag-click', tag)">
            #{{ tag }}
          </span>
        </div>
      </div>
      <div class="score-badge">{{ score.toFixed(2) }}</div>
      <i class="pi pi-chevron-down expand-icon" :class="{ open: isExpanded }"></i>
    </div>
    <div v-show="isExpanded" class="result-card-body">
      <slot></slot>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  rank: Number,
  score: Number,
  title: String,
  subtitle: String,
  tags: { type: Array, default: () => [] },
})

defineEmits(['tag-click'])

const isExpanded = ref(false)
</script>
