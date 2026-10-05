/* Home page behavior: hero panels and the custom frame builder. */
(() => {
  'use strict';

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
  const inr = (n) => '₹' + Math.round(n).toLocaleString('en-IN');

  /* Hero panels: hover, focus or tap a panel (or hover a headline phrase) to expand it. */
  const panels = $$('.panel');
  const setActive = (index) => panels.forEach((p, i) => p.classList.toggle('is-active', i === index));
  panels.forEach((panel, i) => {
    panel.addEventListener('mouseenter', () => setActive(i));
    panel.addEventListener('focusin', () => setActive(i));
    panel.addEventListener('click', () => setActive(i));
  });
  $$('.hero-title span').forEach((span) => {
    span.addEventListener('mouseenter', () => setActive(Number(span.dataset.panel)));
  });

  /* Frame builder: options and prices come from FRAME_BUILDER in store/data.py. */
  const cfg = JSON.parse($('#frame-builder').textContent);
  const pick = (list, key) => list.find((x) => x.key === key);
  const chosen = (name) => $(`input[name="${name}"]:checked`).value;
  let current = null;

  function draw() {
    const size = pick(cfg.sizes, chosen('size'));
    const frame = pick(cfg.frames, chosen('frame'));
    const width = pick(cfg.widths, chosen('width'));
    const mat = pick(cfg.mats, chosen('mat'));
    const glazing = pick(cfg.glazing, chosen('glazing'));

    // Fit the artwork's aspect ratio into the preview, scaled a little by size.
    const fit = Math.min(300 / size.w, 340 / size.h) * size.k;
    const ow = size.w * fit;
    const oh = size.h * fit;
    const cx = 200;
    const cy = 212;
    const x = cx - ow / 2;
    const y = cy - oh / 2;
    const border = 16;
    const m = width.px * (ow / 300);
    const ax = x + border + m;
    const ay = y + border + m;
    const aw = ow - 2 * (border + m);
    const ah = oh - 2 * (border + m);

    $('#pv').innerHTML = `
      <g filter="url(#drop)"><rect x="${x}" y="${y}" width="${ow}" height="${oh}" fill="${frame.color}"/></g>
      <rect x="${x}" y="${y}" width="${ow}" height="${oh}" fill="none" stroke="#000" stroke-opacity=".18"/>
      <rect x="${x + 3}" y="${y + 3}" width="${ow - 6}" height="${oh - 6}" fill="none" stroke="#000" stroke-opacity=".16"/>
      <rect x="${x + border}" y="${y + border}" width="${ow - 2 * border}" height="${oh - 2 * border}" fill="${mat.color}"/>
      <svg x="${ax}" y="${ay}" width="${aw}" height="${ah}" viewBox="0 0 100 100" preserveAspectRatio="xMidYMid slice">
        <rect width="100" height="100" fill="#2A3BD0"/><circle cx="68" cy="34" r="17" fill="#E8B02E"/>
        <path d="M0 74C18 52 36 48 52 60s30 6 48-10v60H0z" fill="#0F7B63"/>
        <path d="M0 88c20-12 40-10 58 0s28 4 42-4v26H0z" fill="#0A5A49"/>
      </svg>
      <rect x="${ax}" y="${ay}" width="${aw}" height="${ah}" fill="none" stroke="#000" stroke-opacity="${m ? '.22' : '0'}"/>
      <polygon points="${ax},${ay} ${ax + aw * 0.52},${ay} ${ax},${ay + ah * 0.34}" fill="#fff" opacity="${glazing.add ? '.2' : '.11'}"/>`;

    $('#matSet').hidden = width.px === 0;

    const price = Math.round((size.base * frame.mult + width.add + glazing.add) / 10) * 10;
    const parts = [
      size.label,
      `${frame.label.toLowerCase()} frame`,
      width.px ? `${width.label.toLowerCase()} mat in ${mat.label.toLowerCase()}` : 'no mat',
      glazing.label.toLowerCase(),
    ];
    $('#framePrice').textContent = inr(price);
    $('#frameSummary').textContent = parts.join(', ');
    $('#lbSize').textContent = size.label;
    $('#lbFrame').textContent = frame.label;
    $('#lbWidth').textContent = width.label;
    $('#lbMat').textContent = mat.label;
    $('#lbGlazing').textContent = glazing.label;

    current = {
      id: ['frame', size.key, frame.key, width.key, width.px ? mat.key : '-', glazing.key].join('-'),
      name: `Custom frame, ${parts.join(', ')}`,
      by: 'Custom framing',
      price,
      icon: 'a-frame',
      colors: [frame.color, '#2A3BD0', '#0F7B63'],
    };
  }

  $('#cfg').addEventListener('change', draw);
  $('#frameAdd').addEventListener('click', () => window.Varnam.addToCart(current));
  draw();
})();
