// Страницы архива (команда, игрок, этап, игра) — рисуем на клиенте из одного JSON.
(function () {
  var root = document.getElementById('archive-app');
  if (!root) return;

  var cache = null;

  function load() {
    if (!cache) {
      cache = fetch('/static/data/archive.json').then(function (r) { return r.json(); });
    }
    return cache;
  }

  function el(tag, cls, html) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    if (html !== undefined) node.innerHTML = html;
    return node;
  }

  function link(href, text) {
    return '<a href="' + href + '">' + text + '</a>';
  }

  function fmtDate(iso) {
    if (!iso) return '';
    return iso.slice(8, 10) + '.' + iso.slice(5, 7) + '.' + iso.slice(0, 4);
  }

  function table(headers, rows) {
    var html = '<table class="archive-table"><thead><tr>' +
      headers.map(function (h) { return '<th>' + h + '</th>'; }).join('') +
      '</tr></thead><tbody>' +
      rows.map(function (row) {
        return '<tr>' + row.map(function (cell) { return '<td>' + cell + '</td>'; }).join('') + '</tr>';
      }).join('') + '</tbody></table>';
    return html;
  }

  function crumbs(parts) {
    return '<p class="crumbs">' + parts.map(function (p, i) {
      return i === parts.length - 1 ? p[1] : link(p[0], p[1]);
    }).join(' / ') + '</p>';
  }

  function stats(items) {
    return '<div class="archive-stats archive-stats--small">' + items.map(function (item) {
      return '<div class="archive-stat"><b>' + item[0] + '</b><span>' + item[1] + '</span></div>';
    }).join('') + '</div>';
  }

  function renderTeam(data, id) {
    var team = data.teams.filter(function (t) { return t.id === id; })[0];
    if (!team) return render404();
    var stageById = {};
    data.stages.forEach(function (s) { stageById[s.id] = s; });

    var stages = team.stages.slice().sort(function (a, b) {
      return stageById[a[0]].date.localeCompare(stageById[b[0]].date);
    }).map(function (row) {
      var stage = stageById[row[0]];
      var place = row[1];
      var medal = place === 1 ? (row[2] === 'Mid' ? 'medal--silver' : 'medal--gold') : '';
      return [fmtDate(stage.date), link('/archive/stage/' + stage.slug, stage.title),
        stage.division, '<span class="medal ' + medal + '">' + place + '</span>' + (row[2] ? ' <span class="archive-table__note">' + row[2] + '</span>' : '')];
    });

    var players = data.players.filter(function (p) {
      return p.seasons.some(function (s) { return s.teams.indexOf(id) >= 0; });
    }).sort(function (a, b) { return (b.goals + b.assists) - (a.goals + a.assists); })
      .map(function (p) {
        return [link('/archive/player/' + p.id, p.name), p.stages, p.goals, p.assists];
      });

    var spirit = (team.sotg_seasons || []).map(function (row) {
      return [row[0], row[1].toFixed(1)];
    });

    root.innerHTML =
      crumbs([['/archive', 'Архив'], ['/archive?tab=teams', 'Команды'], [null, team.name]]) +
      '<h1 class="archive-title">' + team.name + '</h1>' +
      (team.note ? '<p class="archive-lead">' + team.note + '</p>' : '') +
      stats([[team.stages.length, 'этапов'], [team.gold, 'золото'], [team.silver, 'серебро'],
        [team.wins + '–' + team.losses, 'победы'], [team.goals_for + '–' + team.goals_against, 'голы']]) +
      '<h2 class="archive-h2">Этапы</h2>' + table(['Дата', 'Этап', 'Дивизион', 'Место'], stages) +
      (spirit.length ? '<h2 class="archive-h2">Дух по сезонам</h2>' + table(['Сезон', 'Средний балл'], spirit) : '') +
      '<h2 class="archive-h2">Игроки</h2>' + table(['Игрок', 'Этапов', 'Голы', 'Ассисты'], players);
  }

  function renderPlayer(data, id) {
    var player = data.players.filter(function (p) { return p.id === id; })[0];
    if (!player) return render404();
    var teamById = {};
    data.teams.forEach(function (t) { teamById[t.id] = t; });
    var stageById = {};
    data.stages.forEach(function (s) { stageById[s.id] = s; });

    var seasons = player.seasons.map(function (s) {
      return [s.season, s.teams.map(function (t) { return link('/archive/team/' + t, (teamById[t] || {}).name || t); }).join(', '), s.stages];
    });

    var stages = (player.by_stage || []).map(function (row) {
      var stage = stageById[row[0]];
      if (!stage) return null;
      var teamIds = player.seasons.filter(function (s) { return s.season === stage.season; })
        .map(function (s) { return s.teams; }).reduce(function (a, b) { return a.concat(b); }, []);
      var place = '';
      stage.places.forEach(function (p) {
        if (teamIds.indexOf(p[0]) >= 0) place = p[1];
      });
      return [fmtDate(stage.date), link('/archive/stage/' + stage.slug, stage.title), place, row[1], row[2]];
    }).filter(Boolean);

    root.innerHTML =
      crumbs([['/archive', 'Архив'], ['/archive?tab=players', 'Игроки'], [null, player.name]]) +
      '<h1 class="archive-title">' + player.name + '</h1>' +
      (player.note ? '<p class="archive-lead">' + player.note + '</p>' : '') +
      stats([[player.stages, 'этапов'], [player.goals, 'голов'], [player.assists, 'ассистов'], [player.goals + player.assists, 'очков']]) +
      '<h2 class="archive-h2">Сезоны и команды</h2>' + table(['Сезон', 'Команды', 'Этапов'], seasons) +
      '<h2 class="archive-h2">По этапам</h2>' + table(['Дата', 'Этап', 'Место', 'Голы', 'Ассисты'], stages);
  }

  function renderStage(data, slug) {
    var stage = data.stages.filter(function (s) { return s.slug === slug; })[0];
    if (!stage) return render404();
    var teamById = {};
    data.teams.forEach(function (t) { teamById[t.id] = t; });

    var stageGames = data.games.filter(function (g) { return g.stage === stage.id; });
    var record = {};
    stageGames.forEach(function (g) {
      [[g.home, g.hs, g.vs], [g.away, g.vs, g.hs]].forEach(function (row) {
        var item = record[row[0]] || (record[row[0]] = { games: 0, wins: 0, losses: 0 });
        item.games += 1;
        if (row[1] > row[2]) item.wins += 1;
        if (row[1] < row[2]) item.losses += 1;
      });
    });

    var spirit = {};
    stage.sotg.forEach(function (row) { spirit[row[0]] = row[1]; });

    var seats = stage.places.slice().sort(function (a, b) {
      var da = a[2] === 'Mid' ? 1 : 0;
      var db = b[2] === 'Mid' ? 1 : 0;
      return da - db || a[1] - b[1];
    }).map(function (row) {
      var team = teamById[row[0]] || {};
      var medal = row[1] === 1 ? 'medal--gold' : '';
      var stats = record[row[0]] || { games: 0, wins: 0, losses: 0 };
      var avatar = team.avatar ? '<img class="team-avatar" src="' + team.avatar + '" alt="" loading="lazy">' : '';
      var name = avatar + link('/archive/team/' + row[0], team.name || row[0]) +
        (row[2] ? ' <span class="archive-table__note archive-table__note--inline">' + row[2] + '</span>' : '');
      return [
        '<span class="medal ' + medal + '">' + row[1] + '</span>',
        name,
        stats.games,
        stats.wins + '–' + stats.losses,
        spirit[row[0]] ? spirit[row[0]].toFixed(1) : '—'
      ];
    });

    var games = stageGames.map(function (g) {
      return [link('/archive/game/' + g.id, g.home_name + ' — ' + g.away_name), g.hs + ' : ' + g.vs];
    });

    root.innerHTML =
      crumbs([['/archive', 'Архив'], ['/archive?tab=stages', 'Этапы'], [null, stage.season]]) +
      '<h1 class="archive-title">' + stage.title + '</h1>' +
      '<p class="archive-lead">' + fmtDate(stage.date) + ' · ' + stage.division + ' дивизион · ' + stage.games_count + ' игр</p>' +
      '<h2 class="archive-h2">Итоги этапа</h2>' + table(['Место', 'Команда', 'Игр', 'В–П', 'Дух'], seats) +
      '<h2 class="archive-h2">Игры</h2>' + table(['Игра', 'Счёт'], games);
  }

  function renderGame(data, id) {
    var game = data.games.filter(function (g) { return String(g.id) === String(id); })[0];
    if (!game) return render404();
    var playerById = {};
    data.players.forEach(function (p) { playerById[p.id] = p; });
    var stage = data.stages.filter(function (s) { return s.id === game.stage; })[0];

    var timeline = game.timeline.map(function (row) {
      var scorer = playerById[row[2]] ? link('/archive/player/' + row[2], playerById[row[2]].name) : '—';
      var assist = row[3] && playerById[row[3]]
        ? '<span class="timeline__assist">ассист: ' + link('/archive/player/' + row[3], playerById[row[3]].name) + '</span>' : '';
      return '<li class="timeline__item"><span class="timeline__score">' + row[0] + ' : ' + row[1] +
        '</span><span class="timeline__player">' + scorer + assist + '</span></li>';
    }).join('');

    root.innerHTML =
      crumbs([['/archive', 'Архив'], stage ? ['/archive/stage/' + stage.slug, stage.title] : [null, 'Этап'], [null, 'игра']]) +
      '<h1 class="archive-title">' + game.home_name + ' <span class="archive-score">' + game.hs + ' : ' + game.vs + '</span> ' + game.away_name + '</h1>' +
      '<p class="archive-lead">' + fmtDate(game.date) + '</p>' +
      '<h2 class="archive-h2">Хронология очков</h2><ul class="timeline">' + timeline + '</ul>';
  }

  function render404() {
    root.innerHTML = '<p class="crumbs">' + link('/archive', 'Архив') + '</p>' +
      '<h1 class="archive-title">Не найдено</h1><p class="archive-lead">Такой записи в архиве нет.</p>';
  }

  load().then(function (data) {
    var path = window.location.pathname.replace(/\/$/, '');
    var parts = path.split('/').filter(Boolean); // ["archive", "team", "gadyuki"]
    var kind = parts[1], id = decodeURIComponent(parts[2] || '');
    if (kind === 'team') return renderTeam(data, id);
    if (kind === 'player') return renderPlayer(data, id);
    if (kind === 'stage') return renderStage(data, id);
    if (kind === 'game') return renderGame(data, id);
    render404();
  }).catch(function () {
    root.innerHTML = '<p class="archive-lead">Не удалось загрузить архив.</p>';
  });
})();
