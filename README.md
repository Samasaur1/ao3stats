# ao3stats

Scrape your history from AO3, and then get some statistics from that data.

This repository is packaged with the [Nix package manager](https://nix.dev/), so if you have it installed, you can simply run

```
nix run github:Samasaur1/ao3stats#scrape
nix run github:Samasaur1/ao3stats#stats
```

For other installation instructions, see below.

## General Overview

### Requirements

ao3stats requires Python 3.10 or later, Swift 5.5 or later, and an internet connection.

### Structure

ao3stats is split into two component projects: a Python project that scrapes your history from AO3, and a Swift project that takes the output data and outputs a summary of statistics.

## Setup

1. Clone or download the repository: `git clone https://github.com/Samasaur1/ao3stats` works, or you can click "Code" and then "Download as ZIP" from the GitHub page
2. Open a terminal in the cloned/downloaded folder. On macOS, Terminal.app comes preinstalled; on Windows, I believe you'd use PowerShell or the command prompt; and on Linux, I assume you know what you're doing.
3. Run the following (instructions are for macOS/Linux; Windows instructions will be slightly different):

    ```
    python3 -m venv .
    source bin/activate
    python3 -m pip install tqdm requests beautifulsoup4
    ```

4. (Optional, for calculating stats).

    Run the following instructions (again, instructions are for macOS/Linux):

    ```
    cd display
    swift build -c release
    cd ..
    ln -s display/.build/release/display stats
    ```

## Running the program(s)

Open a terminal in the cloned/downloaded folder (if you are running the program immediately after setting it up, you can use the same terminal).

When you ran `source bin/activate`, the prompt should have changed to say `(ao3stats)` before whatever it was. If your current prompt looks like that, you are "in the virtual environment." If it doesn't look that way, you are not in the virtual environment (if you are running the program immediately after setting it up, you should be in the virtual environment).

If you aren't in the virtual environment, run `source bin/activate` in the terminal, and you now should be.

Now you can do the following:

1. Run the following command: `python3 main.py` and put in your username and password when asked
2. Wait for the program to finish (it should tell you how many deleted works were in your history)
3. There is now a file called `works.json` in the folder. This is your AO3 data, but not yet a summary
4. Run `./stats`. It should output a summary of your AO3 history

### Options to `./stats`

By default, running `./stats` with no arguments produces a summary on a file named `works.json` in the current folder. If you want, you can generate statistics for an old data dump by putting the name of that file as the first argument (e.g., `./stats old-works.json`).

You can also get specific stats on an author and/or a fandom. For example: `./stats --fandom "GitHub"` or `./stats --author "Octocat"`.

## Using `jq` to dump the works database

If you can't or don't want to build the program that calculates stats, you can inspect the `works.json` file manually. [`jq`](https://jqlang.github.io/jq/) is a great tool for working with JSON, and you can try examples such as these:

```
jp '.' works.json
jq '. | map(select(.authors[0] == "Samasaur1"))' works.json
jq '. | map(select(.changes_since_last_view != "Latest version."))' works.json
```
