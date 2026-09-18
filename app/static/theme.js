(() => {
  const media = matchMedia('(prefers-color-scheme: dark)');
  const read = () => { try { return localStorage.getItem('wewrite-theme') || 'system'; } catch { return 'system'; } };
  window.applyWeWriteTheme = (mode = read()) => {
    document.documentElement.dataset.theme = mode === 'system' ? (media.matches ? 'dark' : 'light') : mode;
    document.documentElement.style.colorScheme = document.documentElement.dataset.theme;
  };
  applyWeWriteTheme();
  media.addEventListener('change', () => applyWeWriteTheme());
  addEventListener('storage', () => applyWeWriteTheme());
})();
