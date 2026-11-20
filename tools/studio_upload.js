// Bibi Buzz TV - uploads the day's videos from the "media" branch to YouTube Studio, one by one.
// Run it inside a signed-in studio.youtube.com tab (the channel's content page). It never touches passwords:
// the browser must already be signed in. It fetches each mp4 from the media branch, drops it into Studio's own
// upload dialog, fills the form (title, description, tags, English (US), Education, made for kids = yes,
// paid promotion = no, AI/altered content = no), publishes it as PUBLIC and records the video id.
//
//   __bibi.run({ dates: ['2026-11-20'], only: ['d001-L1'], skipTitles: [...], skipIds: [...] })   // starts in the background
//   limitWaitMin: 20   -> if the very first upload of the run hits the daily limit (YouTube counts uploads over a rolling
//                         24 h window, so the slot of exactly one day ago may free up a few minutes later), wait and retry
//                         every limitRetryMin (default 3) minutes for up to that long. Once a video of this run has been
//                         published, a limit hit means the day's quota is used up and the run stops at once.
//   __bibi.status()                                                                              // poll this
//   __bibi.scrape()                                                                              // titles already in Studio (Videos + Shorts tabs)
//   __bibi.stop = true                                                                           // stop after the current step
(() => {
  const BASE = 'https://raw.githubusercontent.com/ebrukuskilic/bibi-buzz-tv/media/';
  if (window.__bibi && window.__bibi.running) return 'already running';
  const S = window.__bibi = { v: 2, running: false, stop: false, phase: 'idle', current: null, limit: false, log: [], done: [], failed: [], published: {} };
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const txt = e => ((e && (e.innerText || e.textContent)) || '').replace(/\s+/g, ' ').trim();
  const L = m => { S.log.push(new Date().toTimeString().slice(0, 8) + ' ' + m); if (S.log.length > 300) S.log.shift(); };

  // timers that keep ticking when the browser pane is hidden: a worker timer, with plain setTimeout as the fallback
  const plain = ms => new Promise(r => setTimeout(r, ms));
  let wk = null, wid = 0; const waits = {};
  try {
    wk = new Worker(URL.createObjectURL(new Blob(['onmessage=e=>setTimeout(()=>postMessage(e.data.id),e.data.ms)'], { type: 'text/javascript' })));
    wk.onmessage = e => { const r = waits[e.data]; if (r) { delete waits[e.data]; r(); } };
  } catch (e) { wk = null; }
  const sleep = ms => wk ? new Promise(r => { const id = ++wid; waits[id] = r; wk.postMessage({ id, ms }); }) : plain(ms);
  S.ready = (async () => {
    if (wk) { const ok = await Promise.race([sleep(30).then(() => true), plain(2000).then(() => false)]); if (!ok) { try { wk.terminate(); } catch (e) {} wk = null; } }
    L('timers: ' + (wk ? 'worker' : 'page'));
  })();

  const until = async (fn, ms, what) => {
    const t0 = Date.now();
    for (;;) {
      let r = null; try { r = fn(); } catch (e) {}
      if (r) return r;
      if (S.stop) throw new Error('stopped');
      if (Date.now() - t0 > ms) throw new Error('timeout: ' + what);
      await sleep(250);
    }
  };
  const dlg = () => $('ytcp-uploads-dialog');
  const isOpen = () => { const d = dlg(); return !!(d && $('tp-yt-paper-dialog', d)); };

  async function closeShare() {                              // the "Video yayınlandı" dialog; closing it also removes the upload dialog
    for (let i = 0; i < 12 && $('ytcp-video-share-dialog'); i++) {
      const b = $('ytcp-video-share-dialog #close-button');
      if (b) b.click();
      await sleep(1500);
    }
  }
  async function openUpload() {
    await closeShare();
    const open = $('ytcp-uploads-dialog input[type=file][name=Filedata]');
    if (open) return open;                                   // already open on the file picker step: use it
    if (isOpen()) throw new Error('the upload dialog is open on another step');
    for (let k = 0; k < 3; k++) {
      const create = $('ytcp-button.ytcpAppHeaderCreateIcon') || $('ytcp-button#create-icon');
      if (!create) throw new Error('Create button not found (is this the Studio content page?)');
      create.click(); await sleep(1200);                    // let the menu finish opening before choosing an item
      const item = $$('tp-yt-paper-item').find(e => /Video yükle/.test(txt(e)));
      if (item) item.click();
      try { return await until(() => $('ytcp-uploads-dialog input[type=file][name=Filedata]'), 8000, 'file input'); }
      catch (e) {
        const t = txt(dlg());
        if (/sınır|limit/i.test(t)) {
          S.limit = true;
          const x = $('#ytcp-uploads-dialog-close-button'); if (x) x.click();
          await sleep(1500);
          throw new Error('daily upload limit reached: ' + t.slice(0, 160));
        }
        L('open attempt ' + (k + 1) + ' failed'); await sleep(600);
      }
    }
    throw new Error('could not open the upload dialog');
  }
  async function getFile(date, name) {
    const r = await fetch(BASE + date + '/' + name + '?t=' + Date.now());
    if (!r.ok) throw new Error('download ' + name + ': HTTP ' + r.status);
    return new File([await r.blob()], name, { type: 'video/mp4', lastModified: Date.now() });
  }
  async function setBox(d, sel, text) {
    const box = $(sel, d);
    box.scrollIntoView({ block: 'center' }); box.focus(); await sleep(100);
    document.execCommand('selectAll', false, null); document.execCommand('delete', false, null);
    document.execCommand('insertText', false, text);
    box.dispatchEvent(new Event('input', { bubbles: true })); await sleep(150);
  }
  async function choose(d, name) {
    const r = $(`tp-yt-paper-radio-button[name=${name}]`, d);
    if (!r) throw new Error('radio ' + name + ' not found');
    if (r.getAttribute('aria-checked') !== 'true') { r.scrollIntoView({ block: 'center' }); r.click(); await sleep(400); }
    if (r.getAttribute('aria-checked') !== 'true') throw new Error('could not set ' + name);
  }
  async function pickItem(trigger, label) {
    trigger.scrollIntoView({ block: 'center' }); trigger.click(); await sleep(800);
    const it = $$('tp-yt-paper-item').find(e => txt(e) === label);
    if (!it) throw new Error('menu item not found: ' + label);
    it.click(); await sleep(700);
  }
  async function fill(d, v) {
    await setBox(d, '#title-textarea #textbox', v.title);
    await setBox(d, '#description-textarea #textbox', v.description);
    await choose(d, 'VIDEO_MADE_FOR_KIDS_MFK');
    const tg = $('ytcp-button#toggle-button', d);
    if (tg && /göster/.test(tg.getAttribute('aria-label') || '')) { tg.click(); await sleep(1200); }
    await choose(d, 'VIDEO_PAID_PRODUCT_PLACEMENT_NO');
    await choose(d, 'VIDEO_HAS_ALTERED_CONTENT_NO');
    const inp = $('ytcp-form-input-container#tags-container input#text-input', d);
    inp.scrollIntoView({ block: 'center' }); inp.focus(); await sleep(150);
    document.execCommand('insertText', false, v.tags.join(','));
    inp.dispatchEvent(new Event('input', { bubbles: true })); await sleep(400);
    inp.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true })); await sleep(500);
    const lang = $('ytcp-form-language-input#language-input', d);
    if (!/İngilizce \(Amerika/.test(txt(lang))) await pickItem($('ytcp-text-dropdown-trigger', lang), 'İngilizce (Amerika Birleşik Devletleri)');
    const cat = $('ytcp-form-select#category', d);
    if (!/Eğitim/.test(txt(cat))) await pickItem($('ytcp-text-dropdown-trigger', cat), 'Eğitim');
  }
  function problems(d, v) {
    const p = [], norm = s => (s || '').replace(/\s+/g, ' ').trim();
    if (norm($('#title-textarea #textbox', d).innerText) !== norm(v.title)) p.push('title');
    if (norm($('#description-textarea #textbox', d).innerText).length < norm(v.description).length * 0.95) p.push('description');
    const on = n => { const r = $(`tp-yt-paper-radio-button[name=${n}]`, d); return !!r && r.getAttribute('aria-checked') === 'true'; };
    if (!on('VIDEO_MADE_FOR_KIDS_MFK')) p.push('made for kids');
    if (!on('VIDEO_PAID_PRODUCT_PLACEMENT_NO')) p.push('paid promotion');
    if (!on('VIDEO_HAS_ALTERED_CONTENT_NO')) p.push('altered content');
    if ($$('ytcp-form-input-container#tags-container ytcp-chip', d).length < v.tags.length) p.push('tags');
    if (!/İngilizce \(Amerika/.test(txt($('ytcp-form-language-input#language-input', d)))) p.push('language');
    if (!/Eğitim/.test(txt($('ytcp-form-select#category', d)))) p.push('category');
    return p;
  }

  async function one(date, v) {
    L('start ' + v.id + ' | ' + v.title);
    let d = dlg();
    if (d && isOpen() && $('#title-textarea #textbox', d) && txt(d).includes(v.file)) {
      L('resuming the dialog that is already open for ' + v.file);      // e.g. after a failed attempt on the details step
    } else {
      const file = await getFile(date, v.file);
      const input = await openUpload();
      const dt = new DataTransfer(); dt.items.add(file); input.files = dt.files;
      input.dispatchEvent(new Event('change', { bubbles: true }));
      // the dialog shows the file name once the upload has started (this also rules out a stale dialog)
      d = await until(() => { const x = dlg(); return x && $('#title-textarea #textbox', x) && txt(x).includes(v.file) && x; }, 90000, 'details form');
      await sleep(1500);
    }
    await fill(d, v);
    const bad = problems(d, v);
    if (bad.length) throw new Error('form is not as expected: ' + bad.join(', '));
    L('form ok; waiting for the upload and checks');
    let last = '', lastLog = 0, limited = false;
    await until(() => {
      const p = txt($('ytcp-video-upload-progress', d));
      if (p !== last || Date.now() - lastLog > 60000) { last = p; lastLog = Date.now(); L('progress: ' + p.slice(0, 120)); }
      if (/Günlük yükleme sınırına ulaşıldı/i.test(txt(d))) { limited = true; return true; }   // unverified channels: ~10 uploads per 24 h
      return /Kontroller tamamlandı|Sorun bulunmadı|sorun bulundu/i.test(p);
    }, 30 * 60000, 'upload and checks');
    if (limited) {
      S.limit = true;
      const x = $('#ytcp-uploads-dialog-close-button'); if (x) x.click();
      await sleep(1500);
      throw new Error('daily upload limit reached (verify the channel with a phone number, or wait 24 h)');
    }
    for (let i = 0; i < 3; i++) {
      const nb = $('#next-button', d);
      await until(() => nb.getAttribute('aria-disabled') !== 'true', 60000, 'Next button');
      nb.click(); await sleep(1500);
    }
    await until(() => { const r = $('tp-yt-paper-radio-button[name=PUBLIC]', d); return r && r.offsetParent; }, 15000, 'visibility step');
    await choose(d, 'PUBLIC');
    const done = $('#done-button', d);
    await until(() => done.getAttribute('aria-disabled') !== 'true' && /Yayınla/.test(txt(done)), 60000, 'Publish button');
    done.click();
    const a = await until(() => $('ytcp-video-share-dialog a[href^="https://youtube.com/"], ytcp-video-share-dialog a[href^="https://youtu.be/"], ytcp-video-share-dialog a[href^="https://www.youtube.com/"]'), 180000, 'share dialog');
    const m = /(?:shorts\/|youtu\.be\/|watch\?v=)([\w-]{11})/.exec(a.href);
    S.published[v.id] = m ? m[1] : a.href;
    L('PUBLISHED ' + v.id + ' -> ' + S.published[v.id]);
    await closeShare();
    await until(() => !isOpen(), 15000, 'dialog closed');
    await sleep(2500);
  }

  S.run = async (opts = {}) => {
    if (S.running) return 'already running';
    S.running = true; S.stop = false; S.limit = false; S.phase = 'running';
    try {
      await S.ready;
      // typing into Studio's fields only works while this tab is the one shown in the browser pane
      if (document.visibilityState !== 'visible') throw new Error('this tab is in the background: bring the Studio tab to the front and run again');
      const t0 = Date.now(), waitMs = (opts.limitWaitMin || 0) * 60000, gap = (opts.limitRetryMin || 3) * 60000;
      let published = 0;                                     // videos published by this run
      for (const date of opts.dates || []) {
        let man;
        try { man = await (await fetch(BASE + date + '/manifest.json?t=' + Date.now())).json(); }
        catch (e) { L('no manifest for ' + date); continue; }
        for (const v of man.videos) {
          if (S.stop) break;
          if (S.done.includes(v.id) || (opts.skipIds || []).includes(v.id) || (opts.skipTitles || []).includes(v.title)) continue;
          if (opts.only && !opts.only.includes(v.id)) continue;
          S.current = v.id;
          for (;;) {
            try { await one(date, v); S.done.push(v.id); published++; break; }
            catch (e) {
              const retry = S.limit && !S.stop && published === 0 && Date.now() + gap <= t0 + waitMs;
              if (!retry) { S.failed.push(v.id + ': ' + e.message); L('ERROR ' + v.id + ': ' + e.message); S.stop = true; break; }
              L('upload limit: no free slot yet, trying ' + v.id + ' again in ' + gap / 60000 + ' min');
              S.phase = 'waiting for an upload slot'; S.limit = false;
              for (let i = 0; i < gap / 1000 && !S.stop; i++) await sleep(1000);
              S.phase = 'running';
              if (S.stop) break;
            }
          }
        }
      }
      S.phase = S.stop ? 'stopped' : 'finished';
    } catch (e) { S.phase = 'error: ' + e.message; L(S.phase); }
    finally { S.running = false; S.current = null; }
  };
  S.status = () => ({ phase: S.phase, running: S.running, current: S.current, done: S.done, failed: S.failed, published: S.published, limit: S.limit, last: S.log.slice(-5) });
  // keep ms <= 25000 per tool call; while the run is still going the answer is a short summary, the full status comes at the end
  S.wait = async ms => {
    const t0 = Date.now(); while (S.running && Date.now() - t0 < ms) await sleep(500);
    return S.running ? { phase: S.phase, current: S.current, done: S.done.length, failed: S.failed.length, limit: S.limit, last: S.log.slice(-1) } : S.status();
  };
  // titles that are already in Studio (Videos tab + Shorts tab, newest 30 each)
  S.scrape = async () => {
    await S.ready;
    const out = new Set();
    for (const id of ['video-list-uploads-tab', 'video-list-shorts-tab']) {
      const t = document.getElementById(id);
      if (t) { t.click(); await sleep(3500); }
      $$('ytcp-video-row #video-title').forEach(a => out.add(txt(a)));
    }
    const first = document.getElementById('video-list-uploads-tab'); if (first) first.click();
    return [...out];
  };
  return 'bibi uploader ready (v' + S.v + ')';
})();
