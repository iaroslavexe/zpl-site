// Страницы архива (команда, игрок, этап, игра) — рисуем на клиенте из одного JSON.
(function () {
  var AWARDS = {
    season_mvp: { title: 'MVP сезона' },
    season_defense: { title: 'MVP сезона · защита' },
    regular_mvp: { title: 'MVP регулярного сезона' },
    regular_defense: { title: 'MVP регулярного сезона · защита' },
    regular_mvp_central: { title: 'MVP регулярного сезона · Центральный' },
    regular_defense_central: { title: 'MVP регулярного сезона · защита · Центральный' },
    regular_mvp_spb: { title: 'MVP регулярного сезона · Северо-западный' },
    regular_defense_spb: { title: 'MVP регулярного сезона · защита · Северо-западный' },
    final_mvp: { title: 'MVP финала' },
    final_defense: { title: 'MVP финала · защита' },
    final_mid_mvp: { title: 'MVP финала Mid', quiet: true },
    final_mid_defense: { title: 'MVP финала Mid · защита', quiet: true },
    offense: { title: 'Лучший в атаке' },
    defense: { title: 'Лучший в защите' },
    spirit_player: { title: 'Дух игры' },
    spirit_team: { title: 'Дух игры' },
    champion: { title: 'Чемпион сезона' },
    regular_winner_central: { title: 'Победитель регулярного сезона · Центральный' },
    regular_winner_spb: { title: 'Победитель регулярного сезона · Северо-западный' },
    mid_winner: { title: 'Победитель Mid дивизиона' }
  };

  var root = document.getElementById('archive-app');
  if (!root) return;

  var cache = null;

  function load() {
    if (!cache) {
      cache = fetch('/archive/data.json').then(function (r) { return r.json(); });
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
    return '<div class="archive-scroll">' + html + '</div>';
  }

  function crumbs(parts) {
    return '<p class="crumbs">' + parts.map(function (p, i) {
      return i === parts.length - 1 ? p[1] : link(p[0], p[1]);
    }).join(' / ') + '</p>';
  }

  function plural(n, one, few, many) {
    if (n % 10 === 1 && n % 100 !== 11) return one;
    if (n % 10 >= 2 && n % 10 <= 4 && (n % 100 < 12 || n % 100 > 14)) return few;
    return many;
  }

  function stats(items) {
    return '<div class="archive-stats archive-stats--small">' + items.map(function (item) {
      return '<div class="archive-stat"><b>' + item[0] + '</b><span>' + item[1] + '</span></div>';
    }).join('') + '</div>';
  }

  function sortableTable(headers, rows) {
    var html = '<table class="archive-table archive-table--sortable" data-sortable><thead><tr>' +
      headers.map(function (h, i) {
        return '<th data-sort="' + i + '">' + h + '</th>';
      }).join('') + '</tr></thead><tbody>' +
      rows.map(function (row) {
        return '<tr>' + row.map(function (cell) { return '<td>' + cell + '</td>'; }).join('') + '</tr>';
      }).join('') + '</tbody></table>';
    return '<div class="archive-scroll">' + html + '</div>';
  }

  function enableSorting(scope) {
    scope.querySelectorAll('table[data-sortable]').forEach(function (table) {
      table.querySelectorAll('th[data-sort]').forEach(function (header) {
        header.style.cursor = 'pointer';
        header.addEventListener('click', function () {
          var index = Number(header.dataset.sort);
          var body = table.tBodies[0];
          var rows = Array.prototype.slice.call(body.rows);
          var dir = header.dataset.dir === 'desc' ? 1 : -1;
          rows.sort(function (a, b) {
            var ta = a.cells[index].textContent.trim();
            var tb = b.cells[index].textContent.trim();
            var na = parseFloat(ta.replace(',', '.'));
            var nb = parseFloat(tb.replace(',', '.'));
            if (!isNaN(na) && !isNaN(nb)) return (na - nb) * dir;
            return ta.localeCompare(tb, 'ru') * dir;
          });
          rows.forEach(function (row) { body.appendChild(row); });
          table.querySelectorAll('th').forEach(function (h) { h.dataset.dir = ''; });
          header.dataset.dir = dir === -1 ? 'asc' : 'desc';
        });
      });
    });
  }

  var SPIRIT_FLAME = '<svg viewBox="0 0 48 48" width="15" height="15" aria-hidden="true">' +
    '<path d="M24 2c2.5 7 6 9 8.5 13S37 24 37 28c0 8-5.8 15-13 15S11 36 11 28c0-4 2-7 4-9.5-.5 3 .5 5 2 6C16 17 18 9 24 2z" fill="currentColor"/></svg>';

  function renderTeam(data, id) {
    var team = data.teams.filter(function (t) { return t.id === id; })[0];
    if (!team) return render404();
    var stageById = {};
    data.stages.forEach(function (s) { stageById[s.id] = s; });

    var titles = (data.champions || []).filter(function (c) { return c.team === id; });
    var spiritSeasons = (data.awards || []).filter(function (a) {
      return a.type === 'spirit_team' && (a.teams || []).indexOf(id) >= 0;
    }).map(function (a) { return a.season; });

    var badges = [];
    titles.forEach(function (c) {
      badges.push('<span class="team-title__icon" data-tip="Чемпионство ' + c.season + '">★</span>');
    });
    spiritSeasons.forEach(function (season) {
      badges.push('<span class="team-title__flame" data-tip="Дух ' + season + '">' + SPIRIT_FLAME + '</span>');
    });
    var titleBadge = badges.length ? '<span class="team-title">' + badges.join('') + '</span>' : '';

    var seasonRows = (team.season_stats || []).map(function (s) {
      return [
        s.season,
        s.best || '',
        s.stages,
        s.games,
        s.wins + '–' + s.losses,
        s.goals_for + '–' + s.goals_against,
        s.spirit ? s.spirit.toFixed(1) : '—'
      ];
    });

    var stageRows = [];
    var bySeason = {};
    team.stages.forEach(function (row) {
      var stage = stageById[row[0]];
      if (!stage) return;
      (bySeason[stage.season] || (bySeason[stage.season] = [])).push({ stage: stage, place: row[1] });
    });
    Object.keys(bySeason).sort().forEach(function (season) {
      stageRows.push(['<span class="archive-season__label">' + season + '</span>', '']);
      bySeason[season].forEach(function (item) {
        var medal = item.place === 1 ? 'medal--gold' : '';
        stageRows.push([
          '<a href="/archive/stage/' + item.stage.slug + '">' + (item.stage.name || item.stage.title) + '</a>',
          '<span class="medal ' + medal + '">' + item.place + '</span>'
        ]);
      });
    });

    var players = data.players.map(function (p) {
      var own = { stages: 0, games: 0, goals: 0, assists: 0 };
      (p.by_stage || []).forEach(function (row) {
        if (row[3] !== id) return;
        own.stages += 1;
        own.games += row[4] || 0;
        own.goals += row[1];
        own.assists += row[2];
      });
      return { player: p, own: own };
    }).filter(function (item) {
      return item.own.stages > 0;
    }).sort(function (a, b) {
      var pa = a.own.goals + a.own.assists, pb = b.own.goals + b.own.assists;
      return pb - pa || b.own.stages - a.own.stages;
    }).map(function (item) {
      var p = item.player, own = item.own;
      return [link('/archive/player/' + p.id, p.name), own.stages, own.games,
        own.goals + own.assists, own.goals, own.assists];
    });

    root.innerHTML =
      crumbs([['/archive', 'Архив'], ['/archive/teams', 'Команды'], [null, team.name]]) +
      '<div class="archive-player__head">' +
        '<h1 class="archive-title">' + team.name + titleBadge + '</h1>' +
        (team.avatar ? '<img class="archive-player__avatar" src="' + team.avatar + '" alt="" loading="lazy">' : '') +
      '</div>' +
      (team.note ? '<p class="archive-lead">' + team.note + '</p>' : '') +
      stats([[team.stages.length, plural(team.stages.length, 'этап', 'этапа', 'этапов')],
        [team.gold + team.silver, plural(team.gold + team.silver, 'победа', 'победы', 'побед')],
        [team.games, plural(team.games, 'игра', 'игры', 'игр')], [team.wins + '–' + team.losses, 'победы'],
        [team.goals_for + '–' + team.goals_against, 'голы']]) +
      '<h2 class="archive-h2">Сезоны</h2>' +
      table(['Сезон', 'Лучшее место', 'Этапов', 'Игр', 'В–П', 'Голы', 'Дух'], seasonRows) +
      '<h2 class="archive-h2">Этапы</h2>' +
      table(['Этап', 'Место'], stageRows) +
      '<h2 class="archive-h2">Игроки</h2>' +
      sortableTable(['Игрок', 'Этапов', 'Игр', 'Очки', 'Голы', 'Ассисты'], players);

    enableSorting(root);
  }

  var SPIRIT_FLAME_SMALL = '<svg viewBox="0 0 48 48" width="17" height="17" aria-hidden="true">' +
    '<path d="M24 2c2.5 7 6 9 8.5 13S37 24 37 28c0 8-5.8 15-13 15S11 36 11 28c0-4 2-7 4-9.5-.5 3 .5 5 2 6C16 17 18 9 24 2z" fill="currentColor"/></svg>';

  function awardMark(award) {
    if (award.type === 'champion') return '<span class="awards-star">★</span>';
    if (award.type === 'regular_winner_central' || award.type === 'regular_winner_spb') {
      return '<span class="awards-star awards-star--regular">★</span>';
    }
    if (award.type === 'mid_winner') return '<span class="awards-star awards-star--mid">☆</span>';
    if (award.type === 'spirit_team') return '<span class="spirit-flame">' + SPIRIT_FLAME_SMALL + '</span>';
    return '<span class="mvp-badge' + (award.quiet ? ' mvp-badge--quiet' : '') + '">MVP</span>';
  }

  function awardsBlock(data, player) {
    var stageById = {};
    data.stages.forEach(function (s) { stageById[s.id] = s; });
    var teamById = {};
    data.teams.forEach(function (t) { teamById[t.id] = t; });

    var items = [];

    (data.awards || []).forEach(function (award) {
      if ((award.players || []).indexOf(player.id) >= 0) {
        items.push({ award: award, teamId: null });
      }
    });

    // командные заслуги: сезонные — ≥2 этапа за команду;
    // в 24/25–25/26 регулярка и финал считаются отдельно
    var perSeasonTeam = {};
    (player.by_stage || []).forEach(function (row) {
      var stage = stageById[row[0]];
      if (!stage || !row[3]) return;
      var season = perSeasonTeam[stage.season] || (perSeasonTeam[stage.season] = {});
      var stat = season[row[3]] || (season[row[3]] = { stages: 0, regular: 0, final: false });
      stat.stages += 1;
      if ((stage.name || '').indexOf('Финал') >= 0) {
        stat.final = true;
      } else {
        stat.regular += 1;
      }
    });

    function teamAwardFits(award, stat) {
      if (!stat) return false;
      var splitSeason = award.season === '2024/25' || award.season === '2025/26';
      if (!splitSeason) return stat.stages >= 2;
      if (award.type === 'champion' || award.type === 'mid_winner') return stat.final;
      if (award.type === 'regular_winner_central' || award.type === 'regular_winner_spb') return stat.regular >= 2;
      return stat.stages >= 2;
    }

    (data.awards || []).forEach(function (award) {
      if (!(award.teams || []).length) return;
      var seasonTeams = perSeasonTeam[award.season] || {};
      award.teams.forEach(function (tid) {
        if (teamAwardFits(award, seasonTeams[tid])) {
          items.push({ award: award, teamId: tid });
        }
      });
    });

    if (!items.length) return '';

    items.sort(function (a, b) {
      if (a.award.season !== b.award.season) return a.award.season < b.award.season ? 1 : -1;
      return 0;
    });

    var rows = items.map(function (item) {
      var award = item.award;
      var meta = AWARDS[award.type] || { title: award.type };
      var team = item.teamId ? teamById[item.teamId] : null;
      return '<div class="awards-row">' +
        '<span class="awards-row__mark">' + awardMark(award) + '</span>' +
        '<span class="awards-row__title">' + meta.title +
          (team ? '<span class="awards-row__team"> · ' + team.name + '</span>' : '') + '</span>' +
        '<span class="archive-table__note">' + award.season + '</span></div>';
    }).join('');

    return '<h2 class="archive-h2">Награды</h2><div class="awards awards--compact">' + rows + '</div>';
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
    var bySeason = {};

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

      var team = row[3] ? teamById[row[3]] : null;
      var teamCell = team
        ? '<a class="stage-team" href="/archive/team/' + team.id + '">' +
          (team.avatar ? '<img class="team-avatar" src="' + team.avatar + '" alt="" loading="lazy">' : '') +
          '<span>' + team.name + '</span></a>'
        : '';

      (bySeason[stage.season] || (bySeason[stage.season] = [])).push([
        '<a href="/archive/stage/' + stage.slug + '">' + (stage.name || stage.title) + '</a>',
        teamCell,
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
        var team = teamById[tid] || {};
        return '<a class="stage-team" href="/archive/team/' + tid + '">' +
          (team.avatar ? '<img class="team-avatar" src="' + team.avatar + '" alt="" loading="lazy">' : '') +
          '<span>' + (team.name || tid) + '</span></a>';
      }).join('<span class="team-sep">/</span>');
      return [item.season, teams, item.stages, item.games, item.goals + item.assists, item.goals, item.assists];
    });

    function stageTable() {
      var head = '<thead><tr><th>Этап</th><th>Команда</th><th>Место</th><th>Игр</th><th>Очки</th><th>Голы</th><th>Ассисты</th></tr></thead>';
      var body = Object.keys(bySeason).sort().map(function (season) {
        var rows = bySeason[season].map(function (cells) {
          return '<tr>' + cells.map(function (c) { return '<td>' + c + '</td>'; }).join('') + '</tr>';
        }).join('');
        return '<tbody class="archive-season"><tr class="archive-season__row"><td colspan="7">' + season + '</td></tr>' + rows + '</tbody>';
      }).join('');
      return '<div class="archive-scroll"><table class="archive-table archive-table--stages">' + head + body + '</table></div>';
    }

    var avatar = player.avatar
      ? '<img class="archive-player__avatar" src="' + player.avatar + '" alt="" loading="lazy">'
      : '';

    var points = totals.goals + totals.assists;

    root.innerHTML =
      crumbs([['/archive', 'Архив'], ['/archive/players', 'Игроки'], [null, player.name]]) +
      '<div class="archive-player">' +
        '<div class="archive-player__head">' +
          '<h1 class="archive-title">' + player.name + '</h1>' + avatar +
        '</div>' +
        (player.note ? '<p class="archive-lead">' + player.note + '</p>' : '') +
        stats([
          [totals.stages, plural(totals.stages, 'этап', 'этапа', 'этапов')],
          [totals.games, plural(totals.games, 'игра', 'игры', 'игр')],
          [points, plural(points, 'очко', 'очка', 'очков')],
          [totals.goals, plural(totals.goals, 'гол', 'гола', 'голов')],
          [totals.assists, plural(totals.assists, 'ассист', 'ассиста', 'ассистов')]
        ]) +
        awardsBlock(data, player) +
        '<h2 class="archive-h2">Сезоны и команды</h2>' +
        table(['Сезон', 'Команды', 'Этапов', 'Игр', 'Очки', 'Голы', 'Ассисты'], seasonsRows) +
        '<h2 class="archive-h2">По этапам</h2>' +
        stageTable() +
      '</div>';
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
      crumbs([['/archive', 'Архив'], ['/archive/stages', 'Этапы'],
        stage ? ['/archive/stage/' + stage.slug, stage.season + ' · ' + (stage.name || stage.title)] : [null, 'Этап'],
        [null, 'игра']]) +
      '<h1 class="archive-title">' + game.home_name + ' <span class="archive-score">' + game.hs + ' : ' + game.vs + '</span> ' + game.away_name + '</h1>' +
      '<p class="archive-lead">' + fmtDate(game.date) + '</p>' +
      '<h2 class="archive-h2">Хронология очков</h2><ul class="timeline">' + timeline + '</ul>';
  }

  // Подсказки к бейджам наград
  (function () {
    var tip = null;
    function box() {
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
      var node = box();
      node.textContent = el.getAttribute('data-tip');
      node.classList.add('is-on');
      var rect = el.getBoundingClientRect();
      var left = Math.min(rect.left, window.innerWidth - node.offsetWidth - 12);
      var top = rect.bottom + 8;
      if (top + node.offsetHeight > window.innerHeight - 8) top = rect.top - node.offsetHeight - 8;
      node.style.left = Math.max(8, left) + 'px';
      node.style.top = Math.max(8, top) + 'px';
    });
    document.addEventListener('mouseout', function (event) {
      if (event.target.closest('[data-tip]') && tip) tip.classList.remove('is-on');
    });
  })();

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
