// A UCI front end for GarboChess-JS. garbochess.js is a browser engine: a web worker that takes
// FENs, moves and "search <ms>" messages. This loads it, unchanged, into a context of its own and
// calls its functions: Search(callback, maxPly, plyCallback) searches until a depth or until
// g_timeout milliseconds have passed, so `go depth` and `go movetime` map onto it directly.
//
//   go depth N      Search to depth N, without a time limit. Repeatable.
//   go nodes N      The time limit, counted in nodes instead of milliseconds: the engine reads its
//                   clock through Date, which here returns its node count. Repeatable.
//   go movetime N   Search for N milliseconds, as the worker's "search N" does.
//   go wtime ...    A share of the clock: a thirtieth of it plus most of the increment.
//   go              One second, the browser page's g_timeout.
//
// Every `go` starts from a fresh engine, as the worker's "position" message does: an empty hash
// table, killers and history. The moves of `position` are played from its start, so the engine
// sees repetitions. Its moves are from-to squares, so it castles as e1g1.

"use strict";

const fs = require("fs");
const path = require("path");
const readline = require("readline");
const vm = require("vm");

const STARTPOS = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";
const NO_LIMIT = 1e15;

let clock = () => Date.now();
class EngineDate {
    getTime() {
        return clock();
    }
}

// garbochess.js runs as the body of a function, as a CommonJS module does, with the worker's
// globals as its arguments; the object it returns reaches its functions and variables. (A vm
// context of its own would make every access to its globals many times slower.)
const exported = [
    "ResetGame", "InitializeFromFen", "GenerateValidMoves", "GetMoveFromString", "MakeMove",
    "UnmakeMove", "FormatMove", "Search", "minEval", "maxEval", "minMateBuffer", "maxMateBuffer",
];
const variables = ["g_moveCount", "g_toMove", "g_timeout", "g_nodeCount", "g_qNodeCount", "g_hashTable",
    "g_hashMask", "g_hashKeyLow", "g_hashKeyHigh"];
const file = path.join(__dirname, "garbochess.js");
const accessors = [
    ...exported.map((name) => `${name}: ${name},`),
    ...variables.map((name) => `get ${name}() { return ${name}; }, set ${name}(v) { ${name} = v; },`),
];
const engine = vm.compileFunction(
    fs.readFileSync(file, "utf8") + "\nreturn {\n" + accessors.join("\n") + "\n};\n",
    ["self", "postMessage", "alert", "Date"],
    { filename: file },
)({}, () => {}, (message) => {
    throw new Error(message);
}, EngineDate);

let fen = STARTPOS;
let moves = [];

function send(line) {
    process.stdout.write(line + "\n");
}

function setUp() {
    engine.ResetGame();
    engine.g_moveCount = 0;
    const error = engine.InitializeFromFen(fen);
    for (const move of moves) {
        if (engine.GenerateValidMoves().length === 0) break;
        engine.MakeMove(engine.GetMoveFromString(move));
    }
    return error;
}

function score(value) {
    if (value >= engine.maxMateBuffer) return `mate ${Math.ceil((engine.maxEval - value) / 2)}`;
    if (value <= engine.minMateBuffer) return `mate -${Math.ceil((value - engine.minEval) / 2)}`;
    return `cp ${Math.round(value / 8)}`; // a pawn is 800
}

// The principal variation, from the hash table, as PVFromHash finds it.
function pv(move, plies) {
    const line = [];
    const made = [];
    while (move && line.length < plies) {
        const legal = engine.GenerateValidMoves();
        if (!legal.includes(move)) break;
        line.push(engine.FormatMove(move));
        engine.MakeMove(move);
        made.push(move);
        const node = engine.g_hashTable[engine.g_hashKeyLow & engine.g_hashMask];
        move = node != null && node.lock == engine.g_hashKeyHigh ? node.bestMove : 0;
    }
    while (made.length) engine.UnmakeMove(made.pop());
    return line.join(" ");
}

function go(args) {
    const arg = (name) => {
        const i = args.indexOf(name);
        return i >= 0 && i + 1 < args.length ? Number(args[i + 1]) : undefined;
    };
    setUp();
    const legal = engine.GenerateValidMoves();
    if (legal.length === 0) {
        send("bestmove 0000");
        return;
    }

    let depth = arg("depth") ?? 99;
    let limit = NO_LIMIT;
    clock = () => Date.now();
    const white = engine.g_toMove !== 0;
    const time = arg(white ? "wtime" : "btime");
    const increment = arg(white ? "winc" : "binc") ?? 0;
    if (arg("nodes") !== undefined) {
        clock = () => engine.g_nodeCount + engine.g_qNodeCount;
        limit = arg("nodes");
    } else if (arg("movetime") !== undefined) {
        limit = arg("movetime");
    } else if (time !== undefined) {
        limit = Math.max(10, Math.min(time / 30 + increment * 0.75, time - 100));
    } else if (arg("depth") === undefined) {
        limit = 1000;
    }
    engine.g_timeout = limit;

    const start = Date.now();
    let best = 0;
    engine.Search(
        (move) => {
            best = move;
        },
        Math.max(1, Math.min(depth, 99)),
        (move, value, _, ply) => {
            const ms = Date.now() - start;
            const nodes = engine.g_nodeCount + engine.g_qNodeCount;
            const nps = ms > 0 ? Math.round((nodes * 1000) / ms) : 0;
            send(`info depth ${ply} score ${score(value)} nodes ${nodes} nps ${nps} time ${ms} pv ${pv(move, ply)}`);
        },
    );
    clock = () => Date.now();
    // A search cut off in its first depth has no move: take the first legal one.
    if (!best || !legal.includes(best)) best = legal[legal.length - 1];
    send(`bestmove ${engine.FormatMove(best)}`);
}

function position(args) {
    const at = args.indexOf("moves");
    const head = at >= 0 ? args.slice(0, at) : args;
    moves = at >= 0 ? args.slice(at + 1) : [];
    if (head[0] === "startpos") fen = STARTPOS;
    else if (head[0] === "fen") fen = head.slice(1).join(" ");
}

const input = readline.createInterface({ input: process.stdin, terminal: false });
input.on("line", (line) => {
    const [command, ...args] = line.trim().split(/\s+/);
    try {
        switch (command) {
            case "uci":
                send("id name GarboChess-JS 6.0");
                send("id author Gary Linscott");
                send("uciok");
                break;
            case "isready":
                send("readyok");
                break;
            case "position":
                position(args);
                break;
            case "go":
                go(args);
                break;
            case "quit":
                process.exit(0);
        }
    } catch (error) {
        send(`info string error: ${error.message}`);
        if (command === "go") send("bestmove 0000");
    }
});
input.on("close", () => process.exit(0));
