(function(){
  var initialized = false;

  function setupIO(){
    var io = new IntersectionObserver(function(es){
      es.forEach(function(e){ if(e.isIntersecting) e.target.classList.add('cine-visible'); });
    }, {threshold: 0.12, rootMargin: '0px 0px -40px 0px'});
    var sels = '[data-anim="section"],[data-anim="card"],[data-anim="step"],[data-anim="pricing"],[data-anim="footer"]';
    var els = document.querySelectorAll(sels);
    if(els.length === 0) return false;
    els.forEach(function(el){ io.observe(el); });
    return true;
  }

  function initParticles(){
    var c = document.getElementById('cineParticles');
    if(!c || c.dataset.init) return;
    c.dataset.init = '1';
    var ctx = c.getContext('2d');
    var w = c.width = window.innerWidth, h = c.height = window.innerHeight;
    window.addEventListener('resize', function(){ w = c.width = window.innerWidth; h = c.height = window.innerHeight; });
    var ps = [];
    var n = Math.min(50, Math.floor(w * h / 18000));
    for(var i = 0; i < n; i++){
      ps.push({
        x: Math.random()*w, y: Math.random()*h,
        vx: (Math.random()-.5)*.35, vy: (Math.random()-.5)*.35,
        r: Math.random()*1.5+.5,
        c: Math.random()>.5 ? '56,189,248' : '52,211,153',
        o: Math.random()*.35+.08
      });
    }
    function draw(){
      ctx.clearRect(0,0,w,h);
      for(var i = 0; i < ps.length; i++){
        var p = ps[i];
        ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, 6.28);
        ctx.fillStyle = 'rgba('+p.c+','+p.o+')'; ctx.fill();
        for(var j = i+1; j < ps.length; j++){
          var q = ps[j], dx = p.x-q.x, dy = p.y-q.y, d = Math.sqrt(dx*dx+dy*dy);
          if(d < 130){
            ctx.beginPath(); ctx.moveTo(p.x,p.y); ctx.lineTo(q.x,q.y);
            ctx.strokeStyle = 'rgba(52,211,153,'+(0.06*(1-d/130))+')';
            ctx.lineWidth = .5; ctx.stroke();
          }
        }
        p.x += p.vx; p.y += p.vy;
        if(p.x < 0 || p.x > w) p.vx *= -1;
        if(p.y < 0 || p.y > h) p.vy *= -1;
      }
      requestAnimationFrame(draw);
    }
    draw();
  }

  function initMouseGlow(){
    var g = document.getElementById('mouseGlow');
    if(!g || g.dataset.init) return;
    g.dataset.init = '1';
    document.addEventListener('mousemove', function(e){
      g.style.left = e.clientX + 'px';
      g.style.top = e.clientY + 'px';
    });
  }

  function ease(t){ return t < .5 ? 4*t*t*t : 1 - Math.pow(-2*t+2, 3)/2; }

  function cineScroll(){
    if(window.innerWidth <= 768) return;
    var total = document.documentElement.scrollHeight - window.innerHeight;
    if(total <= 0) return;
    var dMs = 5500, uMs = 2200, st = null;
    function dn(ts){
      if(!st) st = ts;
      var p = Math.min((ts-st)/dMs, 1);
      window.scrollTo(0, ease(p)*total);
      if(p < 1) requestAnimationFrame(dn);
      else { st = null; setTimeout(function(){ requestAnimationFrame(up); }, 400); }
    }
    function up(ts){
      if(!st) st = ts;
      var p = Math.min((ts-st)/uMs, 1);
      window.scrollTo(0, (1-ease(p))*total);
      if(p < 1) requestAnimationFrame(up);
    }
    setTimeout(function(){ requestAnimationFrame(dn); }, 2800);
  }

  function init(){
    if(initialized) return;
    var found = setupIO();
    if(!found){
      // Elements not yet rendered, retry
      setTimeout(init, 500);
      return;
    }
    initialized = true;
    initParticles();
    initMouseGlow();
    cineScroll();
  }

  // Try init on various lifecycle events
  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', function(){ setTimeout(init, 300); });
  } else {
    setTimeout(init, 300);
  }
  // Also retry on route changes (Reflex SPA navigation)
  var observer = new MutationObserver(function(){
    if(!initialized) setTimeout(init, 300);
  });
  observer.observe(document.body, {childList: true, subtree: true});
  // Safety: retry a few times
  setTimeout(init, 1000);
  setTimeout(init, 2000);
  setTimeout(init, 4000);
})();
