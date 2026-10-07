// Checkout: create order on the server, open Razorpay, verify the signature on success.
(() => {
  const form = document.getElementById('checkoutForm');
  if (!form) return;
  const btn = document.getElementById('payBtn');
  const alertBox = document.getElementById('formAlert');
  const csrf = form.querySelector('[name=csrfmiddlewaretoken]').value;
  const label = btn.textContent.trim();

  const busy = (on, text) => { btn.disabled = on; btn.textContent = on ? text : label; };
  const showAlert = (msg) => { alertBox.textContent = msg; alertBox.hidden = !msg; };

  function showErrors(errors) {
    form.querySelectorAll('.is-invalid').forEach((el) => el.classList.remove('is-invalid'));
    form.querySelectorAll('[data-error-for]').forEach((el) => { el.textContent = ''; });
    let first = null;
    Object.entries(errors || {}).forEach(([name, list]) => {
      const input = form.elements[name];
      const slot = form.querySelector(`[data-error-for="${name}"]`);
      if (input) { input.classList.add('is-invalid'); first = first || input; }
      if (slot) slot.textContent = list.map((e) => e.message).join(' ');
    });
    if (first) first.focus();
  }

  async function post(url, body) {
    const res = await fetch(url, {
      method: 'POST', body, credentials: 'same-origin', headers: { 'X-CSRFToken': csrf },
    });
    return { res, data: await res.json().catch(() => ({})) };
  }

  function report(rpOrderId, reason) {
    const body = new FormData();
    body.set('razorpay_order_id', rpOrderId);
    body.set('reason', reason);
    return post(form.dataset.failedUrl, body).catch(() => {});
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    showAlert('');
    showErrors({});
    busy(true, 'Starting payment…');

    let result;
    try {
      result = await post(form.action, new FormData(form));
    } catch (err) {
      busy(false); return showAlert('Network error. Please try again.');
    }
    const { res, data } = result;
    if (res.status === 401 && data.login_url) { location.href = data.login_url; return; }
    if (!res.ok || !data.ok) {
      busy(false);
      if (data.errors) showErrors(data.errors);
      return showAlert(data.message || 'Please check the highlighted fields.');
    }

    const rzp = new Razorpay({
      key: data.key,
      amount: data.amount,
      currency: data.currency,
      name: data.name,
      description: data.description,
      order_id: data.razorpay_order_id,
      prefill: data.prefill,
      theme: { color: '#2A3BD0' },
      handler: async (resp) => {
        busy(true, 'Confirming payment…');
        const body = new FormData();
        body.set('razorpay_order_id', resp.razorpay_order_id);
        body.set('razorpay_payment_id', resp.razorpay_payment_id);
        body.set('razorpay_signature', resp.razorpay_signature);
        try {
          const v = await post(form.dataset.verifyUrl, body);
          if (v.data.ok) { location.href = v.data.redirect; return; }
          busy(false); showAlert(v.data.message || 'Payment could not be verified.');
        } catch (err) {
          // Payment went through; the webhook will confirm it. Send them to the order page.
          location.href = form.dataset.orderUrl.replace('ORDER_NUMBER', data.order_number);
        }
      },
      modal: {
        ondismiss: () => { busy(false); report(data.razorpay_order_id, 'Checkout closed before payment'); },
      },
    });
    rzp.on('payment.failed', (r) => {
      busy(false);
      report(data.razorpay_order_id, (r.error && r.error.description) || 'Payment failed');
      showAlert((r.error && r.error.description) || 'Payment failed. You can try again.');
    });
    rzp.open();
  });
})();
