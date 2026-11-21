/* آوا | AVA Music Archive — shared UI behaviour
   Every block is defensive: the same file is loaded on all pages. */
(function () {
  "use strict";

  const root = document.documentElement;
  const $ = (sel, ctx) => (ctx || document).querySelector(sel);
  const $$ = (sel, ctx) => Array.prototype.slice.call((ctx || document).querySelectorAll(sel));
  const faNum = (n) => String(n).replace(/\d/g, (d) => "۰۱۲۳۴۵۶۷۸۹"[d]);
  const faTime = (s) => {
    s = Math.max(0, Math.round(s));
    return faNum(Math.floor(s / 60)) + ":" + faNum(String(s % 60).padStart(2, "0"));
  };

  /* ---------- theme ---------- */
  const themeBtn = $("#themeBtn");
  const savedTheme = (function () {
    try { return localStorage.getItem("ava-theme"); } catch (e) { return null; }
  })();
  if (savedTheme === "light" || savedTheme === "dark") root.dataset.theme = savedTheme;
  const themeColor = $('meta[name="theme-color"]');

  function labelTheme() {
    const dark = root.dataset.theme === "dark";
    if (themeBtn) {
      themeBtn.setAttribute("aria-checked", String(dark));
      themeBtn.setAttribute("aria-label", dark ? "حالت روز" : "حالت شب");
      themeBtn.title = dark ? "روشن کردن" : "تیره کردن";
    }
    if (themeColor) themeColor.setAttribute("content", dark ? "#091540" : "#f9dbba");
  }
  labelTheme();
  if (themeBtn) {
    themeBtn.addEventListener("click", function () {
      root.dataset.theme = root.dataset.theme === "dark" ? "light" : "dark";
      try { localStorage.setItem("ava-theme", root.dataset.theme); } catch (e) {}
      labelTheme();
    });
  }

  /* ---------- mobile navigation ---------- */
  const menuBtn = $("#menuBtn");
  const nav = $("#navLinks");
  if (menuBtn && nav) {
    menuBtn.addEventListener("click", function () {
      const open = nav.classList.toggle("open");
      menuBtn.setAttribute("aria-expanded", String(open));
    });
    $$("a", nav).forEach(function (a) {
      a.addEventListener("click", function () {
        nav.classList.remove("open");
        menuBtn.setAttribute("aria-expanded", "false");
      });
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && nav.classList.contains("open")) {
        nav.classList.remove("open");
        menuBtn.setAttribute("aria-expanded", "false");
        menuBtn.focus();
      }
    });
  }

  /* ---------- toast ---------- */
  let toastTimer;
  function toast(message) {
    let el = $("#toast");
    if (!el) {
      el = document.createElement("div");
      el.id = "toast";
      el.className = "toast";
      el.setAttribute("role", "status");
      document.body.appendChild(el);
    }
    el.textContent = message;
    el.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { el.classList.remove("show"); }, 2400);
  }

  /* ---------- header search ---------- */
  const searchForm = $("#searchForm");
  const searchInput = $("#search");
  if (searchForm && searchInput) {
    searchForm.addEventListener("submit", function (e) {
      e.preventDefault();
      const q = searchInput.value.trim();
      if (document.body.dataset.page === "home") {
        $$(".music-post").forEach(function (post) {
          post.hidden = q ? post.innerText.toLowerCase().indexOf(q.toLowerCase()) === -1 : false;
        });
        return;
      }
      window.location.href = "search.html" + (q ? "?q=" + encodeURIComponent(q) : "");
    });
    if (document.body.dataset.page === "home") {
      searchInput.addEventListener("input", function () {
        const q = searchInput.value.trim().toLowerCase();
        $$(".music-post").forEach(function (post) {
          post.hidden = q ? post.innerText.toLowerCase().indexOf(q) === -1 : false;
        });
      });
    }
  }

  /* ---------- demo forms ---------- */
  $$("[data-demo-form]").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      const required = $$("[required]", form);
      const empty = required.filter(function (el) { return !String(el.value).trim(); });
      if (empty.length) {
        empty[0].focus();
        toast("لطفاً فیلدهای ستاره‌دار را کامل کنید.");
        return;
      }
      const msg = $(".form-msg", form);
      if (msg) {
        msg.textContent = form.dataset.success || "پیام شما ثبت شد. به‌زودی پاسخ می‌دهیم.";
        msg.classList.add("show");
      }
      toast(form.dataset.toast || "با موفقیت ارسال شد.");
      form.reset();
      if (form.dataset.resetFile !== undefined) {
        const name = $(".file-name", form);
        if (name) name.textContent = "فایل خود را انتخاب کنید یا اینجا رها کنید";
      }
    });
  });

  /* file picker label */
  $$(".file-input").forEach(function (input) {
    input.addEventListener("change", function () {
      const label = $(".file-name", input.closest("label") || input.parentElement);
      if (label && input.files && input.files[0]) label.textContent = input.files[0].name;
    });
  });

  /* ---------- comments ---------- */
  const csrfToken = (function () {
    const meta = document.querySelector('meta[name="csrf-token"]');
    if (meta && meta.content) return meta.content;
    const input = document.querySelector('input[name="csrfmiddlewaretoken"]');
    return input ? input.value : "";
  })();

  const commentForm = $("#commentForm");
  if (commentForm) {
    const commentMsg = $(".form-msg", commentForm);
    commentForm.addEventListener("submit", function (e) {
      e.preventDefault();
      const textField = commentForm.elements.body;
      const text = textField ? textField.value.trim() : "";
      if (!text) { toast("متن دیدگاه را بنویسید."); return; }
      const submit = $("button[type=submit]", commentForm);
      if (submit) submit.disabled = true;
      fetch(commentForm.action, {
        method: "POST",
        body: new FormData(commentForm),
        headers: { "X-Requested-With": "XMLHttpRequest" },
        credentials: "same-origin"
      })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (!data.ok) {
            if (commentMsg) commentMsg.textContent = data.error || "ارسال دیدگاه ممکن نشد.";
            toast(data.error || "ارسال دیدگاه ممکن نشد.");
            return;
          }
          const list = $("#commentList");
          const empty = $(".comment-empty", list);
          if (empty) empty.remove();
          if (list) {
            const row = document.createElement("div");
            row.className = "comment";
            const initial = document.createElement("span");
            initial.className = "avatar";
            initial.textContent = data.initial || "؟";
            const body = document.createElement("div");
            const head = document.createElement("div");
            head.className = "comment-head";
            const b = document.createElement("b");
            b.textContent = data.name;
            const time = document.createElement("time");
            time.textContent = "همین حالا";
            head.appendChild(b);
            head.appendChild(time);
            const p = document.createElement("p");
            p.textContent = data.body;
            body.appendChild(head);
            body.appendChild(p);
            row.appendChild(initial);
            row.appendChild(body);
            list.appendChild(row);
          }
          commentForm.reset();
          if (commentMsg) commentMsg.textContent = "";
          toast("دیدگاه شما ثبت شد.");
        })
        .catch(function () { toast("ارتباط با سرور برقرار نشد."); })
        .then(function () { if (submit) submit.disabled = false; });
    });
  }

  /* ---------- shared audio player ---------- */
  const dock = $("#audioDock");
  const dockTitle = $("#dockTitle");
  const dockArtist = $("#dockArtist");
  const dockPlay = $("#playPause");
  const dockBar = $("#dockBar");
  const dockCur = $("#dockCur");
  const dockDurEl = $("#dockDur");
  const songPlayer = $("[data-song-player]");
  const bigBtn = songPlayer ? $("[data-player-toggle]", songPlayer) : null;
  const bigBar = songPlayer ? $("[data-player-bar]", songPlayer) : null;
  const bigTime = songPlayer ? $("[data-player-time]", songPlayer) : null;
  const audio = $("[data-player-audio]") || new Audio();
  audio.preload = "metadata";

  function paintPlayer() {
    const dur = isFinite(audio.duration) && audio.duration > 0 ? audio.duration : 0;
    const cur = audio.currentTime || 0;
    const pct = dur ? Math.min(100, (cur / dur) * 100) : 0;
    if (dockBar) dockBar.style.width = pct + "%";
    if (dockCur) dockCur.textContent = faTime(cur);
    if (dockDurEl && dur) dockDurEl.textContent = faTime(dur);
    if (bigBar) bigBar.style.width = pct + "%";
    if (bigTime) bigTime.textContent = faTime(cur);
    const on = !audio.paused && !audio.ended;
    if (dockPlay) {
      dockPlay.textContent = on ? "⏸" : "▶";
      dockPlay.setAttribute("aria-label", on ? "توقف" : "پخش");
    }
    if (bigBtn) {
      bigBtn.textContent = on ? "⏸" : "▶";
      bigBtn.setAttribute("aria-label", on ? "توقف" : "پخش");
    }
    if (songPlayer) songPlayer.classList.toggle("playing", on);
  }

  function openDock(title, artist) {
    if (!dock) return;
    if (dockTitle) dockTitle.textContent = title || "پخش نمونه";
    if (dockArtist) dockArtist.textContent = artist || "آوا موزیک";
    dock.classList.add("is-open");
  }

  const HISTORY_KEY = "nava.player.history";
  const CURRENT_KEY = "nava.player.current";
  const HISTORY_LIMIT = 30;

  function readStored(key) {
    try {
      const raw = window.localStorage.getItem(key);
      const value = raw ? JSON.parse(raw) : null;
      return value;
    } catch (e) {
      return null;
    }
  }

  function writeStored(key, value) {
    try {
      window.localStorage.setItem(key, JSON.stringify(value));
    } catch (e) {
      /* storage unavailable (private mode) — history just won't persist */
    }
  }

  function readHistory() {
    const list = readStored(HISTORY_KEY);
    return Array.isArray(list) ? list : [];
  }

  function currentTrack() {
    const track = readStored(CURRENT_KEY);
    return track && track.url ? track : null;
  }

  function slugFromStream(url) {
    const match = String(url || "").match(/\/songs\/([^/]+)\/stream\/?/);
    return match ? decodeURIComponent(match[1]) : "";
  }

  function pushHistory(track) {
    if (!track || !track.url) return;
    const list = readHistory().filter(function (item) { return item.url !== track.url; });
    list.unshift({ url: track.url, title: track.title || "", artist: track.artist || "" });
    writeStored(HISTORY_KEY, list.slice(0, HISTORY_LIMIT));
  }

  function playItem(url, title, artist, options) {
    const opts = options || {};
    openDock(title, artist);
    if (!url) {
      toast("فایل صوتی این آهنگ در دسترس نیست.");
      return;
    }
    const target = new URL(url, window.location.href).href;
    if (audio.src !== target) {
      const previous = currentTrack();
      if (!opts.skipHistory && previous && previous.url !== url) pushHistory(previous);
      audio.src = target;
    }
    writeStored(CURRENT_KEY, { url: url, title: title || "", artist: artist || "" });
    const result = audio.play();
    if (result && result.catch) {
      result.catch(function () { toast("پخش امکان‌پذیر نشد؛ دوباره تلاش کنید."); });
    }
    paintPlayer();
  }

  function playRandomSong() {
    if (!dock) return;
    const randomUrl = dock.dataset.randomUrl || "";
    if (!randomUrl) {
      toast("پخش تصادفی در دسترس نیست.");
      return;
    }
    const previous = currentTrack();
    const exclude = previous ? slugFromStream(previous.url) : "";
    const endpoint = exclude
      ? randomUrl + "?exclude=" + encodeURIComponent(exclude)
      : randomUrl;

    fetch(endpoint, { headers: { "X-Requested-With": "XMLHttpRequest" } })
      .then(function (response) { return response.json(); })
      .then(function (data) {
        if (!data.ok || !data.stream) {
          toast(data.detail || "آهنگ تصادفی پیدا نشد.");
          return;
        }
        playItem(data.stream, data.title, data.artist);
      })
      .catch(function () { toast("ارتباط با سرور برقرار نشد."); });
  }

  function playPreviousSong() {
    const history = readHistory();
    const last = history.shift();
    if (!last) {
      audio.currentTime = 0;
      paintPlayer();
      return;
    }
    writeStored(HISTORY_KEY, history);
    playItem(last.url, last.title, last.artist, { skipHistory: true });
  }

  audio.addEventListener("loadedmetadata", paintPlayer);
  audio.addEventListener("timeupdate", paintPlayer);
  audio.addEventListener("play", paintPlayer);
  audio.addEventListener("pause", paintPlayer);
  audio.addEventListener("ended", function () {
    if (repeatOn) return;
    if (shuffleOn) {
      playRandomSong();
      return;
    }
    audio.currentTime = 0;
    paintPlayer();
  });

  if (dockPlay) {
    dockPlay.addEventListener("click", function () {
      if (!dock || !dock.classList.contains("is-open")) {
        openDock(dockTitle ? dockTitle.textContent : "پخش نمونه", dockArtist ? dockArtist.textContent : "آوا موزیک");
        return;
      }
      if (!audio.src) {
        toast("ابتدا یک آهنگ را انتخاب کنید.");
        return;
      }
      if (audio.paused) {
        const result = audio.play();
        if (result && result.catch) result.catch(function () {});
      } else {
        audio.pause();
      }
    });
  }

  const closeDock = $("#closeDock");
  if (closeDock) {
    closeDock.addEventListener("click", function () {
      audio.pause();
      if (dock) dock.classList.remove("is-open");
    });
  }

  const dockShuffle = $("[data-dock-shuffle]");
  const dockRepeat = $("[data-dock-repeat]");
  const dockRandom = $("[data-dock-random]");
  const dockHistory = $("[data-dock-history]");
  let shuffleOn = false;
  let repeatOn = false;

  if (dockShuffle) {
    dockShuffle.addEventListener("click", function () {
      shuffleOn = !shuffleOn;
      dockShuffle.classList.toggle("is-on", shuffleOn);
      dockShuffle.setAttribute("aria-pressed", shuffleOn ? "true" : "false");
      toast(shuffleOn ? "پخش تصادفی روشن شد." : "پخش تصادفی خاموش شد.");
    });
  }

  if (dockRepeat) {
    dockRepeat.addEventListener("click", function () {
      repeatOn = !repeatOn;
      audio.loop = repeatOn;
      dockRepeat.classList.toggle("is-on", repeatOn);
      dockRepeat.setAttribute("aria-pressed", repeatOn ? "true" : "false");
      toast(repeatOn ? "تکرار آهنگ روشن شد." : "تکرار آهنگ خاموش شد.");
    });
  }

  if (dockRandom) {
    dockRandom.addEventListener("click", playRandomSong);
  }
  if (dockHistory) {
    dockHistory.addEventListener("click", playPreviousSong);
  }

  function bindSeek(el) {
    if (!el) return;
    el.style.cursor = "pointer";
    el.addEventListener("click", function (e) {
      if (!(isFinite(audio.duration) && audio.duration > 0)) return;
      const rect = el.getBoundingClientRect();
      const ratio = Math.min(1, Math.max(0, (e.clientX - rect.left) / rect.width));
      audio.currentTime = audio.duration * ratio;
      paintPlayer();
    });
  }
  if (dockBar && dockBar.parentElement) bindSeek(dockBar.parentElement);
  if (songPlayer) bindSeek($(".track-progress", songPlayer));

  $$("[data-play]").forEach(function (el) {
    el.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();
      const holder = el.closest("[data-song]") || el.closest(".music-post, .song-card, .track");
      const heading = holder ? $("h3, .track-title", holder) : null;
      const title = el.dataset.song || (heading && heading.textContent.trim()) || "پخش نمونه";
      const artistNode = holder ? $(".post-bottom b, .card-foot b, .track-title small", holder) : null;
      const artist = el.dataset.artist || (artistNode && artistNode.textContent.trim()) || "آوا موزیک";
      const url = el.dataset.stream || (songPlayer && songPlayer.dataset.stream) || "";
      playItem(url, title, artist);
    });
  });

  if (bigBtn) {
    bigBtn.addEventListener("click", function () {
      if (!audio.paused) {
        audio.pause();
        return;
      }
      if (!audio.src && songPlayer && songPlayer.dataset.stream) {
        audio.src = songPlayer.dataset.stream;
      }
      if (!audio.src) {
        toast("فایل صوتی این آهنگ در دسترس نیست.");
        return;
      }
      const result = audio.play();
      if (result && result.catch) result.catch(function () {});
    });
  }

  /* waveform bars */
  $$("[data-wave]").forEach(function (wave, w) {
    const total = 46;
    for (let i = 0; i < total; i++) {
      const bar = document.createElement("i");
      const h = 22 + Math.abs(Math.sin((i + w) * 0.55)) * 60 + Math.abs(Math.cos(i * 0.23)) * 18;
      bar.style.height = Math.min(100, h) + "%";
      bar.style.animationDelay = (i % 12) * 0.07 + "s";
      wave.appendChild(bar);
    }
  });

  paintPlayer();

  /* ---------- filter chips ---------- */
  $$("[data-filter-group]").forEach(function (group) {
    const target = $(group.dataset.filterTarget || "#songGrid");
    const empty = group.dataset.empty ? $(group.dataset.empty) : null;
    $$("[data-filter]", group).forEach(function (chip) {
      chip.addEventListener("click", function () {
        $$("[data-filter]", group).forEach(function (c) { c.classList.remove("active"); c.setAttribute("aria-pressed", "false"); });
        chip.classList.add("active");
        chip.setAttribute("aria-pressed", "true");
        const value = chip.dataset.filter;
        // reset to first page on the server so the chosen category is actually listed
        const params = new URLSearchParams(window.location.search);
        params.set("page", "1");
        if (value === "all") { params.delete("category"); } else { params.set("category", value); }
        const sortSel = document.querySelector("[data-sort]");
        if (sortSel && sortSel.value) params.set("sort", sortSel.value.replace(/^\?sort=/, ""));
        window.location.href = window.location.pathname + "?" + params.toString();
      });
    });
  });

  /* ---------- deep links to archive filters (#special / #remix / #video / #popular) ---------- */
  function applyHashFilter() {
    const key = location.hash.replace("#", "");
    if (!key) return;
    if (key === "popular") {
      const allChip = $$("[data-filter]").filter(function (c) { return c.dataset.filter === "all"; })[0];
      if (allChip) allChip.click();
      const sel = $("[data-sort]");
      if (sel) {
        sel.value = "views";
        sel.dispatchEvent(new Event("change"));
      }
      return;
    }
    const map = { special: "all", remix: "remix", video: "all" };
    const target = map[key];
    if (target === "all") {
      const allChip = $$("[data-filter]").filter(function (c) { return c.dataset.filter === "all"; })[0];
      if (allChip) allChip.click();
      return;
    }
    if (!target) return;
    const chip = $$("[data-filter]").filter(function (c) { return c.dataset.filter === target; })[0];
    if (chip) chip.click();
  }
  applyHashFilter();
  window.addEventListener("hashchange", applyHashFilter);

  /* ---------- grid / list switch ---------- */
  $$("[data-view]").forEach(function (button) {
    button.addEventListener("click", function () {
      const toggle = button.closest(".view-toggle");
      const scope = $((toggle && toggle.dataset.viewScope) || button.dataset.viewScope || "[data-view-scope]");
      if (!scope) return;
      $$("[data-view]", button.parentElement).forEach(function (b) { b.classList.remove("active"); });
      button.classList.add("active");
      const list = $(".post-list", scope);
      const grid = $(".song-grid", scope);
      const isList = button.dataset.view === "list";
      if (grid) grid.hidden = isList;
      if (list) list.hidden = !isList;
      const active = $(".chip.active");
      if (active) active.click();
    });
  });

  /* ---------- sort ---------- */
  $$("[data-sort]").forEach(function (select) {
    select.addEventListener("change", function () {
      const target = $(select.dataset.sortTarget || "#songGrid");
      if (!target) return;
      const cards = $$("[data-tags]", target);
      const order = select.value;
      cards.sort(function (a, b) {
        if (order === "views") return (+b.dataset.views || 0) - (+a.dataset.views || 0);
        if (order === "title") return (a.dataset.title || "").localeCompare(b.dataset.title || "", "fa");
        return (b.dataset.date || "").localeCompare(a.dataset.date || "");
      });
      cards.forEach(function (c) { target.appendChild(c); });
    });
  });

  /* ---------- alphabet filter (artists) ---------- */
  $$("[data-alpha-group]").forEach(function (group) {
    const target = $(group.dataset.alphaTarget || "#artistGrid");
    $$("[data-letter]", group).forEach(function (btn) {
      btn.addEventListener("click", function () {
        $$("[data-letter]", group).forEach(function (b) { b.classList.remove("active"); });
        btn.classList.add("active");
        const letter = btn.dataset.letter;
        let visible = 0;
        if (target) {
          $$("[data-name]", target).forEach(function (card) {
            const match = letter === "all" || (card.dataset.name || "").charAt(0) === letter;
            card.hidden = !match;
            if (match) visible++;
          });
        }
        const empty = $("[data-alpha-empty]");
        if (empty) empty.classList.toggle("show", visible === 0);
      });
    });
  });

  /* ---------- tabs ---------- */
  $$("[data-tabs]").forEach(function (tabs) {
    const buttons = $$("[data-tab]", tabs);
    buttons.forEach(function (btn) {
      btn.addEventListener("click", function () {
        buttons.forEach(function (b) {
          b.classList.remove("active");
          b.setAttribute("aria-selected", "false");
        });
        btn.classList.add("active");
        btn.setAttribute("aria-selected", "true");
        $$("[data-panel]").forEach(function (panel) {
          panel.classList.toggle("active", panel.dataset.panel === btn.dataset.tab);
        });
      });
    });
  });

  /* ---------- follow / like ---------- */
  $$("[data-follow]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      const on = btn.classList.toggle("is-following");
      btn.textContent = on ? "✓ دنبال می‌کنید" : "+ دنبال کردن";
      btn.classList.toggle("btn-primary", on);
      btn.classList.toggle("btn-ghost", !on);
      const url = btn.dataset.followUrl;
      if (url && window.fetch) {
        fetch(url, {
          method: "POST",
          headers: { "X-CSRFToken": csrfToken, "X-Requested-With": "XMLHttpRequest" },
          credentials: "same-origin"
        })
          .then(function (r) { return r.json(); })
          .then(function (data) {
            if (data && typeof data.following === "boolean") {
              btn.classList.toggle("is-following", data.following);
              btn.classList.toggle("btn-primary", data.following);
              btn.classList.toggle("btn-ghost", !data.following);
              btn.textContent = data.following ? "✓ دنبال می‌کنید" : "+ دنبال کردن";
            }
          })
          .catch(function () {});
      }
      toast(on ? "به فهرست دنبال‌شده‌ها اضافه شد." : "از فهرست دنبال‌شده‌ها حذف شد.");
    });
  });
  $$("[data-like]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      const url = btn.dataset.likeUrl;
      if (url && window.fetch) {
        fetch(url, {
          method: "POST",
          headers: { "X-CSRFToken": csrfToken, "X-Requested-With": "XMLHttpRequest" },
          credentials: "same-origin"
        })
          .then(function (r) { return r.json(); })
          .then(function (data) {
            if (data && typeof data.count === "number") {
              btn.classList.toggle("liked", !!data.liked);
              btn.dataset.count = data.count;
              btn.textContent = (data.liked ? "♥ " : "♡ ") + (data.count_fa || faNum(data.count));
              toast(data.liked ? "پسندیدید." : "پسند حذف شد.");
            }
          })
          .catch(function () { toast("ارتباط با سرور برقرار نشد."); });
        return;
      }
      const on = btn.classList.toggle("liked");
      const count = +btn.dataset.count || 0;
      btn.dataset.count = on ? count + 1 : count;
      btn.textContent = (on ? "♥ " : "♡ ") + faNum(on ? count + 1 : count);
      toast(on ? "پسندیدید." : "پسند حذف شد.");
    });
  });

  /* ---------- copy / share ---------- */
  $$("[data-copy]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      const el = $(btn.dataset.copy);
      if (!el) return;
      const text = el.innerText;
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(function () { toast("در کلیپ‌بورد کپی شد."); }, function () { toast("کپی ممکن نشد."); });
      } else {
        toast("کپی ممکن نیست؛ متن را دستی انتخاب کنید.");
      }
    });
  });
  $$("[data-share]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      const network = btn.dataset.share;
      const url = window.location.href;
      if (network === "copy") {
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(url).then(function () { toast("لینک صفحه کپی شد."); });
        } else { toast("لینک صفحه را از نوار آدرس کپی کنید."); }
        return;
      }
      toast("اشتراک‌گذاری در " + (btn.getAttribute("aria-label") || "شبکه اجتماعی") + " (نسخه نمایشی)");
    });
  });

  /* ---------- demo downloads ---------- */
  $$("[data-demo-download]").forEach(function (el) {
    el.addEventListener("click", function (e) {
      e.preventDefault();
      toast("این یک فایل نمونه است؛ لینک دانلود را به فایل واقعی وصل کنید.");
    });
  });

  /* ---------- back to top ---------- */
  const toTop = $("#toTop");
  if (toTop) {
    window.addEventListener("scroll", function () {
      toTop.classList.toggle("show", window.scrollY > 480);
    }, { passive: true });
    toTop.addEventListener("click", function () {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }

  /* ---------- search page ---------- */
  const searchPage = document.body.dataset.page === "search";
  if (searchPage) {
    const params = new URLSearchParams(window.location.search);
    const q = (params.get("q") || "").trim();
    const pageInput = $("#searchPageInput");
    const heading = $("#searchHeading");
    const count = $("#resultCount");
    const grid = $("#resultGrid");
    const empty = $("#searchEmpty");
    if (pageInput) pageInput.value = q;
    if (heading) heading.textContent = q ? "نتایج جستجو برای «" + q + "»" : "همه انتشارها";
    function runSearch(term) {
      let visible = 0;
      if (grid) {
        $$("[data-tags]", grid).forEach(function (card) {
          const hay = card.innerText.toLowerCase();
          const match = !term || hay.indexOf(term.toLowerCase()) !== -1;
          card.hidden = !match;
          if (match) visible++;
        });
      }
      if (count) count.textContent = faNum(visible) + " نتیجه";
      if (empty) empty.classList.toggle("show", visible === 0);
    }
    runSearch(q);
    const pageForm = $("#searchPageForm");
    if (pageForm && pageInput) {
      pageForm.addEventListener("submit", function (e) {
        e.preventDefault();
        const term = pageInput.value.trim();
        const url = term ? "?q=" + encodeURIComponent(term) : "?";
        if (window.history && window.history.pushState) {
          window.history.pushState({}, "", "search.html" + url);
          if (heading) heading.textContent = term ? "نتایج جستجو برای «" + term + "»" : "همه انتشارها";
          runSearch(term);
        } else {
          window.location.search = url;
        }
      });
    }
    $$("[data-suggest]").forEach(function (link) {
      link.addEventListener("click", function (e) {
        e.preventDefault();
        if (pageInput) pageInput.value = link.dataset.suggest;
        if (pageForm && pageForm.requestSubmit) pageForm.requestSubmit();
        else if (pageForm) pageForm.dispatchEvent(new Event("submit", { cancelable: true }));
      });
    });
  }

  /* ---------- album “play all” ---------- */
  $$("[data-play-album]").forEach(function (btn) {
    btn.addEventListener("click", function (e) {
      e.preventDefault();
      openDock(btn.dataset.playAlbum || "آلبوم نمونه", btn.dataset.albumArtist || "آوا موزیک", 2400);
    });
  });
})();
