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
