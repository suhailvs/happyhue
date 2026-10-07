// Server-backed cart. Fills the #cartDrawer markup in base.html and handles every [data-add] button.
// Load this INSTEAD of the cart code in site.js (keep the wishlist and other parts of site.js).
(() => {
  const $ = (id) => document.getElementById(id);
  const drawer = $('cartDrawer');
  if (!drawer) return;
  const URLS = {
    cart: drawer.dataset.urlCart, add: drawer.dataset.urlAdd,
    update: drawer.dataset.urlUpdate, remove: drawer.dataset.urlRemove,
  };
  const inr = (v) => '₹' + Number(v).toLocaleString('en-IN', { maximumFractionDigits: 0 });
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const csrf = () => (document.cookie.match(/(?:^|; )csrftoken=([^;]+)/) || [])[1] || '';

  async function call(url, body) {
    const res = await fetch(url, {
      method: body ? 'POST' : 'GET',
      headers: body ? { 'Content-Type': 'application/json', 'X-CSRFToken': csrf() } : {},
      body: body ? JSON.stringify(body) : undefined,
      credentials: 'same-origin',
    });
    const data = await res.json();
    render(data);
    return data;
  }

  function render(cart) {
    const badge = $('cartCount');
    if (badge) { badge.textContent = cart.count; badge.hidden = !cart.count; }

    const pct = cart.threshold ? Math.min(100, (cart.subtotal / cart.threshold) * 100) : 0;
    $('shipText').textContent = !cart.count ? `Free shipping on orders over ${inr(cart.threshold)}`
      : cart.remaining > 0 ? `Add ${inr(cart.remaining)} more for free shipping` : 'You have unlocked free shipping';
    $('shipBar').style.width = pct + '%';
    $('shipProgress').setAttribute('aria-valuenow', Math.round(pct));

    const box = $('cartLines');
    if (!cart.count) {
      box.innerHTML = '<p class="text-body-secondary py-5 text-center mb-0">Your cart is empty.</p>';
    } else {
      box.innerHTML = cart.lines.map((l) => `
        <div class="d-flex gap-3 py-3 border-bottom" data-key="${esc(l.key)}">
          ${l.image
            ? `<img src="${esc(l.image)}" alt="" width="64" height="64" style="object-fit:cover;border-radius:8px;flex:none">`
            : `<svg viewBox="0 0 120 120" width="64" height="64" aria-hidden="true"
               style="--c1:${esc(l.colors[0] || '#999')};--c2:${esc(l.colors[1] || '#999')};--c3:${esc(l.colors[2] || '#999')}"><use href="#${esc(l.icon)}"/></svg>`}
          <div class="flex-grow-1">
            <div class="fw-semibold">${esc(l.name)}</div>
            <div class="small text-body-secondary">${esc(l.by)}</div>
            <div class="d-flex align-items-center gap-2 mt-2">
              <button class="btn btn-sm btn-outline-secondary" data-step="-1" aria-label="Decrease quantity">−</button>
              <span aria-live="polite">${l.qty}</span>
              <button class="btn btn-sm btn-outline-secondary" data-step="1" aria-label="Increase quantity"${l.qty >= l.max_qty ? ' disabled' : ''}>+</button>
              <button class="btn btn-link btn-sm ms-2 p-0" data-remove>Remove</button>
            </div>
          </div>
          <div class="fw-semibold">${inr(l.line_total)}</div>
        </div>`).join('');
    }
    $('cartFoot').hidden = !cart.count;
    $('subTotal').textContent = inr(cart.subtotal);
  }

  document.addEventListener('click', async (e) => {
    const add = e.target.closest('[data-add]');
    if (add) {
      add.disabled = true;
      await call(URLS.add, { product_id: add.dataset.id, qty: 1 });
      add.disabled = false;
      bootstrap.Offcanvas.getOrCreateInstance($('cartDrawer')).show();
      return;
    }
    const row = e.target.closest('[data-key]');
    if (!row || !row.closest('#cartLines')) return;
    const key = row.dataset.key;
    if (e.target.closest('[data-remove]')) return void call(URLS.remove, { key });
    const step = e.target.closest('[data-step]');
    if (step) {
      const qty = Number(row.querySelector('[aria-live]').textContent) + Number(step.dataset.step);
      call(URLS.update, { key, qty });
    }
  });

  // For the frame builder: window.HHCart.addFraming({size, frame, mat, width, glazing})
  window.HHCart = {
    async addFraming(options) {
      const data = await call(URLS.add, { framing: options, qty: 1 });
      bootstrap.Offcanvas.getOrCreateInstance($('cartDrawer')).show();
      return data;
    },
  };

  call(URLS.cart);
})();
