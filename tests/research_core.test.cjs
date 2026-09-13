const {test} = require('node:test');
const assert = require('node:assert/strict');
const C = require('../assets/research_core.js');
const S = require('../config/research_settings.json');
const book = () => ({capital:50000,started:'2026-09-01',ledger:[],orders:[],appliedActions:[],nav:[]});

test('A$1,000 becomes A$1,200 at 20% in one year; three-year recovery is not 20% annually',()=>{
  assert.ok(Math.abs(C.scenario(1000,1200,0,1,0,20).annualPct-20)<1e-8);
  assert.ok(Math.abs(C.scenario(70,100,0,3,0,20).annualPct-12.6248)<.001);
  assert.ok(Math.abs(C.scenario(70,100,0,3,0,20).maxEntry-57.87037)<.001);
});
test('costs reduce returns and funding gaps cannot become passes',()=>{
  assert.ok(C.scenario(100,120,0,1,40,20).annualPct<20);
  assert.equal(C.funding({cash:10,facilities:0,debtDue:20,stressOcf:-2,capex:1,buffer:2}),-17);
  assert.equal(C.funding({cash:10}),null);
  assert.equal(C.checklist({},S,'2026-09-13').ready,false);
  assert.equal(C.scenario(0,100,0,1,0,20),null);
});
test('a documented case can complete, but failed covenants override attractive upside',()=>{
  const r={thesis:'Temporary disruption',expectations:'Margins recover with evidence',valuationBasis:'Normalised cash flow',catalyst:'Contract renewal',falsify:'Contract lost',exposures:'Domestic demand',fundingNotes:'Dated debt schedule',source:'https://www.asx.com.au/example',evidenceDate:'2026-09-01',reviewDate:'2026-10-01',covenants:'pass',governance:'pass',timeline:'pass',currency:'AUD millions',cash:20,facilities:0,debtDue:5,stressOcf:2,capex:3,buffer:2,entry:10,bear:7,base:15,bull:20,dividend:0,years:1,costBps:40,lane:'core_research',liquidity:'pass'};
  assert.equal(C.checklist(r,S,'2026-09-13').ready,true);
  r.covenants='fail';assert.equal(C.checklist(r,S,'2026-09-13').ready,false);
  assert.equal(C.checklist(r,S,'2026-09-13').blocked.length,1);
});
test('an exact 20% hurdle is not rejected by floating-point rounding',()=>{
  const result=C.checklist({entry:1000,bear:800,base:1200,bull:1500,dividend:0,years:1,costBps:0},S,'2026-09-13');
  assert.ok(!result.blocked.some(reason=>reason.includes('hurdle')));
});
test('model cannot spend beyond cash or initial concentration limit',()=>{
  const b=book(), marks={'AAA.AX':{price:10,date:'2026-09-13',median_turnover:1000000}};
  const order={ticker:'AAA.AX',units:300,fee:5,lane:'core_research'};
  assert.match(C.buyLimit(b,order,10,marks,S,'2026-09-13'),/5%/);
  order.units=100;assert.equal(C.buyLimit(b,order,10,marks,S,'2026-09-13'),'');
  order.units=10000;assert.match(C.buyLimit(b,order,10,marks,S,'2026-09-13'),/cash/);
});
test('paper orders cannot fill at a price preceding the recorded decision',()=>{
  const b=book();b.orders.push({id:'1',ticker:'AAA.AX',side:'BUY',units:100,fee:5,slippageBps:20,lane:'core_research',submitted:'2026-09-01',status:'pending'});
  C.settle(b,{'AAA.AX':{price:10,date:'2026-09-01',actions:[]}},S,'2026-09-01');
  assert.equal(b.ledger.length,0);
  C.settle(b,{'AAA.AX':{price:10,date:'2026-09-02',actions:[],median_turnover:1000000}},S,'2026-09-02');
  assert.equal(b.ledger.length,1);assert.equal(b.ledger[0].price,10.02);
  assert.equal(C.holdings(b).cash,48993);
});
test('missing held-stock prices suppress the entire portfolio return',()=>{
  const b=book();b.ledger.push({side:'BUY',ticker:'AAA.AX',units:100,price:10,fee:5});
  assert.equal(C.valuation(b,{},'2026-09-13').equity,null);
  assert.deepEqual(C.valuation(b,{},'2026-09-13').missing,['AAA.AX']);
});
test('dividends are credited once and not to a same-day new purchase',()=>{
  const b=book();b.ledger.push({side:'BUY',ticker:'AAA.AX',units:100,price:10,fee:5,date:'2026-09-01'});
  const marks={'AAA.AX':{price:10,date:'2026-09-03',actions:[{date:'2026-09-01',dividend:1,split:0},{date:'2026-09-02',dividend:.5,split:0}]}};
  C.settle(b,marks,S,'2026-09-03');C.settle(b,marks,S,'2026-09-03');
  assert.equal(b.ledger.filter(f=>f.side==='DIVIDEND').length,1);
  assert.equal(C.holdings(b).cash,49045);
});
test('split events adjust held quantities without manufacturing cash',()=>{
  const b=book();b.ledger.push({side:'BUY',ticker:'AAA.AX',units:100,price:10,fee:5,date:'2026-09-01'});
  C.settle(b,{'AAA.AX':{price:5,date:'2026-09-03',actions:[{date:'2026-09-02',dividend:0,split:2}]}},S,'2026-09-03');
  assert.equal(C.holdings(b).positions['AAA.AX'].units,200);
  assert.equal(C.holdings(b).cash,48995);
});
test('calendar-year targets distinguish complete years, partial years and missing boundaries',()=>{
  const b=book();b.nav=[{date:'2026-12-31',equity:60000},{date:'2027-12-31',equity:72000},{date:'2028-09-13',equity:73000}];
  const rows=C.calendarReturns(b,'2028-09-13');
  assert.equal(rows[0].complete,false);assert.equal(rows[1].complete,true);
  assert.ok(Math.abs(rows[1].returnPct-20)<1e-8);assert.equal(rows[2].complete,false);
  b.nav.shift();assert.equal(C.calendarReturns(b,'2028-09-13')[1].returnPct,null);
});
