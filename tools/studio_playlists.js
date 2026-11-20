// Bibi Buzz TV - puts the day's videos into their YouTube playlists (Studio), one video at a time.
// Run it inside the signed-in studio.youtube.com tab (the channel's content page, tab shown in front), after the uploads.
// It only ADDS: for every video of the given days that is already in Studio it opens the video's edit page, ticks the
// playlists the video belongs to (derived from its id, see targets()), saves, and goes back to the list. It never removes
// a video from a playlist, never creates playlists and never changes any other field. Safe to run again any time.
//
//   __bibiPL.run({ dates: ['2026-11-21'], only: ['d002-L1'], dry: false })   // starts in the background
//   __bibiPL.status() / await __bibiPL.wait(20000)                          // poll (<= 25000 ms per call)
//   __bibiPL.stop = true                                                    // stop after the current video
//
// Playlists (exact titles as created in Studio) and what goes where:
//   long lesson slot L1 animals & nature, L2 first words, L3 numbers/colors/shapes, L4 ABC, L5 speaking  (+ "All Lessons")
//   tale T1 fairy tales (English); T2 Turkish fairy tales; every Short goes to the Shorts playlist.
(() => {
  const BASE = 'https://raw.githubusercontent.com/ebrukuskilic/bibi-buzz-tv/media/';
  if (window.__bibiPL && window.__bibiPL.running) return 'already running';
  const S = window.__bibiPL = { v: 1, running: false, stop: false, phase: 'idle', current: null, log: [], result: {}, failed: [] };
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const txt = e => ((e && (e.innerText || e.textContent)) || '').replace(/\s+/g, ' ').trim();
  const norm = s => (s || '').replace(/\s+/g, ' ').trim();
  const vis = e => { if (!e) return false; const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
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
  // A browser pane that is not displayed produces no animation frames, and Studio's dropdowns only open on the next frame
  // (they would stay "opened" but display:none). While this script runs, frames are replaced by 16 ms timers.
  function shimOn() {
    if (window.__bibiRaf) return;
    window.__bibiRaf = { raf: window.requestAnimationFrame, caf: window.cancelAnimationFrame };
    let id = 1; const pend = {};
    window.requestAnimationFrame = cb => { const k = id++; pend[k] = setTimeout(() => { delete pend[k]; try { cb(performance.now()); } catch (e) { console.error(e); } }, 16); return k; };
    window.cancelAnimationFrame = k => { clearTimeout(pend[k]); delete pend[k]; };
  }
  function shimOff() {
    const o = window.__bibiRaf; if (!o) return;
    window.requestAnimationFrame = o.raf; window.cancelAnimationFrame = o.caf; delete window.__bibiRaf;
  }

  // ---- which playlists a video belongs to -------------------------------------------------------------------------------
  const PL = {
    ALL: 'Learn English for Kids | All Lessons | Bibi Buzz TV',
    ANIMALS: 'Animals & Nature for Kids | Bibi Buzz TV',
    FIRST: 'First Words for Kids: Fruits, Food, Clothes & Toys | Bibi Buzz TV',
    NUMBERS: 'Numbers, Colors & Shapes for Kids | Bibi Buzz TV',
    ABC: 'ABC Alphabet & Letters for Kids | Bibi Buzz TV',
    SPEAK: 'English Speaking for Kids | Say It with Bibi | Bibi Buzz TV',
    SHORTS: 'Kids Shorts | Quick Learning with Bibi | Bibi Buzz TV',
    TALES: 'Fairy Tales & Bedtime Stories for Kids | Bibi Buzz TV',
    TALES_TR: 'Türkçe Masallar | Çocuklar için Masal Videoları | Bibi Buzz TV',
  };
  const SLOT = { 1: 'ANIMALS', 2: 'FIRST', 3: 'NUMBERS', 4: 'ABC', 5: 'SPEAK' };
  function targets(v) {
    const m = /-([LTS])(\d+)$/.exec(v.id || '');
    if (!m) return [];
    if (m[1] === 'S') return [PL.SHORTS];
    if (m[1] === 'T') return [m[2] === '2' ? PL.TALES_TR : PL.TALES];
    return SLOT[m[2]] ? [PL.ALL, PL[SLOT[m[2]]]] : [PL.ALL];
  }
  S.targets = targets;

  // ---- Studio navigation (inside the single page app, no page load: this script stays alive) -------------------------
  const isEdit = () => /\/video\/[\w-]{11}\/edit/.test(location.pathname);
  const rowsNow = () => $$('ytcp-video-row');
  async function toList(kind) {
    if (isEdit()) {
      // Studio's own "Kanal içeriği" arrow when it is there. In a browser pane that is not displayed (no animation frames) the
      // side menu never finishes its change to the video menu, the arrow is never built, and history.back() does the same
      // job - but only for a page this script opened from the list itself: elsewhere it could leave Studio.
      const leave = () => {
        const back = $$('a#back-button').find(vis);
        if (back) back.click();
        else if (S.fromList) history.back();
        else throw new Error('no back button on the edit page (start on the Videos list)');
      };
      leave();
      try { await until(() => !isEdit() && rowsNow().length, 8000, 'video list'); }
      catch (e) {
        if (S.stop) throw e;
        const undo = $$('button[aria-label="Değişiklikleri geri al"]').find(vis);   // unsaved changes keep the page open
        if (undo) { undo.click(); await sleep(1500); }
        if (isEdit()) leave();
        await until(() => !isEdit() && rowsNow().length, 30000, 'video list');
      }
    }
    S.fromList = false;
    const tab = document.getElementById(kind === 'short' ? 'video-list-shorts-tab' : 'video-list-uploads-tab');
    if (tab && tab.getAttribute('aria-selected') !== 'true') { tab.click(); await sleep(3500); }
    await until(() => rowsNow().length, 25000, 'video list (start on the Videos list of the Studio content page)');
    await sleep(800);
  }
  const dlgNow = () => $$('tp-yt-paper-dialog').find(x => vis(x) && $('ytcp-button.done-button', x) && $$('ytcp-checkbox-lit', x).length);
  const dlgOpening = () => $$('tp-yt-paper-dialog').find(x => $('ytcp-button.done-button', x) && (x.opened || x.hasAttribute('opened')));

  async function one(v, dry) {
    const want = targets(v);
    if (!want.length) return 'no playlist rule for this id';
    const kind = v.type === 'short' || /-S\d+$/.test(v.id) ? 'short' : 'long';
    await toList(kind);
    const row = rowsNow().find(r => norm(txt($('#video-title', r))) === norm(v.title));
    if (!row) return 'not in Studio yet';
    const link = $('a#video-title', row) || $('a[href*="/video/"]', row);
    if (!link) throw new Error('no link on the video row');
    S.fromList = true;
    link.click();
    await until(() => isEdit() && $('ytcp-video-metadata-playlists') && $('ytcp-button#save'), 30000, 'edit page');
    await sleep(1500);
    const trig = () => { const p = $('ytcp-video-metadata-playlists'); return p && ($('ytcp-text-dropdown-trigger', p) || $('ytcp-dropdown-trigger', p)); };
    let dlg = null;
    for (let k = 0; k < 3 && !dlg; k++) {
      if (!dlgOpening()) {                                    // a click on an open dropdown would close it again
        const t = trig(); if (!t) throw new Error('playlist selector not found');
        t.scrollIntoView({ block: 'center' }); t.click();
      }
      try { dlg = await until(dlgNow, 15000, 'playlist list'); } catch (e) { if (S.stop) throw e; await sleep(800); }
    }
    if (!dlg) throw new Error('the playlist list did not open');
    await sleep(700);
    const have = [], added = [], missing = [];
    for (const name of want) {
      const cb = $$('ytcp-checkbox-lit', dlg).find(c => norm(txt(c.closest('label') || c.parentElement)) === norm(name));
      if (!cb) { missing.push(name); continue; }
      if (cb.checked) { have.push(name); continue; }
      if (dry) { added.push(name); continue; }
      cb.click(); await sleep(500);
      if (!cb.checked) throw new Error('could not tick: ' + name);
      added.push(name);
    }
    $('ytcp-button.done-button', dlg).click();
    await until(() => !dlgNow(), 10000, 'playlist list closes');
    await sleep(500);
    let res;
    if (dry || !added.length) {
      res = (dry && added.length ? 'would add: ' : added.length ? 'added: ' : 'already in all playlists') + (added.length ? added.join(' + ') : '');
    } else {
      const save = $('ytcp-button#save');
      await until(() => save.getAttribute('aria-disabled') !== 'true', 10000, 'Save enabled');
      save.click();
      await until(() => save.getAttribute('aria-disabled') === 'true', 25000, 'save');
      let toast = 'no confirmation toast';
      try { await until(() => $$('tp-yt-paper-toast').some(e => /Değişiklikler kaydedildi/.test(e.textContent || '')), 8000, 'toast'); toast = 'saved'; } catch (e) { if (S.stop) throw e; }
      res = 'added (' + toast + '): ' + added.join(' + ');
    }
    if (missing.length) res += ' | playlist missing in Studio: ' + missing.join(' + ');
    await sleep(500);
    await toList(kind);
    await sleep(1500);
    return res;
  }

  S.run = async (opts = {}) => {
    if (S.running) return 'already running';
    S.running = true; S.stop = false; S.phase = 'running';
    try {
      await S.ready;
      if (document.visibilityState !== 'visible') throw new Error('this tab is in the background: bring the Studio tab to the front and run again');
      shimOn();
      const jobs = [];
      for (const date of opts.dates || []) {
        let man;
        try { man = await (await fetch(BASE + date + '/manifest.json?t=' + Date.now())).json(); }
        catch (e) { L('no manifest for ' + date); continue; }
        for (const v of man.videos) if (!opts.only || opts.only.includes(v.id)) jobs.push(v);
      }
      for (const v of jobs) {
        if (S.stop) break;
        S.current = v.id;
        try { S.result[v.id] = await one(v, !!opts.dry); L(v.id + ': ' + S.result[v.id]); }
        catch (e) {
          S.result[v.id] = 'failed: ' + e.message; S.failed.push(v.id); L('ERROR ' + v.id + ': ' + e.message);
          if (S.stop) break;
          try { const d = dlgNow(); if (d) { $('ytcp-button.done-button', d).click(); await sleep(800); } await toList(/-S\d+$/.test(v.id) ? 'short' : 'long'); } catch (e2) {}
        }
      }
      S.phase = S.stop ? 'stopped' : 'finished';
    } catch (e) { S.phase = 'error: ' + e.message; L(S.phase); }
    finally { shimOff(); S.running = false; S.current = null; }
  };
  S.status = () => ({ phase: S.phase, running: S.running, current: S.current, failed: S.failed, result: S.result, last: S.log.slice(-5) });
  // keep ms <= 25000 per tool call
  S.wait = async ms => {
    const t0 = Date.now(); while (S.running && Date.now() - t0 < ms) await sleep(500);
    return S.running ? { phase: S.phase, current: S.current, done: Object.keys(S.result).length, failed: S.failed.length, last: S.log.slice(-1) } : S.status();
  };
  return 'bibi playlists ready (v' + S.v + ')';
})();
