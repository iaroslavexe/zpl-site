// Активная вкладка всегда видна в прокручиваемом меню на телефоне
(function () {
  var active = document.querySelector('.tab.is-active');
  if (!active) return;
  var tabs = active.parentElement;
  if (tabs.scrollWidth <= tabs.clientWidth) return;
  tabs.scrollLeft = active.offsetLeft - (tabs.clientWidth - active.offsetWidth) / 2;
})();


// Счётчик дней до этапа: пересчитываем на клиенте, чтобы статика не «замерзала»
(function () {
  function plural(days) {
    if (days % 10 === 1 && days % 100 !== 11) return 'день';
    if (days % 10 >= 2 && days % 10 <= 4 && (days % 100 < 12 || days % 100 > 14)) return 'дня';
    return 'дней';
  }

  document.querySelectorAll('[data-days-to]').forEach(function (node) {
    var target = Date.parse(node.dataset.daysTo + 'T00:00:00+03:00');
    if (isNaN(target)) return;

    var days = Math.ceil((target - Date.now()) / 86400000);
    if (days <= 0) {
      node.hidden = true;
      return;
    }

    var number = node.querySelector('b');
    var word = node.querySelector('[data-days-word]');
    if (number) number.textContent = days;
    if (word) word.textContent = plural(days);
    node.hidden = false;
  });
})();
