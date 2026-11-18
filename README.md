# آوا | AVA Music Archive

A fresh RTL Persian music archive homepage, designed as a music-download portal rather than a portfolio/landing page.

## Run
Open `index.html` directly or use VS Code Live Server.

## Files
- `index.html`: homepage structure and sample music posts
- `css/style.css`: palette, layout, dark/light themes, responsive breakpoints
- `js/main.js`: theme persistence, mobile navigation, search, demo mini-player

## Design
- Reference-inspired content structure: music post feed with cover art, metadata, artist/category sidebar, trending list, albums/playlists and editorial feature.
- Palette: `#091540`, `#1B2CC1`, `#7692FF`, `#ABD2FA`
- Persian RTL layout and responsive mobile layout.
- Replace demo titles, covers, dates, artist names and links with your own data.
- Player controls are UI-only; connect licensed audio URLs for real playback.
- External image URLs and Google Fonts require internet access.

## Django
Move CSS/JS into `static/css/` and `static/js/`, then replace sample `.music-post` blocks with a Django `{% for song in songs %}` loop. Store cover, title, artist, publish date, category and download links in your models.
