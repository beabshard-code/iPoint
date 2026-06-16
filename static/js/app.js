(function () {
  var tg = window.Telegram && window.Telegram.WebApp;
  
  if (tg) {
    tg.ready();
    tg.expand();
    if (tg.themeParams) {
      var tp = tg.themeParams;
      if (tp.bg_color) document.documentElement.style.setProperty('--tg-bg', tp.bg_color);
      if (tp.text_color) document.documentElement.style.setProperty('--tg-text', tp.text_color);
    }
    document.body.classList.add('tg-webapp');

    var startParam = tg.initDataUnsafe && tg.initDataUnsafe.start_param;
    if (startParam && /^\d+$/.test(startParam)) {
      var target = '/product/' + startParam;
      if (window.location.pathname !== target) {
        window.location.replace(target);
        return;
      }
    }

    if (tg.colorScheme === 'dark') {
      var di = document.querySelector('.switcher__input[value="dark"]');
      if (di) { di.checked = true; localStorage.setItem('ipoint-theme', 'dark'); }
    }

    // Автоматическая авторизация через Telegram WebApp
    if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
      var user = tg.initDataUnsafe.user;
      var isAuth = document.body.dataset.authenticated === "true";
      if (!isAuth) {
        fetch('/api/tg-login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(user)
        })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (data.ok) {
            window.location.reload();
          }
        })
        .catch(function() {});
      }
    }
  }

  var savedTheme = localStorage.getItem('ipoint-theme') || 'light';
  var tinput = document.querySelector('.switcher__input[value="' + savedTheme + '"]');
  if (tinput) tinput.checked = true;
  document.addEventListener('change', function (e) {
    if (e.target.matches('.switcher__input')) localStorage.setItem('ipoint-theme', e.target.value);
  });

  var toastWrap = document.querySelector('.toasts');
  if (!toastWrap) {
    toastWrap = document.createElement('div');
    toastWrap.className = 'toasts';
    document.body.appendChild(toastWrap);
  }
  var ICONS = {
    success: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" class="icon"><path d="M5 12.5 10 17.5 19 7"/></svg>',
    error: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" class="icon"><path d="M6 6l12 12M18 6 6 18"/></svg>',
    info: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" class="icon"><path d="M12 8h.01M11 12h1v4h1"/></svg>',
  };
  window.toast = function (msg, type) {
    type = type || 'info';
    var t = document.createElement('div');
    t.className = 'toast ' + type;
    t.innerHTML = '<span class="ic">' + (ICONS[type] || ICONS.info) + '</span><span>' + msg + '</span>';
    toastWrap.appendChild(t);
    requestAnimationFrame(function () { t.classList.add('show'); });
    setTimeout(function () {
      t.classList.remove('show');
      setTimeout(function () { t.remove(); }, 450);
    }, 3600);
  };
  document.querySelectorAll('[data-flash]').forEach(function (el) {
    window.toast(el.dataset.flash, el.dataset.cat || 'info');
    el.remove();
  });

  document.querySelectorAll('.cselect').forEach(function (sel) {
    var trigger = sel.querySelector('.cselect__trigger');
    var valEl = sel.querySelector('.cselect__value');
    var hidden = sel.querySelector('input[type=hidden]');
    var opts = sel.querySelectorAll('.cselect__opt');
    trigger.addEventListener('click', function (e) {
      e.stopPropagation();
      var wasOpen = sel.classList.contains('open');
      document.querySelectorAll('.cselect.open').forEach(function (s) { s.classList.remove('open'); });
      sel.classList.toggle('open', !wasOpen);
    });
    opts.forEach(function (opt) {
      opt.addEventListener('click', function () {
        opts.forEach(function (o) { o.classList.remove('sel'); });
        opt.classList.add('sel');
        valEl.textContent = opt.dataset.label;
        if (hidden) hidden.value = opt.dataset.value;
        sel.classList.remove('open');
        if (sel.dataset.autosubmit !== undefined) sel.closest('form').submit();
        sel.dispatchEvent(new CustomEvent('cselect:change', { detail: opt.dataset.value, bubbles: true }));
      });
    });
  });
  document.addEventListener('click', function () { document.querySelectorAll('.cselect.open').forEach(function (s) { s.classList.remove('open'); }); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') document.querySelectorAll('.cselect.open').forEach(function (s) { s.classList.remove('open'); }); });

  var tip;
  document.addEventListener('pointerenter', function (e) {
    var el = e.target.closest && e.target.closest('[data-tip]');
    if (!el) return;
    tip = document.createElement('div');
    tip.className = 'tip-bubble';
    tip.textContent = el.dataset.tip;
    document.body.appendChild(tip);
    var r = el.getBoundingClientRect();
    tip.style.left = r.left + r.width / 2 - tip.offsetWidth / 2 + 'px';
    tip.style.top = r.bottom + 8 + 'px';
    requestAnimationFrame(function () { tip.classList.add('show'); });
  }, true);
  document.addEventListener('pointerleave', function (e) {
    if (e.target.closest && e.target.closest('[data-tip]') && tip) { tip.remove(); tip = null; }
  }, true);

  var scrim = document.getElementById('scrim');
  function openDrawer(id) {
    var d = document.getElementById(id);
    if (!d) return;
    d.classList.add('open');
    if (scrim) scrim.classList.add('open');
    document.body.style.overflow = 'hidden';
  }
  function closeDrawers() {
    document.querySelectorAll('.drawer.open').forEach(function (d) { d.classList.remove('open'); });
    if (scrim) scrim.classList.remove('open');
    document.body.style.overflow = '';
  }
  document.querySelectorAll('[data-open-drawer]').forEach(function (b) { b.addEventListener('click', function () { openDrawer(b.dataset.openDrawer); }); });
  document.querySelectorAll('[data-close-drawer]').forEach(function (b) { b.addEventListener('click', closeDrawers); });
  if (scrim) scrim.addEventListener('click', closeDrawers);
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeDrawers(); });

  var ov = document.getElementById('searchOv');
  document.querySelectorAll('[data-open-search]').forEach(function (b) {
    b.addEventListener('click', function () {
      if (ov) { ov.classList.add('open'); var i = ov.querySelector('input'); if (i) setTimeout(function () { i.focus(); }, 120); }
    });
  });
  document.querySelectorAll('[data-close-search]').forEach(function (b) { b.addEventListener('click', function () { if (ov) ov.classList.remove('open'); }); });

  document.querySelectorAll('.range').forEach(function (range) {
    var min = range.querySelector('.range__min');
    var max = range.querySelector('.range__max');
    var fill = range.querySelector('.range__fill');
    var outMin = range.parentElement.querySelector('.val-min');
    var outMax = range.parentElement.querySelector('.val-max');
    var lo = +min.min, hi = +min.max;
    var fmt = function (n) { return (+n).toLocaleString('ru-RU') + ' \u20BD'; };
    function upd() {
      var a = +min.value, b = +max.value;
      if (a > b - 1) { a = b - 1; min.value = a; }
      var p1 = ((a - lo) / (hi - lo)) * 100, p2 = ((b - lo) / (hi - lo)) * 100;
      fill.style.left = p1 + '%'; fill.style.width = (p2 - p1) + '%';
      if (outMin) outMin.textContent = fmt(a);
      if (outMax) outMax.textContent = (b >= hi ? fmt(b) + '+' : fmt(b));
    }
    min.addEventListener('input', upd); max.addEventListener('input', upd); upd();
  });

  document.addEventListener('click', function (e) {
    var thumb = e.target.closest('.gallery .thumbs img');
    if (thumb) {
      var main = document.getElementById('mainImg');
      if (main) main.innerHTML = '<img src="' + thumb.dataset.src + '" alt="">';
      document.querySelectorAll('.gallery .thumbs img').forEach(function (t) { t.classList.remove('active'); });
      thumb.classList.add('active');
      return;
    }
    var fav = e.target.closest('.fav-btn, .fav-btn-lg');
    if (fav) {
      e.preventDefault();
      fetch('/favorites/toggle/' + fav.dataset.id, { method: 'POST', headers: { 'X-Requested-With': 'fetch' } })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          fav.classList.toggle('active', data.active);
          var lbl = fav.querySelector('.fav-label');
          if (lbl) lbl.textContent = data.active ? '\u0412 \u0438\u0437\u0431\u0440\u0430\u043d\u043d\u043e\u043c' : '\u0412 \u0438\u0437\u0431\u0440\u0430\u043d\u043d\u043e\u0435';
          window.toast(data.active ? '\u0414\u043e\u0431\u0430\u0432\u043b\u0435\u043d\u043e \u0432 \u0438\u0437\u0431\u0440\u0430\u043d\u043d\u043e\u0435' : '\u0423\u0431\u0440\u0430\u043d\u043e \u0438\u0437 \u0438\u0437\u0431\u0440\u0430\u043d\u043d\u043e\u0433\u043e', 'success');
        })
        .catch(function () { window.toast('\u041e\u0448\u0438\u0431\u043a\u0430', 'error'); });
    }
  });

  function bindPreview(id) {
    var input = document.getElementById(id);
    var preview = document.getElementById('preview');
    if (!input || !preview) return;
    input.addEventListener('change', function () {
      preview.innerHTML = '';
      Array.from(input.files).forEach(function (file) {
        var img = document.createElement('img');
        img.src = URL.createObjectURL(file);
        preview.appendChild(img);
      });
    });
  }
  bindPreview('imgInput');
  bindPreview('avInput');

  document.querySelectorAll('.chip-row').forEach(function (row) {
    row.addEventListener('click', function (e) {
      var chip = e.target.closest('.chip');
      if (!chip) return;
      var input = chip.querySelector('input');
      if (!input) return;
      row.querySelectorAll('.chip').forEach(function (c) {
        var i = c.querySelector('input');
        if (i && i.name === input.name) c.classList.remove('active');
      });
      chip.classList.add('active');
    });
  });

  window.sendPurchaseLog = function (title, price, userInfo) {
    fetch('/api/purchase-log', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: title, price: price, user: userInfo }),
    }).catch(function () {});
  };
})();
