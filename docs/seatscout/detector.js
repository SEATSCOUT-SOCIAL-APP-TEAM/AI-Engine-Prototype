// detector.js: YOLO11n (Ultralytics, exported to ONNX at 512 x 512) running in the browser with ONNX Runtime Web.
// It keeps the classes SeatScout cares about: people, and the things guests leave on a table or a chair.

const SIZE = 512;
export const KEEP = { 0: 'person', 24: 'backpack', 26: 'handbag', 28: 'suitcase', 39: 'bottle', 40: 'wine glass', 41: 'cup', 63: 'laptop', 64: 'mouse', 67: 'cell phone', 73: 'book', 25: 'umbrella' };

export async function loadDetector(modelUrl) {
  const ort = window.ort;
  if (!ort) throw new Error('ONNX Runtime did not load');
  ort.env.wasm.wasmPaths = 'https://cdn.jsdelivr.net/npm/onnxruntime-web@1.20.1/dist/';
  ort.env.wasm.numThreads = self.crossOriginIsolated ? Math.min(4, navigator.hardwareConcurrency || 2) : 1;
  let session = null, backend = 'wasm';
  if (navigator.gpu) {
    try { session = await ort.InferenceSession.create(modelUrl, { executionProviders: ['webgpu'], graphOptimizationLevel: 'all' }); backend = 'webgpu' } catch (e) { session = null }
  }
  if (!session) session = await ort.InferenceSession.create(modelUrl, { executionProviders: ['wasm'], graphOptimizationLevel: 'all' });
  const canvas = document.createElement('canvas'); canvas.width = canvas.height = SIZE;
  const ctx = canvas.getContext('2d', { willReadFrequently: true });
  const input = new Float32Array(3 * SIZE * SIZE);

  // source: a canvas already holding the frame (w x h). Returns boxes in 0..1 coordinates of that frame.
  async function detect(source, w, h, conf = 0.35) {
    const s = Math.min(SIZE / w, SIZE / h), nw = Math.round(w * s), nh = Math.round(h * s), px = (SIZE - nw) / 2, py = (SIZE - nh) / 2;
    ctx.fillStyle = 'rgb(114,114,114)'; ctx.fillRect(0, 0, SIZE, SIZE); ctx.drawImage(source, 0, 0, w, h, px, py, nw, nh);
    const d = ctx.getImageData(0, 0, SIZE, SIZE).data, A = SIZE * SIZE;
    for (let i = 0, p = 0; i < A; i++, p += 4) { input[i] = d[p] / 255; input[i + A] = d[p + 1] / 255; input[i + 2 * A] = d[p + 2] / 255 }
    const t0 = performance.now();
    const out = await session.run({ [session.inputNames[0]]: new ort.Tensor('float32', input, [1, 3, SIZE, SIZE]) });
    const ms = performance.now() - t0;
    const o = out[session.outputNames[0]], v = o.data, n = o.dims[2], boxes = [];
    for (let j = 0; j < n; j++) {
      let best = -1, bs = conf;
      for (const k in KEEP) { const sc = v[(4 + +k) * n + j]; if (sc > bs) { bs = sc; best = +k } }
      if (best < 0) continue;
      const cx = v[j], cy = v[n + j], bw = v[2 * n + j], bh = v[3 * n + j];
      const x = (cx - bw / 2 - px) / s / w, y = (cy - bh / 2 - py) / s / h;
      boxes.push({ cls: best, name: KEEP[best], kind: best === 0 ? 'person' : 'object', score: bs, x: Math.max(0, x), y: Math.max(0, y), w: Math.min(1, bw / s / w), h: Math.min(1, bh / s / h) });
    }
    return { boxes: nms(boxes, 0.45), ms };
  }
  return { detect, backend };
}

function iou(a, b) {
  const ix = Math.max(0, Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x)), iy = Math.max(0, Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y));
  const i = ix * iy; return i / (a.w * a.h + b.w * b.h - i);
}
function nms(boxes, thr) {
  boxes.sort((a, b) => b.score - a.score); const keep = [];
  for (const b of boxes) if (!keep.some(k => k.cls === b.cls && iou(k, b) > thr)) keep.push(b);
  return keep;
}
