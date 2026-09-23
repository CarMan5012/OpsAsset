<template>
  <span class="brand-logo-wrapper" aria-hidden="true">
    <svg width="100%" height="100%" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect width="48" height="48" rx="11" fill="#2563EB" />
      <rect x="10" y="12" width="28" height="10" rx="2.5" stroke="white" stroke-width="2.5" />
      <circle cx="15" cy="17" r="1.5" fill="white" />
      <rect x="10" y="26" width="28" height="10" rx="2.5" stroke="white" stroke-width="2.5" />
      <circle cx="15" cy="31" r="1.5" fill="white" />
    </svg>
  </span>
</template>

<style scoped>
.brand-logo-wrapper {
  display: inline-flex;
  width: 36px;
  height: 36px;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
@media (max-width: 1023px) {
  .brand-logo-wrapper {
    width: 32px;
    height: 32px;
  }
}
</style>
