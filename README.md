# bzin22.github.io

Bryan Zin's personal site, published at https://bryanzin.com. GitHub Pages
builds it with Jekyll on every push to `master`.

## Where the content lives

- `index.html` is the home page at `/`: the workbench, a desk of draggable
  objects (one self-contained file, no theme layout). It opens in the aligned
  layout. Its content copies the plain pages, so edit both when the text changes.
  The sun button in its menu bar goes to the plain site.
- `_pages/` holds the plain site, one Markdown file per page: `about.md` (Home,
  served at `/about/`), `research.md`, `projects.md`, `experience.md` (CV, served
  at `/experience/`), `resume.md`, plus `sitemap.md` and `404.md`. `/contact/`
  redirects to Home and `/cv/` redirects to Resume. The sun button in the plain
  header goes back to the workbench.
- `_data/navigation.yml` sets the header menu: Home, Research, Projects, CV,
  Resume.
- `_config.yml` holds site-wide settings and the plain sidebar profile (name,
  bio, optional education line, photo, email, GitHub, LinkedIn). The workbench
  badge in `index.html` has its own text.
- `files/` holds downloads such as `bryan-zin-cv.pdf`. They are served at
  https://bryanzin.com/files/bryan-zin-cv.pdf.
- `images/` holds the profile photo (`bryan-zin.png`), the resume preview
  (`bryan-zin-resume.png`), the Research figure (`scrisk-result.png`), the favicons, and the
  template's theme screenshots under `images/themes/`.

The theme itself (`_includes/`, `_layouts/`, `_sass/`, `assets/`) comes from the
[Academic Pages template](https://github.com/academicpages/academicpages.github.io).

## Running locally

Preview changes locally before pushing them to GitHub.

### Using Ruby and Bundler directly

On Apple Silicon macOS, this site was tested with Ruby 3.3 and Bundler 2.5.23:

```bash
brew install ruby@3.3
export PATH="$(brew --prefix ruby@3.3)/bin:$PATH"
gem install bundler -v 2.5.23
bundle _2.5.23_ config set --local path vendor/bundle
bundle _2.5.23_ install
bundle _2.5.23_ exec jekyll serve -l -H localhost
```

Open `http://localhost:4000`. The `export` applies to the current terminal; add it to
`~/.zshrc` if you want Ruby 3.3 in future zsh sessions. Jekyll rebuilds after edits
to Markdown and HTML files; restart it after changing `_config.yml`.

On Linux or [WSL](https://learn.microsoft.com/en-us/windows/wsl/about), install
Ruby 3.x, Bundler, and build tools for your distribution, then run `bundle
install` and `bundle exec jekyll serve -l -H localhost`.

## Using Docker

Working from a different OS, or just want to avoid installing dependencies? You can use the provided `Dockerfile` to build a container that will run the site for you if you have [Docker](https://www.docker.com/) installed.

You can build and execute the container by running the following command in the repository:

```bash
chmod -R 777 .
docker compose up
```

You should now be able to access the website from `localhost:4000`.

### Using the DevContainer in VS Code

If you are using [Visual Studio Code](https://code.visualstudio.com/) you can use the [Dev Container](https://code.visualstudio.com/docs/devcontainers/containers) that comes with this Repository. Normally VS Code detects that a development container configuration is available and asks you if you want to use the container. If this doesn't happen you can manually start the container by **F1->DevContainer: Reopen in Container**. This restarts your VS Code in the container and automatically hosts your academic page locally on http://localhost:4000. All changes will be updated live to that page after a few seconds.

## Checking the site locally

`scripts/test_site.py` checks the built site in `_site/`. It asserts the
workbench and the five plain pages render their expected content, the nav is Home, Research, Projects, CV,
Resume in that order, each page title is right, `/contact/` and `/cv/` are
redirects, the Research figure, Home links, and resume download link are present,
removed copy stays removed, every internal link and asset resolves to a built
file, and no template placeholder text is left behind.

`scripts/test_workbench.py` opens the built workbench in headless Chrome and
checks the default aligned desk, the one-way Tidy desk button, putting windows
away, centered opening, corner resize, CV illustrations, and the menu underline.

```bash
bundle exec jekyll build
python3 scripts/test_site.py
python3 scripts/test_workbench.py
```

It prints one `FAIL:` line per problem and exits non-zero. Python standard
library only, no test framework.

## Provenance

This site is built from the [Academic Pages
template](https://github.com/academicpages/academicpages.github.io), which was
forked (then detached) by [Stuart Geiger](https://github.com/staeiou) from the
[Minimal Mistakes Jekyll Theme](https://mmistakes.github.io/minimal-mistakes/),
© 2016 Michael Rose, MIT licensed (see LICENSE). Bug reports about the template
itself belong [upstream](https://github.com/academicpages/academicpages.github.io/issues/new/choose),
not here.
