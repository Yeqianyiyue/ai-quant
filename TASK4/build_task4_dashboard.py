# -*- coding: utf-8 -*-
"""生成 李明凯+TASK4_交互式.html：
内嵌 中际旭创(task2) 与 中兴通讯(TASK3) 数据，用 Chart.js 绘图；
顶部滑块自由调节 入场通道/出场通道/ATR/止损倍数/交易成本，下拉切换股票类型，
实时重算并绘制：价格+高低点通道+买卖信号、ATR、净值对比、累计收益柱状图、量化指标表。
海龟策略逻辑（通道/ATR/信号/止损/回测）在 JS 中与 Notebook 保持完全一致。"""
import pandas as pd
import json
import os
HERE = os.path.dirname(os.path.abspath(__file__))

def _norm(d):
    d = str(d)
    return d if '-' in d else f"{d[:4]}-{d[4:6]}-{d[6:8]}"

# —— 中际旭创（强趋势样本）——
df_zj = pd.read_csv(os.path.join(HERE, '..', 'task2', '中际旭创_日度交易数据.csv'))
df_zj['trade_date'] = df_zj['trade_date'].astype(str)
data_zj = [{'d': _norm(d), 'o': float(o), 'h': float(h), 'l': float(low), 'c': float(c)}
           for d, o, h, low, c in zip(df_zj['trade_date'], df_zj['open'], df_zj['high'], df_zj['low'], df_zj['close'])]

# —— 中兴通讯（震荡/弱趋势样本）——
df_zx = pd.read_csv(os.path.join(HERE, '中兴通讯_日度交易数据.csv'))
df_zx['trade_date'] = df_zx['trade_date'].astype(str)
data_zx = [{'d': _norm(d), 'o': float(o), 'h': float(h), 'l': float(low), 'c': float(c)}
           for d, o, h, low, c in zip(df_zx['trade_date'], df_zx['open'], df_zx['high'], df_zx['low'], df_zx['close'])]

zj_json = json.dumps(data_zj, ensure_ascii=False)
zx_json = json.dumps(data_zx, ensure_ascii=False)
zj_range = f"{df_zj['trade_date'].iloc[0]} ~ {df_zj['trade_date'].iloc[-1]}（{len(df_zj)} 日）"
zx_range = f"{df_zx['trade_date'].iloc[0]} ~ {df_zx['trade_date'].iloc[-1]}（{len(df_zx)} 日）"

TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>海龟策略 · 交互式回测（中际旭创 / 中兴通讯）</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
<style>
  * { box-sizing: border-box; }
  body { font-family: "Microsoft YaHei","SimHei","PingFang SC",sans-serif; margin:0; background:#f5f7fa; color:#1e293b; }
  header { background:#185FA5; color:#fff; padding:16px 24px; }
  header h1 { margin:0; font-size:20px; font-weight:600; }
  header p { margin:4px 0 0; font-size:13px; opacity:.85; }
  .wrap { max-width:1280px; margin:0 auto; padding:20px; }
  .panel { background:#fff; border:1px solid #e2e8f0; border-radius:12px; padding:18px 20px; margin-bottom:20px; }
  .controls { display:flex; flex-wrap:wrap; gap:22px 30px; align-items:flex-end; }
  .ctrl { display:flex; flex-direction:column; gap:6px; min-width:210px; }
  .ctrl label { font-size:13px; font-weight:500; }
  .ctrl .val { color:#185FA5; font-weight:600; }
  input[type=range] { width:210px; }
  select { font-size:13px; padding:5px 8px; border-radius:6px; border:1px solid #cbd5e1; }
  table { border-collapse:collapse; width:100%; font-size:13px; }
  th,td { border:1px solid #e2e8f0; padding:8px 10px; text-align:right; }
  th { background:#f1f5f9; }
  td.metric { text-align:left; font-weight:500; }
  .legend-note { font-size:12px; color:#64748b; margin-top:8px; }
  .chart-title { font-size:15px; font-weight:600; margin:0 0 10px; color:#1e293b; }
  .panel h2 { font-size:17px; margin:0 0 12px; color:#185FA5; }
  .panel h2 small { font-size:13px; color:#64748b; font-weight:400; }
  .intro h3 { font-size:14px; margin:16px 0 6px; color:#1e293b; }
  .intro p, .intro li { font-size:13px; line-height:1.75; color:#334155; margin:6px 0; }
  .intro ul { margin:6px 0; padding-left:22px; }
  .intro b { color:#0f172a; }
  .cap { font-size:12px; color:#64748b; margin:0 0 12px; }
  .chart-legend { display:flex; flex-wrap:wrap; gap:6px 18px; margin-top:10px; font-size:13px; color:#1e293b; }
  .legend-item { display:inline-flex; align-items:center; gap:6px; }
  .legend-line { display:inline-block; width:26px; height:0; border-top-width:3px; border-top-style:solid; }
  .legend-tri { font-size:14px; line-height:1; }
  canvas { max-height:430px; }
  .data-info { background:#e3f2fd; padding:14px 16px; border-radius:8px; margin-bottom:14px; font-size:13px; }
</style>
</head>
<body>
<header>
  <h1>海龟策略（Turtle Trading）· 交互式回测</h1>
  <p>拖动滑块自由调节 入场通道 / 出场通道 / ATR / 止损倍数 / 交易成本，下拉切换股票类型，实时重算价格+通道+买卖信号、ATR、净值与全部量化指标。</p>
</header>
<div class="wrap">

  <div class="panel intro">
    <h2>一、海龟策略核心思想与关键优势</h2>
    <p><b>核心思想：</b>1983 年 Richard Dennis 与 William Eckhardt 设计的<b>完整趋势跟踪系统</b>。不预测顶底，只在价格<b>突破前期高低点通道</b>时顺势入场，赚"已发生趋势延续"的钱。原版含两套系统：<b>S1</b>（入场 20 日 / 出场 10 日，本看板默认）、<b>S2</b>（入场 55 日 / 出场 20 日）。辅以 <b>ATR 波动性头寸管理</b>（波动大则单笔头寸小）与 <b>2×ATR 硬止损</b>（单笔亏损锁死）。</p>
    <h3>1. 关键优势</h3>
    <ul>
      <li><b>规则化、可复制：</b>完全机械化，无主观判断，避免情绪化交易。</li>
      <li><b>顺势而为：</b>大趋势中能持住仓位，吃满主升 / 主跌段。</li>
      <li><b>波动自适应仓位：</b>ATR 头寸管理让风险敞口随市况自动缩放。</li>
      <li><b>风险前置：</b>2×ATR 硬止损把单笔最大亏损锁死。</li>
      <li><b>正偏分布友好：</b>少数大赢覆盖多数小亏，靠"截断亏损、让利润奔跑"盈利。</li>
    </ul>
    <h3>2. 三个核心概念</h3>
    <ul>
      <li><b>高低点通道（Donchian）：</b>上轨 = n 日最高价 max，下轨 = n 日最低价 min；价格突破上轨→做多，跌破下轨→平多/做空。</li>
      <li><b>平均真实波幅 ATR：</b>TR = max(H−L, |H−C_昨|, |L−C_昨|)，ATR = TR 的 m 日均值（默认 14）。衡量"一天通常波动多少"，是头寸规模与止损距离的标尺。</li>
      <li><b>止损条件：</b>多头止损价 = 入场价 − 止损倍数×ATR（默认 2×）；空头止损价 = 入场价 + 止损倍数×ATR；触及即离场。</li>
    </ul>
  </div>

  <div class="panel">
    <h2>二、核心参数（拖动滑块实时重算）</h2>
    <div class="controls">
      <div class="ctrl">
        <label>入场通道周期：<span class="val" id="entryVal">20</span> 日</label>
        <input type="range" id="entrySlider" min="5" max="60" step="1" value="20"/>
      </div>
      <div class="ctrl">
        <label>出场通道周期：<span class="val" id="exitVal">10</span> 日</label>
        <input type="range" id="exitSlider" min="5" max="60" step="1" value="10"/>
      </div>
      <div class="ctrl">
        <label>ATR 周期：<span class="val" id="atrVal">14</span> 日</label>
        <input type="range" id="atrSlider" min="5" max="40" step="1" value="14"/>
      </div>
      <div class="ctrl">
        <label>止损倍数：<span class="val" id="stopVal">2.0</span> ×ATR</label>
        <input type="range" id="stopSlider" min="0.5" max="5" step="0.5" value="2"/>
      </div>
      <div class="ctrl">
        <label>单边交易成本：<span class="val" id="costVal">0.030</span> %</label>
        <input type="range" id="costSlider" min="0" max="0.1" step="0.001" value="0.03"/>
      </div>
      <div class="ctrl">
        <label>股票类型</label>
        <select id="stockSel">
          <option value="zj">中际旭创（300308.SZ·强趋势）</option>
          <option value="zx">中兴通讯（000063.SZ·震荡/弱趋势）</option>
        </select>
      </div>
    </div>
    <div class="data-info" id="dataInfo"></div>
    <div class="legend-note">绿▲=买入(开多)，红▼=卖出(平多 / 开空)。为避免未来函数，通道与 ATR 均用"昨日值"触发信号。本看板同时重算两档成本：0 成本 与 所选交易成本。</div>
  </div>

  <div class="panel">
    <h2 id="stockTitle">价格 + 高低点通道 + 买卖信号</h2>
    <h3 class="chart-title">股价、入/出场通道与买卖信号 <span id="pPeriod"></span></h3>
    <canvas id="priceChart"></canvas>
    <div class="chart-legend" id="priceLegend"></div>

    <h3 class="chart-title" style="margin-top:18px;">平均真实波幅 ATR <span id="aPeriod"></span></h3>
    <canvas id="atrChart"></canvas>
    <div class="chart-legend" id="atrLegend"></div>

    <h3 class="chart-title" style="margin-top:18px;">净值对比：策略(0成本) / 策略(成本) / 买入持有 <span id="nPeriod"></span></h3>
    <canvas id="navChart"></canvas>
    <div class="chart-legend" id="navLegend"></div>
    <div class="legend-note">三条净值曲线同参数下对比：蓝=策略(0成本)、红=策略(所选成本)、黑虚线=买入持有。两者之差即交易成本的累计损耗。</div>

    <h3 class="chart-title" style="margin-top:18px;">累计收益率对比 <span id="bPeriod"></span></h3>
    <canvas id="barChart"></canvas>
    <div class="legend-note">三类策略累计收益率对比：长期持有（买入持有）、海龟策略（0 成本）、海龟策略（所选成本）。</div>

    <table id="metricsTable">
      <thead><tr><th class="metric">指标</th><th>策略（0 成本）</th><th id="costHead">策略（成本）</th></tr></thead>
      <tbody></tbody>
    </table>
  </div>

  <div class="panel">
    <h2>三、参数调节与适应场景总结</h2>
    <p class="cap">海龟法则是一套<b>有条件有效</b>的趋势跟踪系统。通过上方滑块切换股票类型与通道周期，可直观观察：强趋势股（中际旭创）在趋势延续时海龟能持住主升段、接近甚至跑赢买入持有；而在震荡 / 弱趋势股（中兴通讯）上，高低点通道频繁被假突破，多空信号反复翻转（whipsaw），交易次数激增、胜率下降，累计回报常落后于买入持有乃至亏损。</p>
    <ul>
      <li><b>① 强趋势市是海龟的"主场"：</b>价格持续突破前高，系统反复触发多头并"让利润奔跑"，能吃掉大部分主升段；但单边牛市里也常因短期回调触发出场而少量踏空、产生换手成本。</li>
      <li><b>② 震荡 / 弱趋势市明显吃力：</b>价格在区间来回，通道被反复假突破，信号翻转频繁，正是趋势跟踪策略的固有弱点——没有趋势就没有超额收益。</li>
      <li><b>③ 参数敏感，需匹配波动节奏：</b>入场周期越短越灵敏但假信号越多；越长越平滑但越滞后、易错过趋势前半段。同一套参数在不同股票 / 年份差异巨大，须做样本外稳健性检验、警惕过拟合。</li>
      <li><b>④ 波动头寸 + 硬止损是"活下来"的关键：</b>2×ATR 止损把单笔最大亏损锁死；但止损在震荡市也会制造频繁小额亏损（与 ② 共振），故海龟法则必须配合大级别趋势环境才能发挥正偏优势。</li>
      <li><b>⑤ 使用心得：</b>海龟法则价值在于"波动自适应 + 严格止损"的纪律性，而非预测顶底。实战中应结合标的所处市场状态评价，并以参数稳健性检验为前提；在清晰、持续、回调少的趋势里表现出色，在震荡 / 弱趋势里跑输持有。</li>
    </ul>
  </div>
</div>

<script>
Chart.defaults.font.family = '"Microsoft YaHei","SimHei","PingFang SC","Heiti SC",sans-serif';
Chart.defaults.font.size = 13;
Chart.defaults.color = '#1e293b';

const DATA_ZJ = __DATA_ZJ__;
const DATA_ZX = __DATA_ZX__;
const RANGE_ZJ = "__ZJ_RANGE__";
const RANGE_ZX = "__ZX_RANGE__";
const STOCKS = {
  zj: { name:'中际旭创', data: DATA_ZJ },
  zx: { name:'中兴通讯', data: DATA_ZX }
};

// —— 海龟策略（与 Notebook 完全一致的 JS 实现）——
function turtle(data, entryP, exitP, atrP, stopM, cost, allowShort){
  const n = data.length;
  const CLOSE = data.map(x=>x.c), HIGH = data.map(x=>x.h), LOW = data.map(x=>x.l);
  const upperEntry = new Array(n).fill(null), lowerEntry = new Array(n).fill(null);
  const upperExit = new Array(n).fill(null), lowerExit = new Array(n).fill(null);
  for(let i=0;i<n;i++){
    if(i>=entryP){ let mx=-Infinity,mn=Infinity; for(let j=i-entryP+1;j<=i;j++){ if(HIGH[j]>mx)mx=HIGH[j]; if(LOW[j]<mn)mn=LOW[j]; } upperEntry[i]=mx; lowerEntry[i]=mn; }
    if(i>=exitP){ let mx=-Infinity,mn=Infinity; for(let j=i-exitP+1;j<=i;j++){ if(HIGH[j]>mx)mx=HIGH[j]; if(LOW[j]<mn)mn=LOW[j]; } upperExit[i]=mx; lowerExit[i]=mn; }
  }
  for(let i=n-1;i>0;i--){ upperEntry[i]=upperEntry[i-1]; lowerEntry[i]=lowerEntry[i-1]; upperExit[i]=upperExit[i-1]; lowerExit[i]=lowerExit[i-1]; }
  upperEntry[0]=null; lowerEntry[0]=null; upperExit[0]=null; lowerExit[0]=null;
  const tr = new Array(n).fill(0), atrRaw = new Array(n).fill(null);
  for(let i=0;i<n;i++){ const pc = i>0?CLOSE[i-1]:CLOSE[i]; tr[i]=Math.max(HIGH[i]-LOW[i], Math.abs(HIGH[i]-pc), Math.abs(LOW[i]-pc)); }
  for(let i=0;i<n;i++){ if(i>=atrP-1){ let s=0; for(let j=i-atrP+1;j<=i;j++) s+=tr[j]; atrRaw[i]=s/atrP; } }
  const atr = new Array(n).fill(null);
  for(let i=n-1;i>0;i--) atr[i]=atrRaw[i-1];
  atr[0]=null;
  const position = new Array(n).fill(0);
  let pos=0, ep=0, ea=0; const tradeReturns=[];
  for(let i=1;i<n;i++){
    let exited=false;
    if(pos===1){ if(CLOSE[i] <= ep - stopM*ea){ pos=0; exited=true; } else if(lowerExit[i]!==null && CLOSE[i] < lowerExit[i]){ pos=0; exited=true; } }
    else if(pos===-1){ if(CLOSE[i] >= ep + stopM*ea){ pos=0; exited=true; } else if(upperExit[i]!==null && CLOSE[i] > upperExit[i]){ pos=0; exited=true; } }
    if(pos===0 && !exited){
      if(upperEntry[i]!==null && CLOSE[i] > upperEntry[i]){ pos=1; ep=CLOSE[i]; ea=atr[i]; }
      else if(allowShort && lowerEntry[i]!==null && CLOSE[i] < lowerEntry[i]){ pos=-1; ep=CLOSE[i]; ea=atr[i]; }
    }
    if(position[i-1]!==0 && pos===0){ const direction=position[i-1]; tradeReturns.push(direction*(CLOSE[i]/ep - 1) - 2*cost); ep=0; ea=0; }
    position[i]=pos;
  }
  return {position, upperEntry, lowerEntry, upperExit, lowerExit, atr, tradeReturns};
}

function backtest(position, data, cost){
  const n = position.length;
  const CLOSE = data.map(x=>x.c);
  const ret=[]; for(let i=1;i<n;i++) ret.push(CLOSE[i]/CLOSE[i-1]-1);
  const posLag = position.slice(0,n-1);
  const turnover=[]; for(let i=1;i<n;i++) turnover.push(Math.abs(position[i]-position[i-1]));
  const sret=[]; for(let i=0;i<n-1;i++) sret.push(posLag[i]*ret[i]-turnover[i]*cost);
  const nav=new Array(n); nav[0]=1;
  for(let i=1;i<n;i++) nav[i]=nav[i-1]*(1+sret[i-1]);
  return {nav, sret, turnover};
}

function pearson(x,y){
  const n=x.length; const mx=x.reduce((a,b)=>a+b,0)/n, my=y.reduce((a,b)=>a+b,0)/n;
  let num=0,dx=0,dy=0; for(let i=0;i<n;i++){ num+=(x[i]-mx)*(y[i]-my); dx+=(x[i]-mx)**2; dy+=(y[i]-my)**2; }
  return (dx===0||dy===0)?0:num/Math.sqrt(dx*dy);
}
function rank(arr){ const idx=arr.map((v,i)=>[v,i]).sort((a,b)=>a[0]-b[0]); const r=new Array(arr.length); for(let i=0;i<idx.length;i++) r[idx[i][1]]=i+1; return r; }
function spearman(x,y){ return pearson(rank(x), rank(y)); }

function metricsOf(t, data, cost){
  const position = t.position;
  const n = position.length;
  const {nav, sret, turnover} = backtest(position, data, cost);
  const cum = nav[n-1]-1;
  const ann = Math.pow(nav[n-1], 252/(n-1)) - 1;
  let peak=-Infinity, mdd=0; for(const v of nav){ if(v>peak)peak=v; const dd=(peak-v)/peak; if(dd>mdd)mdd=dd; }
  const rs = sret.slice();
  const mean = rs.reduce((a,b)=>a+b,0)/rs.length;
  const variance = rs.reduce((a,b)=>a+(b-mean)*(b-mean),0)/(rs.length-1);
  const std = Math.sqrt(variance);
  const rf_d = 0.025/252;
  const sharpe = (mean - rf_d)/std * Math.sqrt(252);
  const CLOSE = data.map(x=>x.c);
  const mkt=[]; for(let i=1;i<n;i++) mkt.push(CLOSE[i]/CLOSE[i-1]-1);
  const mmean = mkt.reduce((a,b)=>a+b,0)/mkt.length;
  let cov=0, varM=0; for(let i=0;i<mkt.length;i++){ cov+=(rs[i]-mean)*(mkt[i]-mmean); varM+=(mkt[i]-mmean)*(mkt[i]-mmean); }
  cov/=(mkt.length-1); varM/=(mkt.length-1);
  const beta = cov/varM;
  const treynor = (ann - 0.025)/beta;
  const ret=[]; for(let i=1;i<n;i++) ret.push(CLOSE[i]/CLOSE[i-1]-1);
  const sig=[], fwd=[]; for(let t=0;t<n-2;t++){ sig.push(position[t]); fwd.push(ret[t+1]); }
  const mask=[]; for(let i=0;i<sig.length;i++){ if(!isNaN(sig[i]) && isFinite(fwd[i])) mask.push(i); }
  const sS=sig.filter((_,i)=>mask.includes(i)), fS=fwd.filter((_,i)=>mask.includes(i));
  const ic = pearson(sS, fS), rankic = spearman(sS, fS);
  const ics=[]; const w=60; for(let i=w;i<sS.length;i++) ics.push(pearson(sS.slice(i-w,i), fS.slice(i-w,i)));
  const icMean = ics.reduce((a,b)=>a+b,0)/ics.length;
  const icVar = ics.reduce((a,b)=>a+(b-icMean)*(b-icMean),0)/(ics.length-1);
  const icir = (ics.length>5 && icVar>1e-12)? icMean/Math.sqrt(icVar) : NaN;
  const wins = t.tradeReturns.filter(r=>r>0).length;
  const winRate = t.tradeReturns.length>0 ? wins/t.tradeReturns.length : NaN;
  return {cum, ann, mdd, sharpe, beta, treynor, ic, rankic, icir, winRate, trades: Math.round(turnover.reduce((a,b)=>a+b,0))};
}

function legendHTML(items){
  return items.map(it=>{
    let sym;
    if(it.type==='tri-up') sym='<span class="legend-tri" style="color:'+it.color+'">▲</span>';
    else if(it.type==='tri-down') sym='<span class="legend-tri" style="color:'+it.color+'">▼</span>';
    else { const b=(it.type==='dash')?'dashed':'solid'; sym='<span class="legend-line" style="border-top-color:'+it.color+';border-top-style:'+b+';"></span>'; }
    return '<span class="legend-item">'+sym+'<span>'+it.label+'</span></span>';
  }).join('');
}

const charts={};
function destroy(key){ if(charts[key]) charts[key].destroy(); }
function fmtPct(x){ return (x*100).toFixed(2)+'%'; }

function render(){
  const key = document.getElementById('stockSel').value;
  const data = STOCKS[key].data, name = STOCKS[key].name;
  const entryP=+document.getElementById('entrySlider').value;
  const exitP=+document.getElementById('exitSlider').value;
  const atrP=+document.getElementById('atrSlider').value;
  const stopM=+document.getElementById('stopSlider').value;
  const costPct=+document.getElementById('costSlider').value;
  const cost = costPct/100;
  document.getElementById('entryVal').textContent=entryP;
  document.getElementById('exitVal').textContent=exitP;
  document.getElementById('atrVal').textContent=atrP;
  document.getElementById('stopVal').textContent=stopM.toFixed(1);
  document.getElementById('costVal').textContent=costPct.toFixed(3);
  document.getElementById('stockTitle').textContent = name + '（海龟策略 · 入场'+entryP+'/出场'+exitP+'/ATR'+atrP+'/止损'+stopM+'×ATR）';
  document.getElementById('costHead').textContent = '策略（'+costPct.toFixed(3)+'%成本）';
  document.getElementById('dataInfo').innerHTML = '<b>数据范围：</b>'+(key==='zj'?RANGE_ZJ:RANGE_ZX)+' ｜ <b>复权：</b>前复权 ｜ <b>无风险利率：</b>年化 2.5% ｜ <b>年化因子：</b>252';

  const t = turtle(data, entryP, exitP, atrP, stopM, cost, true);
  const r0 = backtest(t.position, data, 0.0);
  const rC = backtest(t.position, data, cost);
  const n = data.length, LABELS = data.map(x=>x.d);
  const CLOSE = data.map(x=>x.c);

  // —— 价格 + 通道 + 信号 ——
  const buyData=new Array(n).fill(null), sellData=new Array(n).fill(null);
  for(let i=1;i<n;i++){
    const d = t.position[i]-t.position[i-1];
    if(t.position[i-1]===0 && t.position[i]===1) buyData[i]=CLOSE[i];
    else if(d===-1) sellData[i]=CLOSE[i];
  }
  destroy('price');
  charts.price = new Chart(document.getElementById('priceChart'), {
    type:'line',
    data:{ labels:LABELS, datasets:[
      {label:'收盘价', data:CLOSE, borderColor:'#111', borderWidth:1, pointRadius:0},
      {label:'入场上轨('+entryP+'日)', data:t.upperEntry, borderColor:'#888', borderWidth:1.3, pointRadius:0},
      {label:'入场下轨('+entryP+'日)', data:t.lowerEntry, borderColor:'#888', borderWidth:1.3, pointRadius:0},
      {label:'出场上轨('+exitP+'日)', data:t.upperExit, borderColor:'#bbb', borderWidth:1.0, borderDash:[5,4], pointRadius:0},
      {label:'出场下轨('+exitP+'日)', data:t.lowerExit, borderColor:'#bbb', borderWidth:1.0, borderDash:[5,4], pointRadius:0},
      {label:'买入', data:buyData, showLine:false, pointStyle:'triangle', rotation:0, pointRadius:6, pointBackgroundColor:'#3B6D11', borderColor:'#3B6D11'},
      {label:'卖出', data:sellData, showLine:false, pointStyle:'triangle', rotation:180, pointRadius:6, pointBackgroundColor:'#A32D2D', borderColor:'#A32D2D'}
    ]},
    options:{ responsive:true, interaction:{mode:'index', intersect:false}, plugins:{ legend:{display:false} },
      scales:{ x:{ ticks:{ maxTicksLimit:12, autoSkip:true } } } }
  });
  document.getElementById('priceLegend').innerHTML = legendHTML([
    {label:'收盘价', color:'#111', type:'line'},
    {label:'入场上轨('+entryP+'日)', color:'#888', type:'line'},
    {label:'入场下轨('+entryP+'日)', color:'#888', type:'line'},
    {label:'出场上/下轨('+exitP+'日)', color:'#bbb', type:'dash'},
    {label:'买入', color:'#3B6D11', type:'tri-up'},
    {label:'卖出', color:'#A32D2D', type:'tri-down'}
  ]);
  document.getElementById('pPeriod').textContent='（入场'+entryP+'/出场'+exitP+'/ATR'+atrP+'/止损'+stopM+'×）';

  // —— ATR ——
  destroy('atr');
  charts.atr = new Chart(document.getElementById('atrChart'), {
    type:'line',
    data:{ labels:LABELS, datasets:[ {label:'ATR('+atrP+'日)', data:t.atr, borderColor:'#7c3aed', borderWidth:1.2, pointRadius:0} ]},
    options:{ responsive:true, plugins:{ legend:{display:false} }, scales:{ x:{ ticks:{ maxTicksLimit:12, autoSkip:true } } } }
  });
  document.getElementById('atrLegend').innerHTML = legendHTML([{label:'ATR('+atrP+'日)', color:'#7c3aed', type:'line'}]);
  document.getElementById('aPeriod').textContent='（ATR'+atrP+'）';

  // —— 净值对比 ——
  const bh=new Array(n); bh[0]=1; for(let i=1;i<n;i++) bh[i]=bh[i-1]*(1+CLOSE[i]/CLOSE[i-1]-1);
  destroy('nav');
  charts.nav = new Chart(document.getElementById('navChart'), {
    type:'line',
    data:{ labels:LABELS, datasets:[
      {label:'策略净值(0成本)', data:r0.nav, borderColor:'#185FA5', borderWidth:1.5, pointRadius:0},
      {label:'策略净值('+costPct.toFixed(3)+'%成本)', data:rC.nav, borderColor:'#A32D2D', borderWidth:1.5, pointRadius:0},
      {label:'买入持有', data:bh, borderColor:'#111', borderWidth:1.1, borderDash:[6,4], pointRadius:0}
    ]},
    options:{ responsive:true, interaction:{mode:'index', intersect:false}, plugins:{ legend:{display:false} },
      scales:{ x:{ ticks:{ maxTicksLimit:12, autoSkip:true } } } }
  });
  document.getElementById('navLegend').innerHTML = legendHTML([
    {label:'策略净值(0成本)', color:'#185FA5', type:'line'},
    {label:'策略净值('+costPct.toFixed(3)+'%成本)', color:'#A32D2D', type:'line'},
    {label:'买入持有', color:'#111', type:'dash'}
  ]);
  document.getElementById('nPeriod').textContent='（入场'+entryP+'/出场'+exitP+'）';

  // —— 指标表 ——
  const m0 = metricsOf(t, data, 0.0), mC = metricsOf(t, data, cost);
  const bhCum = bh[n-1]-1;
  const rows = [
    ['累计回报', fmtPct(m0.cum), fmtPct(mC.cum)],
    ['年化收益率', fmtPct(m0.ann), fmtPct(mC.ann)],
    ['最大回撤(MDD)', fmtPct(m0.mdd), fmtPct(mC.mdd)],
    ['夏普比率', m0.sharpe.toFixed(3), mC.sharpe.toFixed(3)],
    ['Beta', m0.beta.toFixed(3), mC.beta.toFixed(3)],
    ['特雷诺比率', m0.treynor.toFixed(4), mC.treynor.toFixed(4)],
    ['IC', m0.ic.toFixed(4), mC.ic.toFixed(4)],
    ['RankIC', m0.rankic.toFixed(4), mC.rankic.toFixed(4)],
    ['ICIR', m0.icir.toFixed(4), mC.icir.toFixed(4)],
    ['交易次数', m0.trades, mC.trades],
    ['胜率', fmtPct(m0.winRate), fmtPct(mC.winRate)]
  ];
  document.querySelector('#metricsTable tbody').innerHTML = rows.map(r=>'<tr><td class="metric">'+r[0]+'</td><td>'+r[1]+'</td><td>'+r[2]+'</td></tr>').join('');

  // —— 累计收益柱状图 ——
  destroy('bar');
  charts.bar = new Chart(document.getElementById('barChart'), {
    type:'bar',
    data:{ labels:['长期持有','海龟策略(0成本)','海龟策略('+costPct.toFixed(3)+'%成本)'],
      datasets:[{ label:'累计收益率(%)', data:[bhCum*100, m0.cum*100, mC.cum*100], backgroundColor:['#111','#185FA5','#A32D2D'], borderRadius:4 }] },
    options:{ responsive:true, plugins:{ legend:{display:false}, tooltip:{ callbacks:{ label: ctx=>ctx.parsed.y.toFixed(2)+'%' } } },
      scales:{ y:{ ticks:{ callback:v=>v+'%' }, title:{ display:true, text:'累计收益率' } }, x:{ ticks:{ maxRotation:0, minRotation:0 } } } }
  });
  document.getElementById('bPeriod').textContent='（入场'+entryP+'/出场'+exitP+'）';
}

['entrySlider','exitSlider','atrSlider','stopSlider','costSlider','stockSel'].forEach(id=>{
  document.getElementById(id).addEventListener('input', render);
  document.getElementById(id).addEventListener('change', render);
});
render();
</script>
</body>
</html>
"""

html = (TEMPLATE
        .replace('__DATA_ZJ__', zj_json)
        .replace('__DATA_ZX__', zx_json)
        .replace('__ZJ_RANGE__', zj_range)
        .replace('__ZX_RANGE__', zx_range))

out = r'E:\BA课程练习\TASK4\李明凯+TASK4_交互式.html'
with open(out, 'w', encoding='utf-8') as f:
    f.write(html)
print('已生成', out)
print('中际旭创数据点：', len(data_zj), '｜', zj_range)
print('中兴通讯数据点：', len(data_zx), '｜', zx_range)
