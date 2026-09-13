/* Pure research calculations shared by the dashboard and financial regression tests. */
(function (root) {
  'use strict';
  const num = value => value === '' || value === null || value === undefined || !Number.isFinite(Number(value)) ? null : Number(value);
  const pct = (a, b) => b > 0 ? (a / b - 1) * 100 : null;
  function scenario(entry, exit, annualDividend, years, costBps, targetPct) {
    if (![entry, exit, annualDividend, years, costBps, targetPct].every(Number.isFinite) || entry <= 0 || exit < 0 || annualDividend < 0 || years <= 0 || costBps < 0 || costBps >= 10000 || targetPct <= -100) return null;
    const half = costBps / 20000;
    const terminal = exit * (1 - half) + annualDividend * years;
    const ratio = terminal / (entry * (1 + half));
    return {totalPct: (ratio - 1) * 100, annualPct: (Math.pow(ratio, 1 / years) - 1) * 100,
      maxEntry: terminal / (Math.pow(1 + targetPct / 100, years) * (1 + half))};
  }
  function funding(r) {
    const fields = ['cash', 'facilities', 'debtDue', 'stressOcf', 'capex', 'buffer'];
    const values = fields.map(key => num(r[key]));
    if (values.some(value => value === null) || values.some((v, i) => i !== 3 && v < 0)) return null;
    const [cash, facilities, debt, ocf, capex, buffer] = values;
    return cash + facilities + 2 * ocf - debt - capex - buffer;
  }
  function checklist(r, s, today) {
    const missing = [];
    const blocked = [];
    for (const key of ['thesis', 'expectations', 'valuationBasis', 'catalyst', 'falsify', 'exposures', 'fundingNotes']) if (!String(r[key] || '').trim()) missing.push(key);
    if (!/^https:\/\//i.test(r.source || '')) missing.push('official evidence URL');
    if (!/^\d{4}-\d{2}-\d{2}$/.test(r.evidenceDate || '') || !Number.isFinite(Date.parse(r.evidenceDate)) || r.evidenceDate > today) missing.push('valid evidence date');
    else if ((Date.parse(today) - Date.parse(r.evidenceDate)) / 86400000 > 210) missing.push('updated financial evidence');
    if (!/^\d{4}-\d{2}-\d{2}$/.test(r.reviewDate || '') || !Number.isFinite(Date.parse(r.reviewDate)) || r.reviewDate < today) missing.push('future review date');
    if (r.covenants === 'fail' || r.governance === 'fail') blocked.push('Verified covenant/governance concern');
    if (!['pass', 'na'].includes(r.covenants)) missing.push('covenant assessment');
    if (r.governance !== 'pass') missing.push('governance assessment');
    if (r.timeline !== 'pass') missing.push('cash remains sufficient at each maturity date');
    if (!r.currency) missing.push('funding currency');
    const headroom = funding(r);
    if (headroom === null) missing.push('complete funding stress inputs');
    else if (headroom < 0) blocked.push('Funding gap under stress');
    const prices = ['entry', 'bear', 'base', 'bull', 'dividend', 'years', 'costBps'].map(k => num(r[k]));
    const [entry, bear, base, bull, dividend, years, cost] = prices;
    const baseCase = prices.includes(null) ? null : scenario(entry, base, dividend, years, cost, s.annual_target_pct);
    if (!baseCase || bear < 0 || bear > base || base > bull) missing.push('ordered bear ≤ base ≤ bull scenarios');
    else if (baseCase.annualPct < s.annual_target_pct) blocked.push('Base scenario below the annual planning hurdle');
    if (!r.lane || r.lane === 'unclassified_missing_data') missing.push('research lane');
    if (r.lane === 'turnaround_research' && !String(r.turnaround || '').trim()) missing.push('funded turnaround milestones and dilution case');
    if (['cyclical_research', 'sector_specialist'].includes(r.lane) && !String(r.sectorNotes || '').trim()) missing.push('sector-specific or mid-cycle assessment');
    if (r.liquidity !== 'pass') missing.push('liquidity and order-size check');
    return {missing, blocked, headroom, ready: !missing.length && !blocked.length};
  }
  function holdings(book) {
    let cash = book.capital;
    const positions = {};
    for (const fill of book.ledger) {
      const pos = positions[fill.ticker] ||= {units: 0, lane: fill.lane, exposures: fill.exposures || ''};
      if (fill.side === 'BUY') { cash -= fill.units * fill.price + fill.fee; pos.units += fill.units; pos.lane = fill.lane; pos.exposures = fill.exposures; }
      if (fill.side === 'SELL') { cash += fill.units * fill.price - fill.fee; pos.units -= fill.units; }
      if (fill.side === 'DIVIDEND') cash += fill.amount;
      if (fill.side === 'SPLIT') pos.units *= fill.ratio;
    }
    return {cash, positions};
  }
  function valuation(book, marks, today) {
    const {cash, positions} = holdings(book);
    let equity = cash;
    const missing = [];
    for (const [ticker, pos] of Object.entries(positions)) if (pos.units > 1e-8) {
      const mark = marks[ticker];
      if (!mark || !(mark.price > 0) || (Date.parse(today) - Date.parse(mark.date)) / 86400000 > 5) missing.push(ticker);
      else equity += pos.units * mark.price;
    }
    return {cash, positions, equity: missing.length ? null : equity, missing};
  }
  function buyLimit(book, order, price, marks, s, today) {
    const v = valuation(book, marks, today);
    if (v.equity === null) return 'Unpriced/stale positions prevent a complete risk check';
    if (order.units * price + order.fee > v.cash + 1e-8) return 'Insufficient model cash; no leverage';
    const existing = v.positions[order.ticker]?.units || 0;
    const limit = order.lane === 'turnaround_research' ? s.turnaround_position_pct : existing > 0 ? s.max_position_pct : s.initial_position_pct;
    if ((existing + order.units) * price / v.equity * 100 > limit + 1e-8) return `Position exceeds ${limit}% model limit`;
    const count = Object.values(v.positions).filter(p => p.units > 0).length;
    if (!existing && count >= s.max_holdings) return 'Maximum holding count reached';
    let speculative = order.lane === 'turnaround_research' ? order.units * price : 0;
    for (const [ticker, p] of Object.entries(v.positions)) if (p.lane === 'turnaround_research') speculative += p.units * (marks[ticker]?.price || 0);
    if (speculative / v.equity * 100 > s.turnaround_total_pct) return 'Combined turnaround exposure exceeds model limit';
    const turnover = num(marks[order.ticker]?.median_turnover);
    if (turnover === null || turnover < s.minimum_median_turnover_aud) return 'Liquidity is unverified or below the model floor';
    if (order.units * price / turnover * 100 > s.max_order_turnover_pct) return 'Order exceeds the model turnover participation limit';
    return '';
  }
  function settle(book, marks, s, today) {
    // Fills use the first later close actually seen by this browser; never the signal close.
    // Broker fees plus slippage are explicit. This is an illustrative paper ledger only.
    const events = [];
    for (const [ticker, mark] of Object.entries(marks)) for (const action of mark.actions || []) {
      if (action.date <= mark.date && action.date >= book.started && !book.appliedActions.includes(`${ticker}:${action.date}`)) events.push({type: 'action', ticker, date: action.date, action});
    }
    for (const order of book.orders) if (order.status === 'pending') {
      const mark = marks[order.ticker];
      if (mark && mark.date > order.submitted && mark.date <= today && (Date.parse(today) - Date.parse(mark.date)) / 86400000 <= 5) events.push({type: 'order', order, date: mark.date});
    }
    events.sort((a, b) => a.date.localeCompare(b.date) || (a.type === 'action' ? -1 : 1));
    for (const event of events) {
      if (event.type === 'action') {
        const {ticker, date, action} = event;
        const units = holdings({...book, ledger:book.ledger.filter(fill=>fill.date<date)}).positions[ticker]?.units || 0;
        if (units > 0 && action.split > 0) book.ledger.push({side: 'SPLIT', ticker, date, ratio: action.split});
        if (units > 0 && action.dividend > 0) book.ledger.push({side: 'DIVIDEND', ticker, date, amount: units * (action.split || 1) * action.dividend});
        book.appliedActions.push(`${ticker}:${date}`);
        continue;
      }
      const o = event.order;
      const price = marks[o.ticker].price * (1 + (o.side === 'BUY' ? 1 : -1) * o.slippageBps / 10000);
      let reason = o.side === 'BUY' ? buyLimit(book, o, price, marks, s, today) : (holdings(book).positions[o.ticker]?.units || 0) < o.units ? 'Insufficient model shares' : '';
      if (!reason && o.side === 'BUY' && o.review && !checklist({...o.review,entry:price},s,today).ready) reason = 'Saved research is due for review or the fill price fails the valuation hurdle';
      if (reason) { o.status = 'rejected'; o.result = reason; }
      else { book.ledger.push({...o, date: event.date, price}); o.status = 'filled'; o.result = `${event.date} at ${price.toFixed(4)}`; }
    }
    book.ledger.sort((a,b)=>a.date.localeCompare(b.date) || ((a.side==='SPLIT'?0:a.side==='DIVIDEND'?1:2)-(b.side==='SPLIT'?0:b.side==='DIVIDEND'?1:2)));
    return book;
  }
  const api = {num, pct, scenario, funding, checklist, holdings, valuation, buyLimit, settle};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  root.ContrarianResearch = api;
})(typeof window !== 'undefined' ? window : globalThis);
