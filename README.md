mailStats
=========

There are a lot of tools/projects that provide some statistics about email but all of the web ones require that you give full access to your mailbox.

This is a series of tools that downloads a set of mail from a gmail inbox and then runs some basic statistics on the resulting email database. 
* Running `main.py` downloads your mailbox and then uses python multi-threading to run a series of map reduce queries to generate basic email stats. (and some fun ones)
* Running `generateSite.py` generates an email.js file which can be used in conjunction with graphView.html to see d3 views of the downloaded emails.
