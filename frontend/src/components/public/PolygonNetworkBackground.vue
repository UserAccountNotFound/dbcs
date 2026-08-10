<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue';

const props = defineProps<{
  active: boolean;
}>();

const canvasRef = ref<HTMLCanvasElement | null>(null);

type Particle = {
  x: number;
  y: number;
  vx: number;
  vy: number;
  r: number;
};

let particles: Particle[] = [];
let raf = 0;
let width = 0;
let height = 0;
let reducedMotion = false;
let resizeObserver: ResizeObserver | null = null;

const LINK_DIST = 140;
const PARTICLE_COUNT_DESKTOP = 70;
const PARTICLE_COUNT_MOBILE = 40;

function countForSize(w: number, h: number): number {
  const area = w * h;
  if (area < 500_000) return PARTICLE_COUNT_MOBILE;
  return PARTICLE_COUNT_DESKTOP;
}

function initParticles(w: number, h: number) {
  const n = countForSize(w, h);
  particles = Array.from({ length: n }, () => {
    const speed = reducedMotion ? 0 : 0.15 + Math.random() * 0.35;
    const angle = Math.random() * Math.PI * 2;
    return {
      x: Math.random() * w,
      y: Math.random() * h,
      vx: Math.cos(angle) * speed,
      vy: Math.sin(angle) * speed,
      r: 1 + Math.random() * 1.8,
    };
  });
}

function draw(ctx: CanvasRenderingContext2D) {
  ctx.clearRect(0, 0, width, height);

  // Точки-звёзды на фоне
  for (const p of particles) {
    ctx.beginPath();
    ctx.fillStyle = 'rgba(255, 255, 255, 0.85)';
    ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
    ctx.fill();
  }

  // Связи между близкими точками
  for (let i = 0; i < particles.length; i++) {
    for (let j = i + 1; j < particles.length; j++) {
      const a = particles[i];
      const b = particles[j];
      const dx = a.x - b.x;
      const dy = a.y - b.y;
      const dist = Math.hypot(dx, dy);
      if (dist > LINK_DIST) continue;
      const alpha = (1 - dist / LINK_DIST) * 0.45;
      ctx.strokeStyle = `rgba(255, 255, 255, ${alpha})`;
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(a.x, a.y);
      ctx.lineTo(b.x, b.y);
      ctx.stroke();
    }
  }
}

function step(ctx: CanvasRenderingContext2D) {
  if (!reducedMotion) {
    for (const p of particles) {
      p.x += p.vx;
      p.y += p.vy;
      if (p.x < 0 || p.x > width) p.vx *= -1;
      if (p.y < 0 || p.y > height) p.vy *= -1;
      p.x = Math.min(width, Math.max(0, p.x));
      p.y = Math.min(height, Math.max(0, p.y));
    }
  }
  draw(ctx);
  raf = requestAnimationFrame(() => step(ctx));
}

function resizeToParent() {
  const canvas = canvasRef.value;
  if (!canvas) return;
  const parent = canvas.parentElement;
  if (!parent) return;

  const rect = parent.getBoundingClientRect();
  width = Math.max(1, Math.floor(rect.width));
  height = Math.max(1, Math.floor(rect.height));
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  canvas.width = Math.floor(width * dpr);
  canvas.height = Math.floor(height * dpr);
  canvas.style.width = `${width}px`;
  canvas.style.height = `${height}px`;

  const ctx = canvas.getContext('2d');
  if (!ctx) return;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  initParticles(width, height);
  draw(ctx);
}

function start() {
  stop();
  const canvas = canvasRef.value;
  if (!canvas || !props.active) return;
  reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  resizeToParent();
  const ctx = canvas.getContext('2d');
  if (!ctx) return;
  raf = requestAnimationFrame(() => step(ctx));

  const parent = canvas.parentElement;
  if (parent && typeof ResizeObserver !== 'undefined') {
    resizeObserver = new ResizeObserver(() => resizeToParent());
    resizeObserver.observe(parent);
  }
}

function stop() {
  if (raf) {
    cancelAnimationFrame(raf);
    raf = 0;
  }
  if (resizeObserver) {
    resizeObserver.disconnect();
    resizeObserver = null;
  }
}

onMounted(() => {
  if (props.active) start();
});

onUnmounted(() => {
  stop();
});

watch(
  () => props.active,
  (active) => {
    if (active) start();
    else stop();
  },
);
</script>

<template>
  <canvas
    v-show="active"
    ref="canvasRef"
    class="polygon-network"
    aria-hidden="true"
  />
</template>

<style scoped>
.polygon-network {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  display: block;
  pointer-events: none;
}
</style>
