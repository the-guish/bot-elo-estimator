#!/bin/sh
# Runs Eubos on the Java runtime built for it. The heap holds Eubos's hash table, which the Lichess
# bot sets to 512 MB, and the old table until the collector frees it after `ucinewgame`.
exec /opt/engines/eubos/java/bin/java -Xmx1g -jar /opt/engines/eubos/Eubos.jar "$@"
