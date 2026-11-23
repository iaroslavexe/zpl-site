// Статистика: живой fetch из фэнтези, фильтр по этапам, поиск и сортировка.
(function () {
  var node = document.getElementById('stats-data');
  if (!node) return;

  var initial = JSON.parse(node.textContent);
  var state = {
    stage: 'all',
    gender: 'all',
    sort: 'goals',
    query: '',
    players: initial.players || [],
    aliases: initial.aliases || {},
    stages: initial.with_data || []
  };

  var body = document.getElementById('stats-body');
  var search = document.getElementById('stats-search');
  var tabs = document.getElementById('stats-stages');

  function canon(team) {
    if (!team) return team;
    var key = String(team).replace(/’/g, "'").trim().toLowerCase();
    return state.aliases[key] || team;
  }

  function teamOf(player) {
    if (state.stage === 'all') return player.team || '—';
    return (player.teams_by_stage || {})[state.stage] || player.team || '—';
  }

  function previousTeam(player) {
    var list = player.teams || [];
    if (state.stage !== 'all' || list.length < 2) return '';
    var current = player.team || list[list.length - 1];
    var previous = list.filter(function (team) { return team !== current; })[0];
    return previous ? 'ранее: ' + previous : '';
  }

  function value(player, key) {
    if (state.stage === 'all') return player[key] || 0;
    var stage = (player.by_stage || {})[state.stage];
    return stage ? (stage[key] || 0) : null;
  }

  function rows() {
    var query = state.query.trim().toLowerCase();
    var list = state.players
      .map(function (player) {
        return {
          player: player,
          goals: value(player, 'goals'),
          assists: value(player, 'assists'),
          blocks: value(player, 'blocks')
        };
      })
      .filter(function (row) { return row.goals !== null; })
      .filter(function (row) {
        return state.gender === 'all' || row.player.gender === state.gender;
      })
      .filter(function (row) {
        if (!query) return true;
        var name = (row.player.name || '').toLowerCase();
        var team = (row.player.team || '').toLowerCase();
        return name.indexOf(query) !== -1 || team.indexOf(query) !== -1;
      });

    list.sort(function (a, b) {
      var diff = b[state.sort] - a[state.sort];
      if (diff) return diff;
      if (b.goals !== a.goals) return b.goals - a.goals;
      return (a.player.name || '').localeCompare(b.player.name || '', 'ru');
    });
    return list;
  }

  function escape(text) {
    return String(text == null ? '' : text).replace(/[&<>"]/g, function (ch) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[ch];
    });
  }

  function render() {
    var list = rows();
    body.innerHTML = list.map(function (row, index) {
      var player = row.player;
      var team = teamOf(player);
      var previous = previousTeam(player);
      var avatar = player.avatar_url
        ? '<img class="st-avatar" src="' + escape(player.avatar_url) + '" alt="" loading="lazy">'
        : '<span class="st-avatar st-avatar--empty">' + escape((player.name || '?').slice(0, 1)) + '</span>';

      return '<tr>' +
        '<td class="st-rank">' + (index + 1) + '</td>' +
        '<td class="st-player"><div class="st-player__inner">' + avatar +
          '<span class="st-player__text">' +
            '<span class="st-name">' + escape(player.name) + '</span>' +
            '<span class="st-team-inline">' + escape(team) + '</span>' +
          '</span>' +
        '</div></td>' +
        '<td class="st-team">' + escape(team) +
          (previous ? '<span class="st-team-change">' + escape(previous) + '</span>' : '') +
        '</td>' +
        '<td class="st-num">' + row.goals + '</td>' +
        '<td class="st-num">' + row.assists + '</td>' +
        '<td class="st-num">' + row.blocks + '</td>' +
        '</tr>';
    }).join('');
  }

  function markSort() {
    document.querySelectorAll('.stats-table th[data-sort]').forEach(function (th) {
      th.classList.toggle('is-sorted', th.dataset.sort === state.sort);
    });
  }

  function renderTabs() {
    var items = [{ id: 'all', title: 'Общий' }].concat(state.stages.map(function (stage) {
      return { id: stage.id, title: stage.title };
    }));
    tabs.innerHTML = items.map(function (item) {
      var active = String(item.id) === String(state.stage) ? ' is-active' : '';
      return '<button type="button" class="stage-switch__item' + active + '" data-stage="' + item.id + '">' +
        escape(item.title) + '</button>';
    }).join('');
  }

  function markStage() {
    tabs.querySelectorAll('[data-stage]').forEach(function (button) {
      button.classList.toggle('is-active', button.dataset.stage === String(state.stage));
    });
  }

  var genderTabs = document.getElementById('stats-gender');

  genderTabs.addEventListener('click', function (event) {
    var button = event.target.closest('[data-gender]');
    if (!button) return;
    state.gender = button.dataset.gender;
    genderTabs.querySelectorAll('[data-gender]').forEach(function (item) {
      item.classList.toggle('is-active', item === button);
    });
    render();
  });

  tabs.addEventListener('click', function (event) {
    var button = event.target.closest('[data-stage]');
    if (!button) return;
    state.stage = button.dataset.stage === 'all' ? 'all' : Number(button.dataset.stage);
    markStage();
    render();
  });

  document.querySelectorAll('.stats-table th[data-sort]').forEach(function (th) {
    th.addEventListener('click', function () {
      state.sort = th.dataset.sort;
      markSort();
      render();
    });
  });

  search.addEventListener('input', function () {
    state.query = search.value;
    render();
  });

  renderTabs();
  render();

  // живое обновление: если фэнтези ответил — берём свежие цифры, иначе остаёмся на снимке
  fetch('https://fantasy.iaroslavexe.art/api/league/stats', { headers: { Accept: 'application/json' } })
    .then(function (response) {
      if (!response.ok) throw new Error('bad status');
      return response.json();
    })
    .then(function (data) {
      if (!data || !data.players) return;
      var known = {};
      state.players.forEach(function (player) { known[player.id] = player; });

      state.players = data.players.map(function (player) {
        var previous = known[player.id];
        player.team = canon(player.team);
        player.teams_by_stage = (previous && previous.teams_by_stage) || {};
        player.teams = (previous && previous.teams) || (player.team ? [player.team] : []);
        return player;
      });
      var used = {};
      data.players.forEach(function (player) {
        Object.keys(player.by_stage || {}).forEach(function (key) { used[key] = true; });
      });
      state.stages = (data.stages || []).filter(function (stage) { return used[String(stage.id)]; });

      if (!state.stages.some(function (stage) { return String(stage.id) === String(state.stage); })) {
        state.stage = 'all';
      }
      renderTabs();

      render();
    })
    .catch(function () { /* снимок уже на экране */ });
})();
