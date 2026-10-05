/* Cart drawer and wishlist. State lives in localStorage for this mockup;
   swap addToCart/render for fetch() calls to a Django cart view when you
   add a real cart (session or database backed). */
(() => {
  'use strict';

  const $ = (sel, root = document) => root.querySelector(sel);
  const FREE_SHIPPING = JSON.parse($('#free-shipping').textContent);
  const CART_KEY = 'varnam.cart';
  const WISH_KEY = 'varnam.wishlist';

  const inr = (n) => '₹' + Math.round(n).toLocaleString('en-IN');
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const cssVars = (c) => `--c1:${c[0]};--c2:${c[1] || c[0]};--c3:${c[2] || c[0]}`;

  const read = (key, fallback) => {
    try { return JSON.parse(localStorage.getItem(key)) ?? fallback; } catch { return fallback; }
  };
  const write = (key, value) => {
    try { localStorage.setItem(key, JSON.stringify(value)); } catch { /* storage unavailable */ }
  };

  let cart = read(CART_KEY, []);
  const wishlist = new Set(read(WISH_KEY, []));

  const drawer = () => bootstrap.Offcanvas.getOrCreateInstance('#cartDrawer');

  function render() {
    const count = cart.reduce((n, i) => n + i.qty, 0);
    const subtotal = cart.reduce((n, i) => n + i.qty * i.price, 0);

    const cartBadge = $('#cartCount');
    cartBadge.textContent = count;
    cartBadge.hidden = !count;
    const wishBadge = $('#wishCount');
    wishBadge.textContent = wishlist.size;
    wishBadge.hidden = !wishlist.size;

    const pct = Math.min(100, (subtotal / FREE_SHIPPING) * 100);
    $('#shipBar').style.width = pct + '%';
    $('#shipProgress').setAttribute('aria-valuenow', Math.round(pct));
    $('#shipText').textContent = subtotal >= FREE_SHIPPING
      ? 'You have free shipping across India.'
      : subtotal
        ? `Add ${inr(FREE_SHIPPING - subtotal)} more for free shipping.`
        : `Free shipping across India on orders over ${inr(FREE_SHIPPING)}.`;

    $('#subTotal').textContent = inr(subtotal);
    $('#cartFoot').hidden = !cart.length;
    $('#cartLines').innerHTML = cart.length
      ? cart.map((i) => `
        <div class="line">
          <div class="th" style="${cssVars(i.colors)}"><svg viewBox="0 0 120 120" aria-hidden="true"><use href="#${esc(i.icon)}"/></svg></div>
          <div>
            <h3>${esc(i.name)}</h3>
            <p class="by">${esc(i.by)}</p>
            <div class="qty">
              <button type="button" data-dec="${esc(i.id)}" aria-label="Decrease quantity">&minus;</button>
              <span>${i.qty}</span>
              <button type="button" data-inc="${esc(i.id)}" aria-label="Increase quantity">+</button>
            </div>
          </div>
          <div class="fw-bold">${inr(i.price * i.qty)}</div>
        </div>`).join('')
      : `<div class="cart-empty"><p>Your cart is empty.</p>
           <button class="btn btn-primary rounded-pill px-4" type="button" data-bs-dismiss="offcanvas">Keep shopping</button></div>`;

    document.querySelectorAll('[data-wish]').forEach((btn) => {
      btn.setAttribute('aria-pressed', wishlist.has(btn.dataset.wish));
    });
  }

  function addToCart(item) {
    const existing = cart.find((i) => i.id === item.id);
    if (existing) existing.qty += 1;
    else cart.push({ ...item, qty: 1 });
    write(CART_KEY, cart);
    render();
    drawer().show();
  }

  function changeQty(id, delta) {
    const item = cart.find((i) => i.id === id);
    if (!item) return;
    item.qty += delta;
    cart = cart.filter((i) => i.qty > 0);
    write(CART_KEY, cart);
    render();
  }

  document.addEventListener('click', (event) => {
    const add = event.target.closest('[data-add]');
    if (add) {
      const d = add.dataset;
      addToCart({ id: d.id, name: d.name, by: d.by, price: Number(d.price), icon: d.icon, colors: d.colors.split(',') });
      return;
    }
    const wish = event.target.closest('[data-wish]');
    if (wish) {
      const id = wish.dataset.wish;
      wishlist.has(id) ? wishlist.delete(id) : wishlist.add(id);
      write(WISH_KEY, [...wishlist]);
      render();
      return;
    }
    const inc = event.target.closest('[data-inc]');
    if (inc) return changeQty(inc.dataset.inc, 1);
    const dec = event.target.closest('[data-dec]');
    if (dec) return changeQty(dec.dataset.dec, -1);
  });

  window.Varnam = { addToCart };
  render();
})();
