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

    var totals = { stages: 0, games: 0, goals: 0, assists: 0 };
    var seasonStats = {};
    var rows = [];

    (player.by_stage || []).forEach(function (row) {
      var stage = stageById[row[0]];
      if (!stage) return;
      var games = row[4] || 0;
      totals.stages += 1;
      totals.games += games;
      totals.goals += row[1];
      totals.assists += row[2];

      var season = seasonStats[stage.season] || (seasonStats[stage.season] = {
        season: stage.season, teams: {}, stages: 0, games: 0, goals: 0, assists: 0
      });
      season.stages += 1;
      season.games += games;
      season.goals += row[1];
      season.assists += row[2];
      if (row[3]) season.teams[row[3]] = 1;

      var place = '';
      stage.places.forEach(function (p) {
        if (row[3] && p[0] === row[3]) place = p[1];
      });

      rows.push([
        '<a href="/archive/stage/' + stage.slug + '">' + stage.season + ' · ' + (stage.name || stage.title) + '</a>',
        place,
        games,
        row[1] + row[2],
        row[1],
        row[2]
      ]);
    });

    var seasonsRows = Object.keys(seasonStats).sort().map(function (key) {
      var item = seasonStats[key];
      var teams = Object.keys(item.teams).map(function (tid) {
        return link('/archive/team/' + tid, (teamById[tid] || {}).name || tid);
      }).join(', ');
      return [item.season, teams, item.stages, item.games, item.goals + item.assists, item.goals, item.assists];
    });

    var avatar = player.avatar
      ? '<img class="archive-player__avatar" src="' + player.avatar + '" alt="" loading="lazy">'
      : '';

    root.innerHTML =
      crumbs([['/archive', 'Архив'], ['/archive/players', 'Игроки'], [null, player.name]]) +
      '<div class="archive-player">' +
        '<div class="archive-player__head">' +
          '<h1 class="archive-title">' + player.name + '</h1>' + avatar +
        '</div>' +
        (player.note ? '<p class="archive-lead">' + player.note + '</p>' : '') +
        stats([[totals.stages, 'этапов'], [totals.games, 'игр'],
               [totals.goals + totals.assists, 'очков'], [totals.goals, 'голов'], [totals.assists, 'ассистов']]) +
        '<h2 class="archive-h2">Сезоны и команды</h2>' +
        table(['Сезон', 'Команды', 'Этапов', 'Игр', 'Очки', 'Голы', 'Ассисты'], seasonsRows) +
        '<h2 class="archive-h2">По этапам</h2>' +
        table(['Этап', 'Место', 'Игр', 'Очки', 'Голы', 'Ассисты'], rows) +
      '</div>';
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

    var groups = {};
    stageGames.slice().sort(function (a, b) {
      return (a.group_order || 99) - (b.group_order || 99) || a.id - b.id;
    }).forEach(function (g) {
      var label = g.group || 'Игры';
      (groups[label] || (groups[label] = [])).push(g);
    });

    function standings(games) {
      var stats = {};
      games.forEach(function (g) {
        [[g.home, g.hs, g.vs], [g.away, g.vs, g.hs]].forEach(function (row) {
          var item = stats[row[0]] || (stats[row[0]] = { wins: 0, losses: 0, diff: 0 });
          item.diff += row[1] - row[2];
          if (row[1] > row[2]) item.wins += 1;
          if (row[1] < row[2]) item.losses += 1;
        });
      });
      return Object.keys(stats).sort(function (a, b) {
        return stats[b].wins - stats[a].wins || stats[b].diff - stats[a].diff;
      }).map(function (id, index) {
        var team = teamById[id] || {};
        var avatar = team.avatar ? '<img class="team-avatar" src="' + team.avatar + '" alt="" loading="lazy">' : '';
        return [index + 1, avatar + link('/archive/team/' + id, team.name || id), stats[id].wins,
          stats[id].losses, (stats[id].diff > 0 ? '+' : '') + stats[id].diff];
      });
    }

    function gameRow(g) {
      var home = teamById[g.home] || {};
      var away = teamById[g.away] || {};
      var homeWin = g.hs > g.vs ? ' is-win' : '';
      var awayWin = g.vs > g.hs ? ' is-win' : '';
      return '<a class="game-row" href="/archive/game/' + g.id + '">' +
        '<span class="game-row__time"></span>' +
        '<span class="game-row__team game-row__team--home' + homeWin + '">' +
          (home.avatar ? '<img src="' + home.avatar + '" alt="" loading="lazy">' : '') +
          '<span class="game-row__name">' + (home.name || g.home_name) + '</span></span>' +
        '<span class="game-row__score">' + g.hs + ' : ' + g.vs + '</span>' +
        '<span class="game-row__team game-row__team--away' + awayWin + '">' +
          '<span class="game-row__name">' + (away.name || g.away_name) + '</span>' +
          (away.avatar ? '<img src="' + away.avatar + '" alt="" loading="lazy">' : '') + '</span>' +
      '</a>';
    }

    var gamesHtml = Object.keys(groups).map(function (label) {
      var items = groups[label];
      var solo = items.length === 1 && label.indexOf('Группа') !== 0;
      var block = '<section class="archive-block' + (solo ? ' archive-block--solo' : '') + '">';
      block += '<h3 class="archive-group">' + label + '</h3>';
      var teamsInBlock = {};
      items.forEach(function (g) { teamsInBlock[g.home] = 1; teamsInBlock[g.away] = 1; });
      var teamCount = Object.keys(teamsInBlock).length;
      var fullRound = teamCount * (teamCount - 1) / 2;
      var isRoundRobin = teamCount > 2 && (items.length === fullRound || items.length === fullRound * 2);
      if (isRoundRobin) {
        block += '<div class="group-standings">' +
          table(['#', 'Команда', 'В', 'П', '+/–'], standings(items)) + '</div>';
      }
      block += '<div class="games">' + items.map(gameRow).join('') + '</div></section>';
      return block;
    }).join('');

    root.innerHTML =
      crumbs([['/archive', 'Архив'], ['/archive?tab=stages', 'Этапы'], [null, stage.season]]) +
      '<h1 class="archive-title">' + stage.season + ' · ' + (stage.name || stage.title) + '</h1>' +
      '<p class="archive-lead">' + (stage.city || '') + ' · ' + fmtDate(stage.date) +
      ' · ' + stage.division + ' дивизион · ' + stage.games_count + ' игр</p>' +
      '<h2 class="archive-h2">Итоги этапа</h2>' + table(['Место', 'Команда', 'Игр', 'В–П', 'Дух'], seats) +
      '<h2 class="archive-h2">Игры</h2>' + gamesHtml;
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
