// Phone OTP sign-in with Firebase. Firebase sends and checks the SMS code in the browser;
// the Django server then verifies the resulting ID token before it logs anyone in.
import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.14.1/firebase-app.js';
import { getAuth, RecaptchaVerifier, signInWithPhoneNumber } from 'https://www.gstatic.com/firebasejs/10.14.1/firebase-auth.js';

const $ = (id) => document.getElementById(id);
const cfg = JSON.parse($('firebase-config').textContent || '{}');
const meta = $('loginConfig').dataset;
const alertBox = $('loginAlert');
const RESEND_SECONDS = 30;

const showAlert = (msg) => { alertBox.textContent = msg || ''; alertBox.hidden = !msg; };
const csrf = () => (document.cookie.match(/(?:^|; )csrftoken=([^;]+)/) || [])[1] || '';

if (!cfg.apiKey) {
  showAlert('Sign-in is not set up yet. Add the Firebase web config to the Django settings.');
  $('sendBtn').disabled = true;
  throw new Error('Missing FIREBASE_WEB_CONFIG');
}

const auth = getAuth(initializeApp(cfg));
auth.languageCode = 'en';

let verifier = null;
let confirmation = null;
let phone = '';
let timer = null;

const ERRORS = {
  'auth/invalid-phone-number': 'That mobile number does not look right.',
  'auth/missing-phone-number': 'Enter your mobile number.',
  'auth/too-many-requests': 'Too many attempts. Please wait a while and try again.',
  'auth/quota-exceeded': 'We cannot send codes right now. Please try again later.',
  'auth/captcha-check-failed': 'Security check failed. Please try again.',
  'auth/invalid-verification-code': 'That code is not correct. Check it and try again.',
  'auth/code-expired': 'That code has expired. Request a new one.',
  'auth/operation-not-allowed': 'Phone sign-in is not enabled for this store yet.',
  'auth/network-request-failed': 'Network problem. Check your connection and try again.',
};
const explain = (e) => ERRORS[e && e.code] || 'Something went wrong. Please try again.';

function freshVerifier() {
  if (verifier) { try { verifier.clear(); } catch (e) { /* already gone */ } verifier = null; }
  const host = $('recaptcha-container');
  host.innerHTML = '';
  const slot = document.createElement('div');   // new element every time
  host.appendChild(slot);
  verifier = new RecaptchaVerifier(auth, slot, { size: 'invisible' });
  return verifier;
}

function startTimer() {
  let left = RESEND_SECONDS;
  $('resendBtn').disabled = true;
  clearInterval(timer);
  const tick = () => {
    $('resendTimer').textContent = left > 0 ? `You can resend in ${left}s` : '';
    if (left-- <= 0) { clearInterval(timer); $('resendBtn').disabled = false; }
  };
  tick();
  timer = setInterval(tick, 1000);
}

async function sendCode() {
  showAlert('');
  const btn = $('sendBtn');
  btn.disabled = true;
  try {
    confirmation = await signInWithPhoneNumber(auth, phone, freshVerifier());
    $('sentTo').textContent = phone;
    $('phoneForm').hidden = true;
    $('otpForm').hidden = false;
    $('otp').value = '';
    $('otp').focus();
    startTimer();
  } catch (e) {
    console.error('send OTP failed:', e.code, e);   // helpful while debugging
    showAlert(explain(e));
    try { verifier && verifier.clear(); } catch (_) { /* ignore */ }
    verifier = null;
  } finally {
    btn.disabled = false;
  }
}

$('phoneForm').addEventListener('submit', (e) => {
  e.preventDefault();
  const digits = $('phone').value.replace(/\D/g, '');
  const ok = /^[6-9]\d{9}$/.test(digits);
  $('phoneError').hidden = ok;
  $('phone').classList.toggle('is-invalid', !ok);
  if (!ok) return;
  phone = '+91' + digits;
  sendCode();
});

$('resendBtn').addEventListener('click', sendCode);

$('changeBtn').addEventListener('click', () => {
  clearInterval(timer);
  confirmation = null;
  showAlert('');
  $('otpForm').hidden = true;
  $('phoneForm').hidden = false;
  $('phone').focus();
});

$('otp').addEventListener('input', (e) => {
  e.target.value = e.target.value.replace(/\D/g, '').slice(0, 6);
  if (e.target.value.length === 6) $('otpForm').requestSubmit();
});

$('otpForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const code = $('otp').value;
  if (code.length !== 6 || !confirmation) return;
  const btn = $('verifyBtn');
  btn.disabled = true;
  btn.textContent = 'Verifying…';
  showAlert('');
  try {
    const result = await confirmation.confirm(code);
    const idToken = await result.user.getIdToken();
    const res = await fetch(meta.loginUrl, {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf() },
      body: JSON.stringify({ id_token: idToken, next: meta.next }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data.ok) throw { message: data.message || 'Sign-in failed. Please try again.' };
    await auth.signOut().catch(() => {});   // Django's session is the login; no need to keep Firebase's
    location.href = data.redirect;
  } catch (err) {
    showAlert(err.code ? explain(err) : err.message);
    btn.disabled = false;
    btn.textContent = 'Verify and continue';
  }
});