# آوا | AVA Music Archive

A complete RTL Persian music-download template (multi-page, static). Includes dark/light theme, a persistent mini-player dock, filtering/sorting, and responsive layouts down to small phones.

## Run

Open `index.html` directly in a browser, or serve the folder with VS Code Live Server (recommended, so `?q=` links work naturally).

## Pages

| File | Description |
| --- | --- |
| `index.html` | Homepage: featured release, latest songs feed, albums, charts, artists, sidebar |
| `archive.html` | Song archive: search, category filters, sort, grid/list toggle, sidebar |
| `song.html` | Single song: player, quality/download list, lyrics, specs, comments, related |
| `artists.html` | Artists directory with alphabet filter and follow buttons |
| `artist.html` | Artist profile: hero, stats, tabs (songs/albums/about), popular tracks |
| `albums.html` | Albums & playlists grid with filters |
| `album.html` | Album detail: hero, tracklist, related albums |
| `contact.html` | Contact form, track-submission form (local file picker), FAQ |
| `about.html` | Story, timeline, values, team |
| `search.html` | Search results page, reads `?q=` from the URL |
| `404.html` | Not-found page |

## Folder structure

```
.
├── index.html
├── archive.html
├── song.html
├── artists.html
├── artist.html
├── albums.html
├── album.html
├── contact.html
├── about.html
├── search.html
├── 404.html
├── css/
│   └── style.css
├── js/
│   └── main.js
└── img/
    ├── cover-1.svg … cover-10.svg     # palette-matched song/album artwork
    └── artist-1.svg … artist-12.svg   # artist avatars
```

## Interactions (`js/main.js`)

- Theme toggle with `localStorage` persistence (`ava-theme`), applied on every page.
- Mobile navigation drawer, sticky header shadow, back-to-top button.
- Header search: filters the homepage feed live; on every other page it opens `search.html?q=…`.
- Archive/search page: text search, category chips, sort select, grid/list view toggle.
- Song page: mini-player dock (play/pause, progress bar, volume), share/copy buttons, quality download rows.
- Artist page: tab switching. Album page: track rows. Contact page: demo form handlers, drag-and-drop file label, FAQ accordion.
- All behaviors are null-safe and shared by every page.

## Design

- Reference-inspired structure: music post feed, category sidebar, charts, albums/playlists, editorial feature.
- Palette: `#091540`, `#1B2CC1`, `#7692FF`, `#ABD2FA`.
- Themes: light (`:root`) and dark (`html[data-theme=dark]`) with matching accents, fields, and cards.
- Persian RTL layout; breakpoints at 1280 / 1024 / 900 / 680 / 480 / 390 px.
- All artwork is local SVG, so the template works offline. Google Fonts (`Vazirmatn`) is the only optional network dependency; the stack falls back to Tahoma.

## Notes / integration

- Names, covers, dates, counts and links are demo content — replace them with real data.
- Player controls are UI-only; wire up licensed audio URLs (or `<audio>` sources) for real playback.
- Forms are demo-only: replace the submit handlers in `js/main.js` with your backend endpoints.
- To use in Django: move CSS/JS to `static/css/` and `static/js/`, convert the repeated `.music-post` / `.song-card` / `.album-card` blocks into `{% for %}` loops, and keep the same class names.
