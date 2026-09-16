# bzin22.github.io

Bryan Zin's personal site, published at https://bzin22.github.io. GitHub Pages
builds it with Jekyll on every push to `master`.

## Where the content lives

- `_pages/` holds one Markdown file per page: `about.md` (Home), `research.md`,
  `projects.md`, `experience.md`, `cv.md`, `contact.md`, plus `sitemap.md` and
  `404.md`.
- `_data/navigation.yml` sets the header menu: Home, Research, Projects,
  Experience, CV, Contact.
- `_config.yml` holds site-wide settings and the sidebar profile (name, bio,
  photo, email, GitHub, LinkedIn).
- `files/` holds downloads such as `bryan-zin-cv.pdf`. They are served at
  https://bzin22.github.io/files/bryan-zin-cv.pdf.
- `images/` holds the profile photo (`bryan-zin.png`), the favicons, and the
  template's theme screenshots under `images/themes/`.

The theme itself (`_includes/`, `_layouts/`, `_sass/`, `assets/`) comes from the
[Academic Pages template](https://github.com/academicpages/academicpages.github.io).

## Running locally

Preview changes locally before pushing them to GitHub.

### Using ruby and bundler directly
1. Make sure you have ruby-dev, bundler, and nodejs installed

    On most Linux distributions and [Windows Subsystem Linux](https://learn.microsoft.com/en-us/windows/wsl/about) the command is:
    ```bash
    sudo apt install ruby-dev ruby-bundler nodejs
    ```
    If you see error `Unable to locate package ruby-bundler`, `Unable to locate package nodejs `, run the following:
    ```bash
    sudo apt update && sudo apt upgrade -y
    ```
    then try running `sudo apt install ruby-dev ruby-bundler nodejs` again.

    On MacOS the commands are:
    ```bash
    brew install ruby
    brew install node
    gem install bundler
    ```
1. Run `bundle install` to install ruby dependencies. If you get errors, delete Gemfile.lock and try again.

    If you see file permission error like `Fetching bundler-2.6.3.gem ERROR:  While executing gem (Gem::FilePermissionError) You don't have write permissions for the /var/lib/gems/3.2.0 directory.` or `Bundler::PermissionError: There was an error while trying to write to /usr/local/bin.`
    Install Gems Locally (Recommended):
    ```bash
    bundle config set --local path 'vendor/bundle'
    ```
    then try run `bundle install` again. If succeeded, you should see a folder called `vendor` and `.bundle`.

1. Run `jekyll serve -l -H localhost` to generate the HTML and serve it from `localhost:4000` the local server will automatically rebuild and refresh the pages on change to Markdown (*.md) and HTML files, while changes to the core template and configuration (i.e., `_config.yml`) will require stopping and restarting Jekyll.
    You may also try `bundle exec jekyll serve -l -H localhost` to ensure jekyll to use specific dependencies on your own local machine.

If you are running on Linux it may be necessary to install some additional dependencies prior to being able to run locally: `sudo apt install build-essential gcc make`

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

`scripts/test_site.py` checks the built site in `_site/`. It asserts the six
pages render their expected content, the nav is Home, Research, Projects,
Experience, CV, Contact in that order, each page title is right, every internal
link and asset resolves to a built file, and no template placeholder text is
left behind.

```bash
bundle exec jekyll build
python3 scripts/test_site.py
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
