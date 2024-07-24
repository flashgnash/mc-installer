# CLI for installing modded minecraft servers

## Installation

To install, run pip install git+https://github.com/flashgnash/mc-installer


## Usage:
To run, find the manifest.json from your modpack install zip (can be downloaded from a modpack's page on curseforge)
``mc-installer "path/to/manifest.json"``

This will download the correct version of forge along with all API accessible mods in the modlist into a a directory named the name of the modpack.
(some URLs will be spat out in console as 404 errors, these mods cannot be accessed via API as their creator has disabled - this will be handled more gracefully in future)



