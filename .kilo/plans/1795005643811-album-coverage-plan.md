# Plan: Complete album coverage for imported songs

## Context

- Songs imported from `F:\Developing\agents\open code workspace\to add` (84 total).
- Albums currently: `Isa` (17), `Recto Verso` (1), `Zaz` (1). 65 songs unlinked.
- Imagine Dragons discography provided by user (shared ChatGPT link).

## Goal

Map every Imagine Dragons track to its studio album per the provided discography, create albums, link songs via `AlbumTrack`. Keep non-album singles as singles.

## Imagine Dragons album mapping (from provided discography)

- **Night Visions (2012)**: Radioactive, Tiptoe, It's Time, Demons, On Top of the World, Bleeding Out, Cha-Ching (Till We Grow Older)
- **Smoke + Mirrors (2015)**: Shots (Remix), Gold, I'm So Sorry, I Bet My Life, Friction, Dream, Second Chances, Release, Warriors, Battle Cry, Who We Are
- **Evolve (2017)**: I Don't Know Why, Whatever It Takes, Believer, Walking the Wire, Rise Up, I'll Make It Up to You, Yesterday, Mouth of the River, Thunder, Start Over, Dancing in the Dark, Not Today
- **Origins (2018)**: Natural, Boomerang, Machine, Cool Out, Bad Liar, West Coast, Zero, Bullet in a Gun, Only, Stuck, Love, Birds, Burn Out, Real Life, Born to Be Yours
- **Mercury – Act 1 (2021)**: none of the imported tracks appear in the listed 12 tracks.

Tracks not in any listed album (singles/other): Monster, Roots, Next To Me, Only? (Origins has Only), etc. Treat unlisted as singles.

## ZAZ/Dream
- `Recto Verso`, `Zaz` (debut), `Isa` already created.
- Dream tracks: singles (no album).

## Implementation steps

1. Create Albums: Night Visions, Smoke + Mirrors, Evolve, Origins (slugs: night-visions, smoke-and-mirrors, evolve, origins). Set release years.
2. For each album, find matching Song by title (case-insensitive, strip joyamusic) and create AlbumTrack with track_number from discography.
3. Extract cover from first track's APIC.
4. Idempotent: get_or_create on album slug and (album, song).

## Validation

- Album count = 7 (3 existing + 4 new).
- Imagine Dragons songs linked count matches discography (~43).
- `/albums/` and detail pages 200.
- `manage.py check` clean.
