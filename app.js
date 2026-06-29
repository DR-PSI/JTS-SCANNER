
var N8N='https://n8n.jupetor-cmms.com/webhook/24b8ea71-daa0-48c1-ac83-c1b79ae2c1a4';
var allData=[],currentFilter='ALL',currentTf='monthly';
var currentSymbol=null,currentModalTf='monthly';
var priceChart=null,macdChart=null;
var cacheMonthly=null,cacheDaily=null;

function cdcColor(col){
  if(col==='GREEN') return '#3fb950';
  if(col==='RED') return '#f85149';
  if(col==='YELLOW') return '#d0b023';
  if(col==='ORANGE') return '#f87730';
  return '#8b949e';
}
function parseDt(d,tf){
  return tf==='monthly'?new Date(d+'-01').getTime():new Date(d).getTime();
}
function fetchJ(file){
  return fetch(file+'?t='+Date.now()).then(function(r){return r.json();});
}
function loadData(){
  document.getElementById('loading').style.display='block';
  document.getElementById('main-table').style.display='none';
  var file=currentTf==='monthly'?'scanner-data.json':'scanner-data-day.json';
  fetchJ(file).then(function(data){
    allData=data.stocks||[];
    if(currentTf==='monthly') cacheMonthly=data; else cacheDaily=data;
    var lbl=currentTf==='monthly'?'Monthly':'Daily';
    document.getElementById('last-update').textContent=lbl+' | Update: '+(data.updated||'-');
    document.getElementById('total-count').textContent=allData.length;
    document.getElementById('buy-count').textContent=allData.filter(function(r){return r.position==='BUY';}).length;
    document.getElementById('sell-count').textContent=allData.filter(function(r){return r.position==='SELL';}).length;
    renderTable(currentFilter);
  }).catch(function(){document.getElementById('loading').innerHTML='ERROR';});
}
function switchTf(tf,btn){
  currentTf=tf;
  document.querySelectorAll('.tf-btn').forEach(function(b){b.classList.remove('active');});
  btn.classList.add('active');
  loadData();
}
function filterData(f,btn){
  currentFilter=f;
  document.querySelectorAll('.btn').forEach(function(b){b.classList.remove('active');});
  btn.classList.add('active');
  renderTable(f);
}
function renderTable(f){
  var rows=allData.filter(function(r){return r.position!=='NONE';});
  if(f==='BUY') rows=rows.filter(function(r){return r.position==='BUY';});
  if(f==='SELL') rows=rows.filter(function(r){return r.position==='SELL';});
  rows.sort(function(a,b){
    if(a.new&&!b.new) return -1;
    if(!a.new&&b.new) return 1;
    return b.date.localeCompare(a.date);
  });
  var html='';
  for(var i=0;i<rows.length;i++){
    var r=rows[i];
    var pos=r.position==='BUY'?'Ready to Buy':'Ready to Sell';
    var posIcon=r.position==='BUY'?'BUY':'SELL';
    var pr=r.price.toLocaleString('th-TH',{minimumFractionDigits:2});
    html+='<tr>';
    html+='<td style="color:#8b949e">'+(i+1)+'</td>';
    html+='<td class="symbol" onclick="showChart(\''+r.symbol+'\')">'+r.symbol+'</td>';
    html+='<td><span class="badge '+r.position.toLowerCase()+'">'+pos+'</span></td>';
    html+='<td style="font-weight:500">'+pr+'</td>';
    html+='<td style="color:#8b949e;font-size:13px">'+r.date+'</td>';
    html+='<td>'+(r.new?'NEW':'')+'</td>';
    html+='<td><button class="chart-btn" onclick="showChart(\''+r.symbol+'\')">Chart</button></td>';
    html+='<td><button class="line-btn" onclick="sendLine(\''+r.symbol+'\',\''+r.position+'\','+r.price+',\''+r.date+'\',this)">LINE</button></td>';
    html+='</tr>';
  }
  document.getElementById('table-body').innerHTML=html;
  document.getElementById('loading').style.display='none';
  document.getElementById('main-table').style.display='table';
}
function showChart(symbol){
  currentSymbol=symbol;
  currentModalTf=currentTf;
  document.getElementById('mtf-monthly').classList.toggle('active',currentModalTf==='monthly');
  document.getElementById('mtf-daily').classList.toggle('active',currentModalTf==='daily');
  document.getElementById('modal-bg').classList.add('show');
  renderChart(symbol,currentModalTf);
}
function switchModalTf(tf,btn){
  currentModalTf=tf;
  document.querySelectorAll('.modal-tf-btn').forEach(function(b){b.classList.remove('active');});
  btn.classList.add('active');
  if(currentSymbol) renderChart(currentSymbol,tf);
}
function renderChart(symbol,tf){
  var cache=tf==='monthly'?cacheMonthly:cacheDaily;
  if(cache){doRender(symbol,tf,cache);}
  else{
    var file=tf==='monthly'?'scanner-data.json':'scanner-data-day.json';
    fetchJ(file).then(function(data){
      if(tf==='monthly') cacheMonthly=data; else cacheDaily=data;
      doRender(symbol,tf,data);
    }).catch(function(){
      document.getElementById('modal-title').textContent=symbol+' - no data';
    });
  }
}
function doRender(symbol,tf,cache){
  var stock=null;
  var stocks=cache&&cache.stocks||[];
  for(var i=0;i<stocks.length;i++){if(stocks[i].symbol===symbol){stock=stocks[i];break;}}
  if(!stock||!stock.chart){
    document.getElementById('modal-title').textContent=symbol+' - no data '+tf;
    return;
  }
  var c=stock.chart;
  var tfLabel=tf==='monthly'?'Monthly':'Daily 6mo';
  var posLabel=stock.position==='BUY'?'Ready to Buy':'Ready to Sell';
  document.getElementById('modal-title').textContent=symbol+' - '+posLabel+' - '+tfLabel;
  var timeUnit=tf==='monthly'?'month':'day';
  var timeFmt=tf==='monthly'?{month:'MMM yy'}:{day:'d MMM yy'};
  var groups={
    GREEN:{color:'#3fb950',bars:[]},
    RED:{color:'#f85149',bars:[]},
    YELLOW:{color:'#d0b023',bars:[]},
    ORANGE:{color:'#f87730',bars:[]}
  };
  for(var i=0;i<c.dates.length;i++){
    var col=(c.cdc_color&&c.cdc_color[i])||'GREEN';
    var g=groups[col];
    if(g) g.bars.push({x:parseDt(c.dates[i],tf),o:c.open[i],h:c.high[i],l:c.low[i],c:c.close[i]});
  }
  var datasets=[];
  var gkeys=Object.keys(groups);
  for(var k=0;k<gkeys.length;k++){
    var name=gkeys[k];
    var g=groups[name];
    if(!g.bars.length) continue;
    datasets.push({label:name,type:'candlestick',data:g.bars,
      color:{up:g.color,down:g.color,unchanged:g.color},
      borderColor:{up:g.color,down:g.color,unchanged:g.color},order:3});
  }
  var e12=[],e26=[];
  for(var i=0;i<c.dates.length;i++){
    e12.push({x:parseDt(c.dates[i],tf),y:c.ema12[i]});
    e26.push({x:parseDt(c.dates[i],tf),y:c.ema26[i]});
  }
  datasets.push({label:'EMA12',type:'line',data:e12,borderColor:'#f85149',borderWidth:1.5,pointRadius:0,tension:0.3,order:2});
  datasets.push({label:'EMA26',type:'line',data:e26,borderColor:'#58a6ff',borderWidth:1.5,pointRadius:0,tension:0.3,order:2});
  var buyPts=[],sellPts=[];
  var sigs=c.signals||[];
  for(var i=0;i<sigs.length;i++){
    if(sigs[i].type==='BUY') buyPts.push({x:parseDt(sigs[i].date,tf),y:sigs[i].price});
    else sellPts.push({x:parseDt(sigs[i].date,tf),y:sigs[i].price});
  }
  if(buyPts.length)  datasets.push({label:'BUY', type:'scatter',data:buyPts, backgroundColor:'#3fb950',pointRadius:10,pointStyle:'triangle',order:1});
  if(sellPts.length) datasets.push({label:'SELL',type:'scatter',data:sellPts,backgroundColor:'#f85149',pointRadius:10,pointStyle:'triangle',rotation:180,order:1});
  var scaleX={type:'time',time:{unit:timeUnit,displayFormats:timeFmt},ticks:{color:'#8b949e',maxTicksLimit:12},grid:{color:'#21262d'}};
  var scaleY={ticks:{color:'#8b949e'},grid:{color:'#21262d'}};
  if(priceChart) priceChart.destroy();
  priceChart=new Chart(document.getElementById('price-chart'),{
    type:'candlestick',data:{datasets:datasets},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{labels:{color:'#e6edf3',font:{size:10}}}},
      scales:{x:scaleX,y:scaleY}}
  });
  var histColors=[];
  for(var i=0;i<c.hist.length;i++) histColors.push(c.hist[i]>=0?'rgba(63,185,80,0.8)':'rgba(248,81,73,0.8)');
  var labels=[];
  for(var i=0;i<c.dates.length;i++) labels.push(parseDt(c.dates[i],tf));
  if(macdChart) macdChart.destroy();
  macdChart=new Chart(document.getElementById('macd-chart'),{
    type:'bar',
    data:{labels:labels,datasets:[
      {label:'Histogram',data:c.hist,backgroundColor:histColors,borderWidth:0,order:2},
      {label:'MACD',data:c.macd,type:'line',borderColor:'#f85149',borderWidth:1.5,pointRadius:0,tension:0.3,order:1},
      {label:'Signal',data:c.signal,type:'line',borderColor:'#58a6ff',borderWidth:1.5,pointRadius:0,tension:0.3,order:1}
    ]},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{labels:{color:'#e6edf3',font:{size:11}}}},
      scales:{x:scaleX,y:scaleY}}
  });
}
function closeModal(){document.getElementById('modal-bg').classList.remove('show');}
function sendLine(symbol,signal,price,date,btn){
  btn.textContent='...';btn.disabled=true;
  var emoji=signal==='BUY'?'BUY':'SELL';
  var tf=currentTf==='monthly'?'Monthly':'Daily';
  var now=new Date().toLocaleString('th-TH',{timeZone:'Asia/Bangkok'});
  var msg=emoji+' - '+symbol+' - '+price+' - '+tf+' - '+date+' - '+now;
  fetch(N8N,{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({symbol:symbol,signal:signal,price:price,date:date,message:msg})
  }).then(function(res){
    if(res.ok){btn.classList.add('sent');btn.textContent='SENT';showToast('Sent '+symbol);}
    else throw new Error();
  }).catch(function(){btn.textContent='LINE';btn.disabled=false;showToast('Error',true);});
}
function showToast(msg,isError){
  var t=document.getElementById('toast');
  t.textContent=msg;t.className='toast show'+(isError?' error':'');
  setTimeout(function(){t.className='toast';},3000);
}
loadData();
