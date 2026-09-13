(function () {
  'use strict';
  const element = document.getElementById('research-data');
  if (!element) return;
  const data = JSON.parse(element.textContent), s = data.settings, C = window.ContrarianResearch;
  const byId = id => document.getElementById(id);
  const form = byId('research-form');
  const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[c]));
  const money = value => value === null ? 'Unavailable' : new Intl.NumberFormat('en-AU', {style:'currency',currency:'AUD',maximumFractionDigits:2}).format(value);
  const percent = value => value === null || !Number.isFinite(value) ? 'Not available' : `${value.toFixed(2)}%`;
  const today = () => {
    const parts = new Intl.DateTimeFormat('en-AU', {timeZone:'Australia/Perth',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date());
    const get = type => parts.find(p => p.type === type).value;
    return `${get('year')}-${get('month')}-${get('day')}`;
  };
  const storageKey = 'contrarian-research-v1';
  const blank = () => ({schema:1, records:{}, reviews:[], book:{capital:s.model_capital_aud, started:today(), ledger:[],orders:[],appliedActions:[],nav:[]}});
  const normalise = value => {
    const ticker = String(value).trim().toUpperCase();
    return /^[A-Z0-9]{2,5}(\.AX)?$/.test(ticker) ? ticker.endsWith('.AX') ? ticker : `${ticker}.AX` : '';
  };
  let state = blank(), storageOk = true, corrupt = false, dirty = false;
  function validate(value) {
    if (!value || value.schema !== 1 || !value.records || typeof value.records !== 'object' || Array.isArray(value.records) || !Array.isArray(value.reviews)) throw Error('Unsupported notebook format');
    for (const [ticker, record] of Object.entries(value.records)) if (normalise(ticker) !== ticker || !record || typeof record !== 'object') throw Error('Invalid company record');
    const b = value.book;
    if (!b || !Number.isFinite(b.capital) || b.capital <= 0 || !/^\d{4}-\d{2}-\d{2}$/.test(b.started)) throw Error('Invalid model capital or start date');
    for (const key of ['ledger','orders','appliedActions','nav']) if (!Array.isArray(b[key])) throw Error('Incomplete paper portfolio');
    if (b.ledger.length > 100000 || b.orders.length > 10000) throw Error('Notebook exceeds supported size');
    for (const f of [...b.ledger, ...b.orders]) {
      if (!normalise(f.ticker) || !['BUY','SELL','DIVIDEND','SPLIT'].includes(f.side)) throw Error('Invalid paper entry');
      if (['BUY','SELL'].includes(f.side) && (!(f.units > 0) || !Number.isFinite(f.units) || !(f.fee >= 0) || !Number.isFinite(f.fee))) throw Error('Invalid units or fee');
      if (f.side === 'DIVIDEND' && (!(f.amount >= 0) || !Number.isFinite(f.amount))) throw Error('Invalid distribution');
      if (f.side === 'SPLIT' && (!(f.ratio > 0) || !Number.isFinite(f.ratio))) throw Error('Invalid split');
    }
    for (const f of b.ledger) if (['BUY','SELL'].includes(f.side) && (!(f.price > 0) || !Number.isFinite(f.price))) throw Error('Invalid fill price');
    for (const o of b.orders) if (!['pending','filled','cancelled','rejected'].includes(o.status) || !/^\d{4}-\d{2}-\d{2}$/.test(o.submitted) || !(o.slippageBps >= 0) || o.slippageBps > 1000) throw Error('Invalid pending order');
    return value;
  }
  try { const stored = localStorage.getItem(storageKey); if (stored) state = validate(JSON.parse(stored)); }
  catch (error) { storageOk = false; corrupt = true; byId('research-storage').textContent = 'Stored data could not be read. It has not been overwritten. Import a valid backup to recover, or export current session notes.'; }
  function persist() {
    if (corrupt) return false;
    try { localStorage.setItem(storageKey, JSON.stringify(state)); storageOk = true; byId('research-storage').textContent = 'Saved in this browser. Export a backup to keep your work.'; return true; }
    catch (error) { storageOk = false; byId('research-storage').textContent = 'Browser storage is unavailable or full. Export now; this session is not safely saved.'; return false; }
  }
  function readForm() { return Object.fromEntries(new FormData(form)); }
  function renderCalculations() {
    const r = readForm(), check = C.checklist(r,s,today());
    const scenarioRows = ['bear','base','bull'].map(name => {
      const keys = ['entry',name,'dividend','years','costBps'];
      const values = keys.map(key => C.num(r[key]));
      const result = values.includes(null) ? null : C.scenario(...values,s.annual_target_pct);
      return `<tr><td>${name[0].toUpperCase()+name.slice(1)}</td><td>${percent(result?.totalPct ?? null)}</td><td>${percent(result?.annualPct ?? null)}</td><td>${money(result?.maxEntry ?? null)}</td></tr>`;
    }).join('');
    const status = check.blocked.length ? 'Research blocked by your inputs' : check.ready ? 'Checklist complete — decision remains manual' : 'Required information is incomplete';
    byId('research-calculation').innerHTML = `<div class="table-wrap"><table><thead><tr><th>Scenario</th><th>Total return</th><th>Annualised planning return</th><th>Max entry for 20% annualised</th></tr></thead><tbody>${scenarioRows}</tbody></table></div><div class="checklist-result ${check.blocked.length?'blocked':check.ready?'complete':''}"><strong>${status}</strong><p>24-month aggregate funding headroom: ${check.headroom===null?'Unknown':escape(check.headroom.toLocaleString('en-AU'))} ${escape(r.currency)}.</p>${check.blocked.length?`<p>${escape(check.blocked.join('; '))}</p>`:''}${check.missing.length?`<p>Still needed: ${escape(check.missing.join('; '))}.</p>`:''}</div>`;
  }
  function loadCompany(value) {
    const ticker = normalise(value);
    if (!ticker) { byId('research-storage').textContent = 'Enter a valid ASX ticker.'; return; }
    // Keep in-progress notes when moving to another company, without marking them reviewed.
    if (dirty) {
      const current = readForm(), key = normalise(form.dataset.loadedTicker || '');
      if (key) { state.records[key] = {...current, ticker:key, reviewedAt:state.records[key]?.reviewedAt || ''}; persist(); }
    }
    form.reset();
    const signal = data.signals.find(row => row.ticker === ticker) || {};
    const r = state.records[ticker] || {ticker, lane:signal.research_lane || 'unclassified_missing_data', entry:data.marks[ticker]?.price || signal.last_price || '', years:1, costBps:s.simulation_round_trip_cost_bps};
    for (const input of form.elements) if (input.name && r[input.name] !== undefined) input.value = r[input.name];
    form.dataset.loadedTicker = ticker;
    dirty = false;
    byId('research-notebook').open = true;
    renderCalculations();
  }
  document.querySelectorAll('[data-research-ticker]').forEach(button => button.addEventListener('click', () => { loadCompany(button.dataset.researchTicker); byId('research').scrollIntoView({behavior:'smooth',block:'start'}); }));
  byId('research-load').addEventListener('click', () => loadCompany(form.elements.ticker.value));
  form.addEventListener('input', () => { dirty = true; renderCalculations(); });
  form.addEventListener('submit', event => {
    event.preventDefault();
    const r = readForm(), ticker = normalise(r.ticker);
    if (!ticker) { byId('research-storage').textContent = 'Enter a valid ASX ticker before saving.'; return; }
    if (form.dataset.loadedTicker && ticker !== form.dataset.loadedTicker) { byId('research-storage').textContent = 'Load this company before saving so another company’s thesis is not copied accidentally.'; return; }
    r.ticker = ticker; r.reviewedAt = new Date().toISOString();
    state.records[ticker] = r; state.reviews.push({...r}); form.dataset.loadedTicker = ticker;
    dirty = false; persist(); renderCalculations(); renderPortfolio();
  });
  function captureDraft() {
    if (!dirty) return;
    const r = readForm(), ticker = normalise(form.dataset.loadedTicker || r.ticker);
    if (ticker) state.records[ticker] = {...r, ticker, reviewedAt:state.records[ticker]?.reviewedAt || ''};
  }
  byId('research-export').addEventListener('click', () => {
    captureDraft();
    const blob = new Blob([JSON.stringify(state,null,2)], {type:'application/json'}), url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href=url; a.download=`research-notebook-${today()}.json`; a.click(); setTimeout(()=>URL.revokeObjectURL(url),1000);
  });
  byId('research-import').addEventListener('change', async event => {
    const file = event.target.files[0]; if (!file) return;
    try {
      if (file.size > 10000000) throw Error('File must be smaller than 10 MB');
      const incoming = validate(JSON.parse(await file.text()));
      if (!window.confirm('Replace this browser’s notebook and paper portfolio with the imported backup? Export current work first if needed.')) return;
      state = incoming; corrupt = false; dirty = false; persist();
      form.reset(); form.dataset.loadedTicker=''; renderCalculations(); renderPortfolio();
    } catch (error) { byId('research-storage').textContent=`Import failed: ${error.message}. Existing work was kept.`; }
    event.target.value='';
  });
  function renderPortfolio() {
    const b = state.book, v = C.valuation(b,data.marks,today());
    if (v.equity !== null) {
      const sample = {date:today(),equity:v.equity};
      if (b.nav.at(-1)?.date === sample.date) b.nav[b.nav.length-1] = sample; else b.nav.push(sample);
    }
    const peak = Math.max(b.capital,...b.nav.map(n=>n.equity));
    const dd = v.equity===null?null:C.pct(v.equity,peak);
    const currentRows = Object.entries(v.positions).filter(([,p])=>p.units>1e-8).map(([ticker,p]) => `<tr><td>${escape(ticker)}</td><td>${p.units.toFixed(3)}</td><td>${money(data.marks[ticker]?p.units*data.marks[ticker].price:null)}</td><td>${escape(p.lane)}</td><td>${escape(data.marks[ticker]?.date || 'Missing')}</td></tr>`).join('');
    const pending = b.orders.slice().reverse().map(o=>`<tr><td>${escape(o.submitted)}</td><td>${escape(o.ticker)}</td><td>${escape(o.side)} ${o.units}</td><td>${escape(o.status)} ${escape(o.result || '')}</td><td>${o.status==='pending'?`<button type="button" class="paper-cancel" data-cancel-order="${escape(o.id)}">Cancel</button>`:''}</td></tr>`).join('');
    const fills = b.ledger.slice().reverse().slice(0,50).map(f=>`<tr><td>${escape(f.date)}</td><td>${escape(f.ticker)}</td><td>${escape(f.side)}</td><td>${f.side==='DIVIDEND'?money(f.amount):f.side==='SPLIT'?`${f.ratio}×`:`${f.units} @ ${money(f.price)} + ${money(f.fee)} fee`}</td></tr>`).join('');
    const risks = [];
    const exposures = {};
    let turnaround=0;
    for (const [ticker,p] of Object.entries(v.positions)) if (p.units>0 && v.equity) {
      const value = p.units*(data.marks[ticker]?.price||0), weight=value/v.equity*100;
      if (weight>s.max_position_pct || (p.lane==='turnaround_research' && weight>s.turnaround_position_pct)) risks.push(`${ticker} exceeds its review ceiling (${weight.toFixed(1)}%)`);
      if (p.lane==='turnaround_research') turnaround+=weight;
      for (const tag of String(p.exposures||'').toLowerCase().split(',').map(t=>t.trim()).filter(Boolean)) exposures[tag]=(exposures[tag]||0)+weight;
    }
    if (turnaround>s.turnaround_total_pct) risks.push('Combined turnaround allocation exceeds its ceiling');
    for (const [tag,weight] of Object.entries(exposures)) if (weight>s.shared_exposure_review_pct) risks.push(`${tag}: ${weight.toFixed(1)}% shared exposure needs review`);
    const overdue = Object.entries(state.records).filter(([,r])=>r.reviewDate && r.reviewDate<today()).map(([ticker])=>ticker);
    byId('paper-results').innerHTML = `<div class="research-summary"><div><strong>${money(v.equity)}</strong><span>model equity including cash</span></div><div><strong>${money(v.cash)}</strong><span>uninvested cash</span></div><div><strong>${percent(v.equity===null?null:C.pct(v.equity,b.capital))}</strong><span>since ${escape(b.started)} · not annualised</span></div><div><strong>${percent(dd)}</strong><span>current drawdown from observed peak</span></div></div><p>First-year ambition: ${money(b.capital*1.2)}. Years below 20% count as missed targets; do not extrapolate short results.</p>${v.missing.length?`<p class="form-message">Prices missing or stale: ${escape(v.missing.join(', '))}. Complete performance is unavailable.</p>`:''}${risks.length?`<p class="form-message">Exposure review: ${escape(risks.join('; '))}.</p>`:''}${overdue.length?`<p class="form-message">Research reviews overdue: ${escape(overdue.join(', '))}.</p>`:''}<div class="table-wrap"><table><thead><tr><th>Company</th><th>Shares</th><th>Value</th><th>Lane</th><th>Price date</th></tr></thead><tbody>${currentRows || '<tr><td colspan="5">No paper holdings. All model capital remains in cash.</td></tr>'}</tbody></table></div><details><summary>Paper orders and fills</summary><div class="ledger"><table><thead><tr><th>Submitted</th><th>Company</th><th>Order</th><th>Status</th><th>Action</th></tr></thead><tbody>${pending}</tbody></table><table><thead><tr><th>Fill / event date</th><th>Company</th><th>Type</th><th>Details</th></tr></thead><tbody>${fills}</tbody></table></div></details>`;
    byId('paper-results').querySelectorAll('[data-cancel-order]').forEach(button=>button.addEventListener('click',()=>{const order=b.orders.find(o=>o.id===button.dataset.cancelOrder);if(order)order.status='cancelled';persist();renderPortfolio();}));
  }
  byId('paper-order').addEventListener('click',()=>{
    const ticker=normalise(form.elements.ticker.value), r=state.records[ticker], b=state.book;
    const status=byId('paper-status');
    const units=C.num(byId('paper-units').value), fee=C.num(byId('paper-fee').value), slippage=C.num(byId('paper-slippage').value);
    const side=byId('paper-side').value, reason=byId('paper-reason').value.trim();
    if (!ticker || !data.marks[ticker]) {status.textContent='A fresh tracked ticker is required for a paper order.';return;}
    if (!Number.isInteger(units) || units<=0 || fee===null || fee<0 || slippage===null || slippage<0 || slippage>1000 || !reason) {status.textContent='Enter whole shares, non-negative fees/slippage (maximum 1,000 bps) and a decision reason.';return;}
    if (b.orders.some(o=>o.status==='pending')) {status.textContent='Wait for or cancel the pending order before queuing another; this avoids spending reserved cash twice.';return;}
    if (side==='BUY' && (!r || dirty || !r.reviewedAt || !C.checklist(r,s,today()).ready)) {status.textContent='Complete and save the research checklist before a paper purchase.';return;}
    const lastBuy=b.ledger.filter(f=>f.ticker===ticker&&f.side==='BUY').at(-1);
    if (side==='BUY' && lastBuy && r.reviewedAt<=lastBuy.reviewedAt) {status.textContent='Save a new dated review before adding; a falling price alone is insufficient.';return;}
    if (side==='SELL' && (C.holdings(b).positions[ticker]?.units||0)<units) {status.textContent='The model does not hold enough shares.';return;}
    const order={id:crypto.randomUUID(),ticker,side,units,fee,slippageBps:slippage,submitted:today(),status:'pending',reason,lane:r?.lane||'',exposures:r?.exposures||'',reviewedAt:r?.reviewedAt||'',review:r?{...r}:null};
    if (side==='BUY') {
      const error=C.buyLimit(b,order,data.marks[ticker].price*(1+slippage/10000),data.marks,s,today());
      if (error) {status.textContent=error;return;}
    }
    b.orders.push(order);persist();status.textContent='Paper order queued. Reopen after a later market close to observe a fill; cash and position limits are checked again.';renderPortfolio();
  });
  if (!corrupt) { C.settle(state.book,data.marks,s,today()); persist(); }
  renderCalculations(); renderPortfolio();
  window.addEventListener('beforeunload',event=>{if(dirty || !storageOk){event.preventDefault();event.returnValue='';}});
})();
