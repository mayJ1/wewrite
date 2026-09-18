(() => {
  const icons = { hotspots: 'flame', styles: 'library', article: 'square-pen', history: 'history' };
  document.querySelectorAll('.nav-button').forEach(button => {
    const text = button.textContent;
    button.innerHTML = `<i data-lucide="${icons[button.dataset.page]}"></i><span>${text}</span>`;
    button.title = text;
  });
  document.querySelector('#newArticleButton').innerHTML = '<i data-lucide="plus"></i><span>新建文章</span>';
  window.lucide?.createIcons();
  const select = document.querySelector('#themeSelect');
  try { select.value = localStorage.getItem('wewrite-theme') || 'system'; } catch {}
  select.addEventListener('change', () => {
    try { localStorage.setItem('wewrite-theme', select.value); } catch {}
    window.applyWeWriteTheme(select.value);
  });
})();
