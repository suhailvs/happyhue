/* Wishlist (the cart lives in cart.js, backed by the Django session). */
(() => {
  'use strict';

  const $ = (sel, root = document) => root.querySelector(sel);
  const WISH_KEY = 'varnam.wishlist';

  const read = (key, fallback) => {
    try { return JSON.parse(localStorage.getItem(key)) ?? fallback; } catch { return fallback; }
  };
  const write = (key, value) => {
    try { localStorage.setItem(key, JSON.stringify(value)); } catch { /* storage unavailable */ }
  };

  const wishlist = new Set(read(WISH_KEY, []));

  function render() {
    const wishBadge = $('#wishCount');
    if (wishBadge) {
      wishBadge.textContent = wishlist.size;
      wishBadge.hidden = !wishlist.size;
    }

    document.querySelectorAll('[data-wish]').forEach((btn) => {
      btn.setAttribute('aria-pressed', wishlist.has(btn.dataset.wish));
    });
  }

  document.addEventListener('click', (event) => {
    const wish = event.target.closest('[data-wish]');
    if (wish) {
      const id = wish.dataset.wish;
      wishlist.has(id) ? wishlist.delete(id) : wishlist.add(id);
      write(WISH_KEY, [...wishlist]);
      render();
    }
  });

  render();
})();
