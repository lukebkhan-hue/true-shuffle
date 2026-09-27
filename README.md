# True Shuffle

A one-page web app that plays a YouTube playlist in a genuinely random order.
YouTube's own shuffle deals one random order and then loops it forever; this
page re-shuffles the whole playlist every time it reaches the end and never
plays the same song twice in a row.

Everything is in `index.html`. There is no build step and no server code.

## Using it

1. Open the page.
2. Paste a playlist link (anything containing `list=`), or just the playlist id.
3. Press **Shuffle & play**.

The playlist must be **public or unlisted**. Songs YouTube refuses to play
embedded (deleted, private, or blocked by the uploader) are skipped and shown
crossed out in the queue. Click any song in the queue to play it next.

Keyboard: `Space` play/pause, `→` next, `←` previous, `S` reshuffle. Keyboard
media keys work as well.

The player only hands over the first 200 songs of a playlist. For longer
playlists, open "Playlist longer than 200 songs?" and paste a free
[YouTube Data API key](https://developers.google.com/youtube/v3/getting-started).
The key is stored only in your browser.

## Hosting on GitHub Pages

The page needs a real `http(s)://` address; opening the file directly from disk
breaks the player's event messages. GitHub Pages is free:

1. Create an empty public repository on GitHub (for example `true-shuffle`).
2. Push this folder to its `main` branch. The workflow in
   `.github/workflows/pages.yml` deploys the page automatically.
3. If the first run fails with a Pages permission error, open the repository's
   **Settings → Pages** and set **Source** to **GitHub Actions**, then re-run it.

The page then lives at `https://<your-username>.github.io/<repository>/`.

## Local preview

```bash
python -m http.server 8775
```

Then open <http://localhost:8775/>.
