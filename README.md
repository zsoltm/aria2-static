Aria2 Static / multiArch Release Scripts 
========================================

The goal of this repo is to provide static builds of (`aria2c`)[http://aria2.sourceforge.net/] the "ultra fast" command
line downloader primarily for use within [docker](http://www.docker.io/).

Check out the [releases](https://github.com/zsoltm/aria2-static/releases) section for downloadable tarballs; or the
original [aria2 github page]

## Prerequisites

Python 2.7 must be installed on the system; `~/netrc` should have entries for hosts `github.com`, `api.github.com`
`uploads.github.com` with a valid login token like in the example below:

    machine github.com
      login 2fd4e1c67a2d28fced849ee1bb76e7391b93eb12
    
    machine api.github.com
      login de9f2c7fd25e1b3afad3e85a0bd17d9b100db4b3
    
    machine uploads.github.com
      login da39a3ee5e6b4b0d3255bfef95601890afd80709

For cross-platform build the linux kernel should support `BINFMT_MISC`.
