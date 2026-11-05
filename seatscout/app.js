// app.js: SeatScout in the browser. Video in, YOLO11n detections, seat zones, the seat rules, a live layout.
import { loadDetector } from './detector.js';
import { createSeat, updateSeat, clearSeat, observe, stayed, away, DEFAULT_RULES } from './seats.js';

const $ = id => document.getElementById(id);
const SAMPLE = id => `https://assets.mixkit.co/videos/${id}/${id}-360.mp4`;
const MAXW = 960;
const rules = { ...DEFAULT_RULES };
const video = document.createElement('video'); video.muted = true; video.playsInline = true; video.loop = true; video.crossOrigin = 'anonymous';
const clean = document.createElement('canvas'), work = document.createElement('canvas');
const cctx = clean.getContext('2d', { willReadFrequently: true }), wctx = work.getContext('2d', { willReadFrequently: true });
const screen = $('screen'), sctx = screen.getContext('2d');

let det = null, source = 'sample', stream = null, seats = [], dets = [], busy = false, lastDet = 0, autoNext = true, editing = false, drag = null, nextId = 1;
const alerts = new Map(), events = [];
const t0 = Date.now();

/* ---------- model ---------- */
async function boot() {
  try {
    const res = await fetch('model/yolo11n.onnx'); const total = +res.headers.get('content-length') || 10.7e6;
    const reader = res.body.getReader(), parts = []; let got = 0;
    for (;;) { const { done, value } = await reader.read(); if (done) break; parts.push(value); got += value.length; $('l-bar').style.width = Math.min(100, got / total * 100) + '%' }
    const buf = new Uint8Array(got); let o = 0; for (const p of parts) { buf.set(p, o); o += p.length }
    $('l-s').textContent = 'Starting the model…';
    det = await loadDetector(buf);
    $('st-model').textContent = `YOLO11n · ${det.backend === 'webgpu' ? 'WebGPU' : 'WebAssembly'}`;
    $('loading').hidden = true;
  } catch (e) { $('l-s').textContent = 'The model could not start in this browser: ' + e.message }
}

/* ---------- sources ---------- */
function stopStream() { if (stream) stream.getTracks().forEach(t => t.stop()); stream = null; $('webcam').setAttribute('aria-pressed', 'false') }
function reset(note) { seats = []; dets = []; nextId = 1; alerts.clear(); autoNext = true; renderSide(); if (note) logEvent({ type: 'info', text: note, seat: null, at: Date.now() }) }
async function useSample(id) {
  stopStream(); source = 'sample'; $('sample').classList.add('on'); video.srcObject = null; video.src = SAMPLE(id); reset('Sample clip loaded. Seats are placed where people sit.');
  $('seats-note').hidden = false; try { await video.play() } catch (e) {} $('play').textContent = 'Pause';
}
async function useWebcam() {
  if (stream) { stopStream(); return useSample($('sample').value) }
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: { width: { ideal: 1280 }, height: { ideal: 720 } }, audio: false });
    source = 'webcam'; $('sample').classList.remove('on'); video.removeAttribute('src'); video.srcObject = stream; await video.play();
    $('webcam').setAttribute('aria-pressed', 'true'); reset('Webcam on. Sit in view: you are seat 1. Get up, leave your phone or a cup, and watch.');
  } catch (e) { logEvent({ type: 'info', text: 'The camera is not available. Allow access, or use a sample clip.', seat: null, at: Date.now() }) }
}
function useFile(f) {
  stopStream(); source = 'file'; $('sample').classList.remove('on'); video.srcObject = null; video.src = URL.createObjectURL(f); reset('Your video is loaded. It stays on this device.'); video.play().catch(() => {});
}

/* ---------- geometry ---------- */
let fit = { x: 0, y: 0, w: 1, h: 1 };
function sizeScreen() {
  const r = screen.getBoundingClientRect(), dpr = Math.min(2, devicePixelRatio || 1);
  screen.width = Math.round(r.width * dpr); screen.height = Math.round(r.height * dpr);
}
const toFrame = (ev) => { const r = screen.getBoundingClientRect(), dpr = screen.width / r.width; const x = ((ev.clientX - r.left) * dpr - fit.x) / fit.w, y = ((ev.clientY - r.top) * dpr - fit.y) / fit.h; return { x: Math.min(1, Math.max(0, x)), y: Math.min(1, Math.max(0, y)) } };
const inside = (p, z) => p.x >= z.x && p.x <= z.x + z.w && p.y >= z.y && p.y <= z.y + z.h;
const iou = (a, b) => { const ix = Math.max(0, Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x)), iy = Math.max(0, Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y)), i = ix * iy; return i / (a.w * a.h + b.w * b.h - i) };
const union = (a, b) => { const x = Math.min(a.x, b.x), y = Math.min(a.y, b.y); return { x, y, w: Math.max(a.x + a.w, b.x + b.w) - x, h: Math.max(a.y + a.h, b.y + b.h) - y } };

function autoSeats() {
  const zones = [];
  for (const p of dets.filter(d => d.kind === 'person' && d.w * d.h > 0.006)) {
    const z = { x: p.x + p.w * .08, y: p.y + p.h * .3, w: p.w * .84, h: Math.min(p.h * .7, 1 - (p.y + p.h * .3)) };
    if (!zones.some(q => iou(q, z) > .35)) zones.push(z);
  }
  zones.sort((a, b) => a.x - b.x);
  seats = zones.map(z => createSeat(nextId++, z)); alerts.clear(); renderSide();
  if (zones.length) logEvent({ type: 'info', text: `${zones.length} seat${zones.length > 1 ? 's' : ''} placed on the people in view.`, seat: null, at: Date.now() });
}

/* ---------- the loop ---------- */
function drawFrame() {
  const vw = video.videoWidth, vh = video.videoHeight; if (!vw) return false;
  const s = Math.min(1, MAXW / vw), w = Math.round(vw * s), h = Math.round(vh * s);
  if (clean.width !== w || clean.height !== h) { clean.width = work.width = w; clean.height = work.height = h }
  cctx.drawImage(video, 0, 0, w, h); wctx.drawImage(clean, 0, 0);
  // a seat whose guest "steps away" on a recorded clip: hide that person from the detector, keep what they left behind
  for (const st of seats) if (st.hidden && st.mask) {
    const m = st.mask, X = Math.round(m.x * w), Y = Math.round(m.y * h), W = Math.max(1, Math.round(m.w * w)), H = Math.max(1, Math.round(m.h * h));
    wctx.fillStyle = st.fill || '#555'; wctx.fillRect(X, Y, W, H);
    for (const o of st.keep || []) wctx.drawImage(clean, o.x * w, o.y * h, o.w * w, o.h * h, o.x * w, o.y * h, o.w * w, o.h * h);
  }
  return true;
}
function avgColor(z) {
  const w = clean.width, h = clean.height, X = Math.max(0, Math.round(z.x * w) - 4), Y = Math.max(0, Math.round(z.y * h) - 4);
  const W = Math.min(w - X, Math.round(z.w * w) + 8), H = Math.min(h - Y, Math.round(z.h * h) + 8), d = cctx.getImageData(X, Y, W, H).data;
  let r = 0, g = 0, b = 0, n = 0; for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) { if (x > 3 && x < W - 4 && y > 3 && y < H - 4) continue; const i = (y * W + x) * 4; r += d[i]; g += d[i + 1]; b += d[i + 2]; n++ }
  return `rgb(${r / n | 0},${g / n | 0},${b / n | 0})`;
}
async function detectNow() {
  if (busy || !det || document.hidden) return; busy = true; lastDet = performance.now();
  try {
    const { boxes, ms } = await det.detect(work, work.width, work.height);
    dets = boxes; const now = Date.now();
    $('st-ms').textContent = `${Math.round(ms)} ms per frame`;
    const np = boxes.filter(b => b.kind === 'person').length; $('st-count').textContent = `${np} ${np === 1 ? 'person' : 'people'} · ${boxes.length - np} object${boxes.length - np === 1 ? '' : 's'}`;
    if (autoNext && boxes.some(b => b.kind === 'person')) { autoNext = false; if (!seats.length) autoSeats() }
    for (const st of seats) {
      // belongings flicker in and out of detection, so they count for a few seconds after they were last seen
      const o = observe(st.zone, boxes); if (o.belongings) st.lastObj = now; o.belongings = st.lastObj !== undefined && now - st.lastObj < 4000;
      for (const ev of updateSeat(st, o, now, rules)) onEvent(st, ev);
    }
  } catch (e) { $('st-ms').textContent = 'detector error: ' + e.message }
  busy = false;
}
function onEvent(st, ev) {
  logEvent(ev);
  if (ev.type === 'check') alerts.set(st.id, now());
  if (ev.type !== 'check' && st.state !== 'check') alerts.delete(st.id);
  renderSide();
}
const now = () => Date.now();
const COLORS = { free: '#C9DD8B', taken: '#9BBC0F', away: '#FFD24D', check: '#E2553A' };
function render() {
  sizeScreen();
  const W = screen.width, H = screen.height; sctx.fillStyle = '#0B140B'; sctx.fillRect(0, 0, W, H);
  if (!work.width) return;
  const s = Math.min(W / work.width, H / work.height); fit = { x: (W - work.width * s) / 2, y: (H - work.height * s) / 2, w: work.width * s, h: work.height * s };
  sctx.imageSmoothingEnabled = true; sctx.drawImage(work, fit.x, fit.y, fit.w, fit.h);
  const R = b => [fit.x + b.x * fit.w, fit.y + b.y * fit.h, b.w * fit.w, b.h * fit.h];
  if ($('privacy').checked) {
    sctx.imageSmoothingEnabled = false;
    for (const d of dets) if (d.kind === 'person') { const [x, y, w, h] = R(d), k = 14; const tw = Math.max(1, Math.round(w / k)), th = Math.max(1, Math.round(h / k));
      const tmp = pix; tmp.width = tw; tmp.height = th; tmp.getContext('2d').drawImage(work, d.x * work.width, d.y * work.height, d.w * work.width, d.h * work.height, 0, 0, tw, th); sctx.drawImage(tmp, x, y, w, h) }
    sctx.imageSmoothingEnabled = true;
  }
  const dpr = screen.width / screen.getBoundingClientRect().width;
  if ($('boxes').checked) for (const d of dets) {
    const [x, y, w, h] = R(d); sctx.lineWidth = 1.5 * dpr; sctx.strokeStyle = d.kind === 'person' ? 'rgba(255,255,255,.85)' : '#FFD24D'; sctx.setLineDash(d.kind === 'person' ? [] : [4 * dpr, 3 * dpr]); sctx.strokeRect(x, y, w, h); sctx.setLineDash([]);
    const label = `${d.name} ${(d.score * 100) | 0}%`; sctx.font = `${600} ${11 * dpr}px Archivo, sans-serif`; const tw = sctx.measureText(label).width + 8 * dpr;
    sctx.fillStyle = d.kind === 'person' ? 'rgba(255,255,255,.9)' : '#FFD24D'; sctx.fillRect(x, y - 16 * dpr, tw, 16 * dpr); sctx.fillStyle = '#0F1A0F'; sctx.fillText(label, x + 4 * dpr, y - 4 * dpr);
  }
  for (const st of seats) {
    const [x, y, w, h] = R(st.zone), c = COLORS[st.state];
    if (st.hidden && st.mask) { const [mx, my, mw, mh] = R(st.mask); sctx.save(); sctx.beginPath(); sctx.rect(mx, my, mw, mh); sctx.clip(); sctx.strokeStyle = 'rgba(255,255,255,.18)'; sctx.lineWidth = 6 * dpr;
      for (let k = -mh; k < mw; k += 16 * dpr) { sctx.beginPath(); sctx.moveTo(mx + k, my + mh); sctx.lineTo(mx + k + mh, my); sctx.stroke() } sctx.restore() }
    sctx.lineWidth = 3 * dpr; sctx.strokeStyle = c; sctx.fillStyle = c + '22'; roundRect(x, y, w, h, 8 * dpr); sctx.fill(); sctx.stroke();
    const tag = `${st.id} · ${st.state.toUpperCase()}${st.since !== null ? ' · ' + mmss(stayed(st, now())) : ''}`; sctx.font = `700 ${12 * dpr}px Archivo, sans-serif`;
    const tw = sctx.measureText(tag).width + 14 * dpr; sctx.fillStyle = c; roundRect(x + 6 * dpr, y + h - 26 * dpr, tw, 20 * dpr, 10 * dpr); sctx.fill(); sctx.fillStyle = st.state === 'check' ? '#fff' : '#0F380F'; sctx.fillText(tag, x + 13 * dpr, y + h - 11.5 * dpr);
  }
  if (drag) { const a = drag.a, b = drag.b, z = { x: Math.min(a.x, b.x), y: Math.min(a.y, b.y), w: Math.abs(a.x - b.x), h: Math.abs(a.y - b.y) }, [x, y, w, h] = R(z);
    sctx.setLineDash([6 * dpr, 4 * dpr]); sctx.strokeStyle = '#fff'; sctx.lineWidth = 2 * dpr; sctx.strokeRect(x, y, w, h); sctx.setLineDash([]) }
}
const pix = document.createElement('canvas');
function roundRect(x, y, w, h, r) { sctx.beginPath(); sctx.moveTo(x + r, y); sctx.arcTo(x + w, y, x + w, y + h, r); sctx.arcTo(x + w, y + h, x, y + h, r); sctx.arcTo(x, y + h, x, y, r); sctx.arcTo(x, y, x + w, y, r); sctx.closePath() }
const mmss = ms => { const s = Math.floor(ms / 1000); return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}` };

let lastSide = 0;
function loop(t) {
  requestAnimationFrame(loop);
  if (drawFrame() && performance.now() - lastDet > 90) detectNow();
  render();
  if (t - lastSide > 250) { lastSide = t; renderSide(true) }
}

/* ---------- side panel ---------- */
function renderSide(timersOnly) {
  const c = { free: 0, taken: 0, away: 0, check: 0 }; seats.forEach(s => c[s.state]++);
  for (const k in c) $('n-' + k).textContent = c[k];
  const fl = $('floor'), ul = $('seats');
  if (timersOnly && fl.childElementCount === seats.length && ul.childElementCount === Math.max(1, seats.length)) {
    seats.forEach((s, i) => { const tile = fl.children[i], li = ul.children[i]; if (!tile || !li) return; tile.className = 'tile ' + s.state; tile.querySelector('em').textContent = s.since !== null ? mmss(stayed(s, now())) : 'free'; li.className = s.state; fillRow(li, s) });
    const al = $('alerts'); if (al.querySelectorAll('li[data-id]').length !== alerts.size) renderAlerts();
    else al.querySelectorAll('li[data-id]').forEach(li => { const s = seats.find(x => x.id === +li.dataset.id); if (s) li.querySelector('.tt').textContent = mmss(away(s, now())) });
    return;
  }
  fl.innerHTML = ''; ul.innerHTML = '';
  if (!seats.length) { fl.innerHTML = '<p class="empty">No seats yet. Press “Place seats on people”, or Edit seats and draw them on the video.</p>'; ul.innerHTML = '<li class="none">No seats yet.</li>' }
  for (const s of seats) {
    const tile = document.createElement('div'); tile.className = 'tile ' + s.state;
    tile.style.left = (8 + (s.zone.x + s.zone.w / 2) * 84) + '%'; tile.style.top = (14 + Math.min(1, s.zone.y + s.zone.h) * 70) + '%';
    tile.innerHTML = `<i>${s.id}</i><em>${s.since !== null ? mmss(stayed(s, now())) : 'free'}</em>`; fl.appendChild(tile);
    const li = document.createElement('li'); li.className = s.state;
    li.innerHTML = `<span class="no">${s.id}</span><span class="st"></span><span class="pill"></span>${source === 'webcam' ? '' : '<button class="btn hide" type="button"></button>'}`;
    fillRow(li, s);
    const b = li.querySelector('.hide'); if (b) b.addEventListener('click', () => toggleHide(s));
    ul.appendChild(li);
  }
  renderAlerts();
}
function fillRow(li, s) {
  const n = now(), st = li.querySelector('.st'), label = { free: 'Free', taken: 'Taken', away: 'Away', check: 'Check' }[s.state];
  const sub = s.state === 'free' ? 'Waiting for a guest' : s.state === 'taken' ? `Stayed ${mmss(stayed(s, n))}` : `Away ${mmss(away(s, n))}${s.belongings ? ', belongings left' : ''} · stayed ${mmss(stayed(s, n))}`;
  st.innerHTML = `${label}<small>${sub}</small>`; li.querySelector('.pill').textContent = s.state;
  const b = li.querySelector('.hide'); if (b) b.textContent = s.hidden ? 'Come back' : 'Step away';
}
function toggleHide(s) {
  if (!s.hidden) {
    let m = s.zone; const keep = [];
    for (const d of dets) { const ov = iou(s.zone, d) > 0 && (Math.max(0, Math.min(s.zone.x + s.zone.w, d.x + d.w) - Math.max(s.zone.x, d.x)) * Math.max(0, Math.min(s.zone.y + s.zone.h, d.y + d.h) - Math.max(s.zone.y, d.y))) > 0;
      if (!ov) continue; if (d.kind === 'person') m = union(m, { x: d.x - .01, y: d.y - .01, w: d.w + .02, h: d.h + .02 }); else keep.push(d) }
    s.mask = { x: Math.max(0, m.x), y: Math.max(0, m.y), w: Math.min(1 - Math.max(0, m.x), m.w), h: Math.min(1 - Math.max(0, m.y), m.h) }; s.fill = avgColor(s.mask); s.keep = keep; s.hidden = true;
    logEvent({ type: 'info', seat: s.id, text: `Simulating: the guest at seat ${s.id} gets up${keep.length ? `, leaving ${keep.map(k => k.name).join(', ')}` : ''}.`, at: now() });
  } else { s.hidden = false; logEvent({ type: 'info', seat: s.id, text: `Simulating: the guest at seat ${s.id} comes back.`, at: now() }) }
  renderSide();
}
function renderAlerts() {
  const ul = $('alerts'); ul.innerHTML = ''; $('alerts-n').textContent = alerts.size ? `${alerts.size} to check` : 'No alerts';
  if (!alerts.size) { ul.innerHTML = '<li class="none">Nothing to check. Staff are asked when a seat is held too long.</li>'; return }
  for (const [id] of alerts) { const s = seats.find(x => x.id === id); if (!s) continue;
    const li = document.createElement('li'); li.dataset.id = id; li.innerHTML = `<span><b>Seat ${id}</b> has been empty for <span class="tt">${mmss(away(s, now()))}</span> with belongings left.</span><button class="btn sm" type="button">Checked</button>`;
    li.querySelector('button').addEventListener('click', () => { for (const ev of clearSeat(s, now())) logEvent(ev); alerts.delete(id); renderSide() }); ul.appendChild(li) }
}
function logEvent(ev) {
  events.unshift(ev); if (events.length > 60) events.pop();
  const ol = $('log'), li = document.createElement('li'); li.className = ev.type;
  const d = new Date(ev.at); li.innerHTML = `<time>${d.toLocaleTimeString('en-GB')}</time><span class="s">${ev.seat ? 'SEAT ' + ev.seat : ''}</span><span></span>`; li.lastChild.textContent = ev.text;
  ol.prepend(li); while (ol.children.length > 60) ol.lastChild.remove();
}

/* ---------- editing ---------- */
screen.addEventListener('pointerdown', e => {
  if (!editing) return; const p = toFrame(e), hit = seats.find(s => inside(p, s.zone));
  if (hit) { seats = seats.filter(s => s !== hit); alerts.delete(hit.id); logEvent({ type: 'info', seat: hit.id, text: `Seat ${hit.id} removed.`, at: now() }); renderSide(); return }
  drag = { a: p, b: p }; screen.setPointerCapture(e.pointerId);
});
screen.addEventListener('pointermove', e => { if (drag) drag.b = toFrame(e) });
screen.addEventListener('pointerup', () => {
  if (!drag) return; const a = drag.a, b = drag.b; drag = null;
  const z = { x: Math.min(a.x, b.x), y: Math.min(a.y, b.y), w: Math.abs(a.x - b.x), h: Math.abs(a.y - b.y) };
  if (z.w * z.h < 0.004) return; const s = createSeat(nextId++, z); seats.push(s); logEvent({ type: 'info', seat: s.id, text: `Seat ${s.id} drawn.`, at: now() }); renderSide();
});

/* ---------- wiring ---------- */
$('sample').addEventListener('change', e => useSample(e.target.value));
$('sample').addEventListener('click', () => { if (source !== 'sample') useSample($('sample').value) });
$('webcam').addEventListener('click', useWebcam);
$('file').addEventListener('change', e => { const f = e.target.files[0]; if (f) useFile(f); e.target.value = '' });
$('play').addEventListener('click', () => { if (video.paused) { video.play(); $('play').textContent = 'Pause' } else { video.pause(); $('play').textContent = 'Play' } });
$('edit').addEventListener('click', () => { editing = !editing; $('edit').setAttribute('aria-pressed', String(editing)); $('view').classList.toggle('editing', editing); $('hint').hidden = !editing });
$('auto').addEventListener('click', autoSeats);
$('clear-log').addEventListener('click', () => { $('log').innerHTML = ''; events.length = 0 });
for (const k of ['absence', 'grace', 'limit']) $(k).addEventListener('input', e => { rules[k] = +e.target.value; $('v-' + k).textContent = (rules[k] / 1000).toFixed(rules[k] < 10000 ? 1 : 0) + ' s' });
addEventListener('resize', render);
window.__ss = { seats: () => seats, dets: () => dets, rules, toggleHide: id => toggleHide(seats.find(s => s.id === id)), ready: () => !!det, backend: () => det && det.backend };

boot(); useSample($('sample').value); requestAnimationFrame(loop);
