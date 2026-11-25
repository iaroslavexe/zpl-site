// Переключение дивизионов в матрице архива
(function () {
  var root = document.getElementById('archive-switch');
  if (!root) return;

  var buttons = root.querySelectorAll('button');
  var tables = document.querySelectorAll('[data-matrix]');

  function show(key) {
    tables.forEach(function (table) {
      table.hidden = table.dataset.matrix !== key;
    });
    buttons.forEach(function (button) {
      button.classList.toggle('is-active', button.dataset.target === key);
    });
  }

  buttons.forEach(function (button) {
    button.addEventListener('click', function () { show(button.dataset.target); });
  });

  show('msk');
})();

// Сортировка таблиц архива по клику и фильтр по строкам
(function () {
  document.querySelectorAll('table[data-sortable]').forEach(function (table) {
    var headers = table.querySelectorAll('th[data-sort]');
    headers.forEach(function (header) {
      header.style.cursor = 'pointer';
      header.addEventListener('click', function () {
        var index = Number(header.dataset.sort);
        var body = table.tBodies[0];
        var rows = Array.prototype.slice.call(body.rows);
        var dir = header.dataset.dir === 'desc' ? 1 : -1;
        rows.sort(function (a, b) {
          var va = Number(a.cells[index].dataset.v || 0);
          var vb = Number(b.cells[index].dataset.v || 0);
          return (va - vb) * dir;
        });
        rows.forEach(function (row) { body.appendChild(row); });
        headers.forEach(function (h) { h.dataset.dir = ''; });
        header.dataset.dir = dir === -1 ? 'asc' : 'desc';
      });
    });
  });
})();


// Фильтр по строкам таблиц архива
(function () {
  document.querySelectorAll('input[data-filter]').forEach(function (input) {
    var next = input.nextElementSibling;
    var table = next && (next.matches('table') ? next : next.querySelector('table'));
    if (!table || !table.tBodies.length) return;
    input.addEventListener('input', function () {
      var query = input.value.trim().toLowerCase();
      Array.prototype.forEach.call(table.tBodies[0].rows, function (row) {
        var text = row.textContent.toLowerCase();
        row.hidden = query.length > 0 && text.indexOf(query) === -1;
      });
    });
  });
})();


// Подсказка для бейджей наград
(function () {
  var tip = null;
  function ensureTip() {
    if (!tip) {
      tip = document.createElement('div');
      tip.className = 'award-tip';
      document.body.appendChild(tip);
    }
    return tip;
  }
  document.addEventListener('mouseover', function (event) {
    var el = event.target.closest('[data-tip]');
    if (!el) return;
    var box = ensureTip();
    box.innerHTML = el.getAttribute('data-tip').split('\n')
      .map(function (line) { return '<div>' + line + '</div>'; }).join('');
    box.classList.add('is-on');
    var rect = el.getBoundingClientRect();
    var left = Math.min(rect.left, window.innerWidth - box.offsetWidth - 12);
    var top = rect.bottom + 8;
    if (top + box.offsetHeight > window.innerHeight - 8) top = rect.top - box.offsetHeight - 8;
    box.style.left = Math.max(8, left) + 'px';
    box.style.top = Math.max(8, top) + 'px';
  });
  document.addEventListener('mouseout', function (event) {
    if (event.target.closest('[data-tip]') && tip) tip.classList.remove('is-on');
  });
})();
