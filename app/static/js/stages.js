// Переключение этапов без перезагрузки: все панели уже отрисованы на сервере.
(function () {
  var root = document.getElementById('stages');
  if (!root) return;

  var links = root.querySelectorAll('[data-stage-link]');
  var panels = root.querySelectorAll('[data-stage-panel]');

  function show(id) {
    var found = false;
    panels.forEach(function (panel) {
      var active = panel.dataset.stagePanel === id;
      panel.hidden = !active;
      if (active) found = true;
    });
    if (!found) return false;

    links.forEach(function (link) {
      link.classList.toggle('is-active', link.dataset.stageLink === id);
    });
    return true;
  }

  links.forEach(function (link) {
    link.addEventListener('click', function (event) {
      var id = link.dataset.stageLink;
      if (!show(id)) return;
      event.preventDefault();
      var url = id === root.dataset.current ? '/stages' : '/stages?stage=' + id;
      history.replaceState(null, '', url);
    });
  });

  var param = new URLSearchParams(window.location.search).get('stage');
  if (param) show(param);
})();
