(function(){
  function initReveal(){
    var selector = [
      '.anim-1','.anim-2','.anim-3','.anim-4','.anim-5','.anim-6','.reveal',
      'main .hero','main .hero-photo','main .section-gap','main .card',
      'main .eco-card','main .metric-card','main .home-section','main .feature-tile',
      'main .table-shell','main .training-card','main .product-card','main .photo-card'
    ].join(',');
    var seen = [];
    var items = Array.prototype.slice.call(document.querySelectorAll(selector)).filter(function(el){
      if(seen.indexOf(el) !== -1) return false;
      seen.push(el);
      return true;
    });
    if(!items.length) return;

    items.forEach(function(el){
      el.classList.add('reveal');
    });

    if(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches){
      items.forEach(function(el){ el.classList.add('visible'); });
      return;
    }

    if(!('IntersectionObserver' in window)){
      items.forEach(function(el){ el.classList.add('visible'); });
      return;
    }

    var observer = new IntersectionObserver(function(entries){
      entries.forEach(function(entry){
        if(entry.isIntersecting){
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15, rootMargin: '0px 0px -40px 0px' });

    items.forEach(function(el){ observer.observe(el); });
  }

  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', initReveal);
  } else {
    initReveal();
  }
})();
