# Python Scripts

Simple and small Python scripts that I find useful.

## Contents

- *agents.py*: Downloads a list of entries from "botsvsbrowsers.org" and makes a list
  useful for importing into the "User Agent Switcher" extension.
- *blocklists.py*: Downloads hostfiles contained in a URL list and parses them. Has the
  ability to remove entries based on Regex matches.
- *certserver.py*: HTTP Server listener that can be used to monitor certificate expiry
  dates in an on-prem Windows CA environment and send emails.
- *feeds.py*: Downloads Mastdon posts based on a users list and outputs the last ~20 (configurable)
  into a JSON formatted file for later parsing.
- *host_convert.py*: Takes a 'name: url' list file that contains URLs for domain host files
  and converts them into hostfiles useful for PiHole or PFBlock.
- *linesort.py*: Breaks config files into lines and reformats them with padding.
- *links.py*: Downloads Zoho Bookmarks and converts them into an RSS feed. Useful with FF
  LiveBookmarks extension.
- *mini.py*: Minifies files into printf statements for easy transport and scripting.
- *move.py*: Re-sorts files in a directory based on a name prefix and number scheme.
- *ntstatus.py*: Looks up a NTSTATUS code and will attempt to find the English translation.
- *samedir.py*: Attempts to find files that match the same hash in a directory and
  offers the ability to delete them
- *sitemap.py*: Used to spider a site and generate an XML-formatted sitemap.xml file.
