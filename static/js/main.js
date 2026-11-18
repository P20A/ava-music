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
    if (themeBtn) themeBtn.innerHTML = dark ? "☼ <span>حالت روشن</span>" : "☾ <span>حالت تیره</span>";
    if (themeColor) themeColor.setAttribute("content", dark ? "#091540" : "#f2f5fc");
    if (themeBtn) themeBtn.setAttribute("aria-pressed", String(!dark));
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

  /* ---------- mini player ---------- */
  const dock = $("#audioDock");
  const dockTitle = $("#dockTitle");
  const dockArtist = $("#dockArtist");
  const dockPlay = $("#playPause");
  const dockBar = $("#dockBar") || (dock && $(".dock-progress i b", dock));
  const dockCur = $("#dockCur");
  const mediaAudio = $("[data-player-audio]");
  let duration = 209;
  let current = 48;
  let timer = null;
  let playing = false;

  function paintDock() {
    if (dockBar) dockBar.style.width = Math.min(100, (current / duration) * 100) + "%";
    if (dockCur) dockCur.textContent = faTime(current);
  }
  function openDock(title, artist, seconds) {
    if (!dock) return;
    if (dockTitle) dockTitle.textContent = title || "پخش نمونه";
    if (dockArtist) dockArtist.textContent = artist || "آوا موزیک";
    duration = seconds || 209;
    current = 0;
    if (mediaAudio) {
      dock.classList.add("is-open");
      paintDock();
      mediaAudio.play();
      return;
    }
    playing = false;
    setPlaying(true);
    dock.classList.add("is-open");
    paintDock();
    if (dock.scrollIntoView && window.innerWidth < 680) {
      /* keep the page still; the dock is fixed */
    }
  }
  function setPlaying(state) {
    playing = state;
    if (dockPlay) dockPlay.textContent = state ? "Ⅱ" : "▶";
    if (dockPlay) dockPlay.setAttribute("aria-label", state ? "توقف" : "پخش");
    clearInterval(timer);
    if (state && !mediaAudio) {
      timer = setInterval(function () {
        current += 1;
        if (current >= duration) { current = duration; setPlaying(false); }
        paintDock();
      }, 1000);
    }
  }
  if (mediaAudio) {
    mediaAudio.addEventListener("play", function () { setPlaying(true); });
    mediaAudio.addEventListener("pause", function () { setPlaying(false); });
    mediaAudio.addEventListener("timeupdate", function () {
      if (!isFinite(mediaAudio.duration) || !mediaAudio.duration) return;
      duration = mediaAudio.duration;
      current = mediaAudio.currentTime;
      paintDock();
      const bigBar = $("[data-player-bar]");
      if (bigBar) bigBar.style.width = Math.min(100, (current / duration) * 100) + "%";
      const bigTime = $("[data-player-time]");
      if (bigTime) bigTime.textContent = faTime(current);
    });
    mediaAudio.addEventListener("ended", function () { current = 0; setPlaying(false); paintDock(); });
  }
  if (dockPlay) {
    dockPlay.addEventListener("click", function () {
      if (!dock || !dock.classList.contains("is-open")) {
        openDock(dockTitle ? dockTitle.textContent : "پخش نمونه", dockArtist ? dockArtist.textContent : "آوا موزیک");
        return;
      }
      if (mediaAudio) {
        if (mediaAudio.paused) mediaAudio.play(); else mediaAudio.pause();
        return;
      }
      setPlaying(!playing);
    });
  }
  const closeDock = $("#closeDock");
  if (closeDock) {
    closeDock.addEventListener("click", function () {
      if (!dock) return;
      setPlaying(false);
      dock.classList.remove("is-open");
    });
  }
  const dockPrev = $("[data-dock-prev]");
  const dockNext = $("[data-dock-next]");
  if (dockPrev) dockPrev.addEventListener("click", function () { current = 0; paintDock(); });
  if (dockNext) dockNext.addEventListener("click", function () { current = 0; paintDock(); toast("صف پخش در نسخه نهایی فعال می‌شود."); });

  $$("[data-play]").forEach(function (el) {
    el.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();
      const holder = el.closest("[data-song]") || el.closest(".music-post, .song-card, .track");
      const title = el.dataset.song || (holder && $("h3, .track-title", holder) && $("h3, .track-title", holder).textContent.trim()) || "پخش نمونه";
      const artist = el.dataset.artist || (holder && ($(".post-bottom b, .card-foot b, .track-title small", holder) || {}).textContent) || "آوا موزیک";
      const secs = parseInt(el.dataset.duration || (holder && holder.dataset.duration) || "209", 10);
      openDock(title, artist, secs);
    });
  });
  if (dockPlay && !$$("[data-play]").length) {
    /* still allow the initial dock button to start the demo */
  }
  if (dockBar) {
    const progress = dockBar.parentElement;
    if (progress) {
      progress.style.cursor = "pointer";
      progress.addEventListener("click", function (e) {
        const rect = progress.getBoundingClientRect();
        const ratio = Math.min(1, Math.max(0, (e.clientX - rect.left) / rect.width));
        current = Math.round(duration * ratio);
        if (mediaAudio && isFinite(mediaAudio.duration) && mediaAudio.duration) {
          mediaAudio.currentTime = mediaAudio.duration * ratio;
        }
        paintDock();
      });
    }
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

  /* big player on song page */
  const songPlayer = $("[data-song-player]");
  if (songPlayer) {
    const btn = $("[data-player-toggle]", songPlayer);
    const bar = $("[data-player-bar]", songPlayer);
    const time = $("[data-player-time]", songPlayer);
    let sCurrent = 0, sDuration = 209, sTimer = null, sPlaying = false;
    function paintPlayer() {
      if (bar) bar.style.width = Math.min(100, (sCurrent / sDuration) * 100) + "%";
      if (time) time.textContent = faTime(sCurrent);
    }
    if (btn) {
      btn.addEventListener("click", function () {
        if (mediaAudio) {
          if (mediaAudio.paused) mediaAudio.play(); else mediaAudio.pause();
          return;
        }
        sPlaying = !sPlaying;
        songPlayer.classList.toggle("playing", sPlaying);
        btn.textContent = sPlaying ? "Ⅱ" : "▶";
        btn.setAttribute("aria-label", sPlaying ? "توقف" : "پخش");
        clearInterval(sTimer);
        if (sPlaying) {
          sTimer = setInterval(function () {
            sCurrent += 1;
            if (sCurrent >= sDuration) { sCurrent = 0; sPlaying = false; clearInterval(sTimer); songPlayer.classList.remove("playing"); btn.textContent = "▶"; }
            paintPlayer();
          }, 1000);
        }
        openDockFromPlayer();
      });
    }
    function openDockFromPlayer() {
      if (!dock) return;
      if (dockTitle) dockTitle.textContent = songPlayer.dataset.title || (dockTitle.textContent);
      if (dockArtist) dockArtist.textContent = songPlayer.dataset.artist || dockArtist.textContent;
      dock.classList.add("is-open");
    }
    if (mediaAudio) {
      mediaAudio.addEventListener("play", function () {
        songPlayer.classList.add("playing");
        if (btn) { btn.textContent = "Ⅱ"; btn.setAttribute("aria-label", "توقف"); }
        openDockFromPlayer();
      });
      mediaAudio.addEventListener("pause", function () {
        songPlayer.classList.remove("playing");
        if (btn) { btn.textContent = "▶"; btn.setAttribute("aria-label", "پخش"); }
      });
      mediaAudio.addEventListener("loadedmetadata", function () {
        if (isFinite(mediaAudio.duration) && mediaAudio.duration) {
          sDuration = mediaAudio.duration;
          paintPlayer();
        }
      });
      mediaAudio.addEventListener("ended", function () {
        sCurrent = 0;
        songPlayer.classList.remove("playing");
        if (btn) { btn.textContent = "▶"; btn.setAttribute("aria-label", "پخش"); }
        paintPlayer();
      });
    }
    const bigProgress = $(".track-progress", songPlayer);
    if (bigProgress) {
      bigProgress.addEventListener("click", function (e) {
        const rect = bigProgress.getBoundingClientRect();
        const ratio = Math.min(1, Math.max(0, (e.clientX - rect.left) / rect.width));
        if (mediaAudio && isFinite(mediaAudio.duration) && mediaAudio.duration) {
          mediaAudio.currentTime = mediaAudio.duration * ratio;
          sCurrent = mediaAudio.currentTime;
        } else {
          sCurrent = Math.round(sDuration * ratio);
        }
        paintPlayer();
      });
    }
    const times = $("[data-duration]", songPlayer);
    if (times) sDuration = parseInt(times.dataset.duration, 10) || 209;
    if (mediaAudio && isFinite(mediaAudio.duration) && mediaAudio.duration) sDuration = mediaAudio.duration;
    paintPlayer();
  }

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
        let visible = 0;
        if (target) {
          $$("[data-tags]", target).forEach(function (card) {
            const match = value === "all" || (card.dataset.tags || "").indexOf(value) !== -1;
            card.hidden = !match;
            if (match) visible++;
          });
        }
        if (empty) empty.classList.toggle("show", visible === 0);
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
    const map = { special: "ویژه", remix: "ریمیکس", video: "موزیک ویدیو" };
    const label = map[key];
    if (!label) return;
    const chip = $$("[data-filter]").filter(function (c) { return c.dataset.filter === label; })[0];
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
