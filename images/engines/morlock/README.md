# morlock

The historical engines of `herohde/morlock`, tag `v0.91.3`, in the extra image.

| Command | Engine |
|---|---|
| `sargon-1ply` to `sargon-4ply` | SARGON (1978) |
| `turochamp-1ply`, `turochamp-2ply` | TUROCHAMP (1948) |
| `bernstein-2ply`, `bernstein-4ply` | Bernstein's IBM 704 program (1957) |

Each command bears the name of the Lichess bot it reproduces, and searches to that bot's depth.
The other settings are morlock's defaults. SARGON and TUROCHAMP add noise of 10 millipawns to their
evaluations, which breaks ties at random. SARGON and Bernstein play their first move from their own
books.

The Dockerfile pins morlock by commit and Go by its sha256, and builds with the flags of morlock's
release. The binaries are static: they need no runtime package.

`engines/morlock` checks the commands against the bots' games.
