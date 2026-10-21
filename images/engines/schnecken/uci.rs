// A UCI loop for schnecken_bot's engine, for bot-elo-estimator. The Dockerfile puts it in place of
// the repository's own src/chess/engine/uci.rs, so it builds as the crate's schnecken_engine
// binary, over the chess library and nothing else.
//
// The repository's loop ignores the arguments of `go`: it searches to depth 20 with no time limit.
// This one plays a move the way the Lichess bot does (src/bot/games/game.rs and engine.rs at the
// pinned commit), with the library's own Engine:
//
// - `go wtime/btime [winc/binc]` gives the search the bot's time: 200 ms under 10 seconds on the
//   clock, else a 90th of the clock plus 10/9 of the increment (capped at 60 s). `go movetime`
//   sets the time directly, and `go depth` the deepest iteration; without it, depth 20, the
//   engine's default and the bot's in rated games. `go infinite` searches until `stop`.
// - The move is drawn at random among the lines within 0.015 pawn of the best one, as the bot
//   draws it; book positions give up to 3 book moves, all scored 0. `setoption name Random value
//   false` plays the best line instead.
// - Within a game the engine keeps its cache from move to move, as the bot does: each `position`
//   that extends the previous one applies only the new moves. `ucinewgame`, or a position from
//   another game, clears it. Asking again for the same position starts a new search, from depth 1,
//   on the cache the earlier searches left. `setoption name KeepCache value false` clears the
//   cache before every search instead, so that each search is independent of the ones before.
// - `Hash` is the size of each of the engine's two cache tables in MB, 1024 by default as in the
//   bot's configuration. `play_style` is the engine's option, Normal by default as in the bot.
//
// Moves come out in lower case (the library writes white promotions as e7e8Q), and castling as
// the king's move, e1g1.

use chess::engine::Engine;
use chess::engine::config::play_style::PlayStyle;
use chess::model::game_state::{GameState, START_POSITION_FEN};
use chess::model::piece::Color;
use rand::Rng;
use std::io::BufRead;
use std::thread::JoinHandle;
use std::time::Duration;

/// The bot's cache size, EngineConfig::default_cache_table_size, in MB.
const DEFAULT_HASH_MB: usize = 1024;
/// EngineOptions' default depth, which the bot keeps in rated games.
const DEFAULT_MAX_DEPTH: usize = 20;

struct Uci {
  engine:      Engine,
  random:      bool,
  keep_cache:  bool,
  /// The position the engine holds: its start and its moves, and the state before its last move.
  fen:         String,
  moves:       Vec<String>,
  before_last: Option<GameState>,
  search:      Option<JoinHandle<()>>,
}

impl Uci {
  fn new() -> Self {
    let mut engine = Engine::new(false);
    engine.options.uci = false;
    engine.resize_cache_tables(DEFAULT_HASH_MB);
    Uci { engine,
          random: true,
          keep_cache: true,
          fen: String::new(),
          moves: Vec::new(),
          before_last: None,
          search: None }
  }

  /// Stops the search, if one runs, and waits for its bestmove.
  fn halt(&mut self) {
    if let Some(search) = self.search.take() {
      while !search.is_finished() {
        self.engine.stop();
        std::thread::sleep(Duration::from_millis(5));
      }
      let _ = search.join();
    }
  }

  fn forget_game(&mut self) {
    self.fen.clear();
    self.moves.clear();
    self.before_last = None;
  }

  fn apply(&mut self, mv: &str) {
    self.before_last = Some(self.engine.position.clone());
    self.engine.apply_move(mv);
  }

  fn position(&mut self, words: &[&str]) {
    let (fen, rest) = match words.get(1) {
      Some(&"startpos") => (START_POSITION_FEN.to_string(), &words[2..]),
      Some(&"fen") => {
        let end = words.iter().position(|w| *w == "moves").unwrap_or(words.len());
        (words[2..end].join(" "), &words[end..])
      },
      _ => return,
    };
    let moves: Vec<String> = match rest.first() {
      Some(&"moves") => rest[1..].iter().map(|m| m.to_string()).collect(),
      _ => Vec::new(),
    };

    let same_game = self.keep_cache
                    && fen == self.fen
                    && !moves.is_empty()
                    && moves.len() >= self.moves.len()
                    && moves[..self.moves.len()] == self.moves[..];
    if same_game && moves.len() == self.moves.len() {
      // The same position again: play its last move once more, from the state before it, so that
      // the search starts over at depth 1 with the cache kept.
      if let Some(before) = self.before_last.clone() {
        self.engine.position = before;
        self.engine.apply_move(&moves[moves.len() - 1]);
      }
    } else if same_game {
      for mv in &moves[self.moves.len()..] {
        self.apply(mv);
      }
    } else {
      self.engine.set_position(&fen);
      self.before_last = None;
      for mv in &moves {
        self.apply(mv);
      }
    }
    self.fen = fen;
    self.moves = moves;
  }

  fn go(&mut self, words: &[&str]) {
    let value = |name: &str| -> Option<usize> {
      let i = words.iter().position(|w| *w == name)?;
      words.get(i + 1)?.parse::<i64>().ok().map(|v| v.max(0) as usize)
    };
    let white = self.engine.position.board.side_to_play == Color::White;
    let (clock, increment) =
      if white { (value("wtime"), value("winc")) } else { (value("btime"), value("binc")) };

    // The bot's time per move (src/bot/games/game.rs).
    let mut max_time = 0;
    if let Some(time_left) = clock {
      let increment = increment.unwrap_or(0).min(60_000);
      max_time = if time_left < 10_000 { 200 } else { time_left / 90 + increment * 10 / 9 };
    }
    if let Some(movetime) = value("movetime") {
      max_time = movetime;
    }
    let infinite = words.contains(&"infinite");
    self.engine.options.max_search_time = if infinite { 0 } else { max_time };
    self.engine.options.max_depth = if infinite { 0 } else { value("depth").unwrap_or(DEFAULT_MAX_DEPTH) };

    let engine = self.engine.clone();
    let random = self.random;
    self.search = Some(std::thread::spawn(move || {
                         engine.go();
                         report(&engine, white, random);
                       }));
  }

  fn setoption(&mut self, line: &str) {
    let Some(rest) = line.trim().strip_prefix("setoption name ") else { return };
    let Some((name, value)) = rest.split_once(" value ") else { return };
    let value = value.trim();
    match name.trim() {
      "Hash" => {
        if let Ok(mb) = value.parse::<usize>() {
          self.engine.resize_cache_tables(mb.clamp(1, 65536));
          self.forget_game();
        }
      },
      "Random" => self.random = value.eq_ignore_ascii_case("true"),
      "KeepCache" => self.keep_cache = value.eq_ignore_ascii_case("true"),
      "play_style" => self.engine.options.play_style = value.parse::<PlayStyle>().unwrap_or_default(),
      _ => {},
    }
  }
}

/// Prints the move the bot would play from the engine's analysis.
fn report(engine: &Engine, white: bool, random: bool) {
  let analysis = engine.get_analysis();
  if analysis.is_empty() {
    println!("bestmove 0000");
    return;
  }

  // The bot's choice (src/bot/games/game.rs): the lines within 0.015 of the best.
  let best_eval = analysis.get_eval().unwrap_or(f32::NAN);
  let mut cutoff = 1;
  while analysis.len() > cutoff {
    if analysis.get(cutoff).eval.is_nan() {
      break;
    }
    if (best_eval - analysis.get(cutoff).eval).abs() > 0.015 {
      break;
    } else {
      cutoff += 1;
    }
  }
  let index = if random { rand::rng().random_range(0..cutoff) } else { 0 };
  let line = analysis.get(index);
  let mv = line.variation.get_first_move().unwrap_or_default();

  println!("info score {} multipv {} pv{}",
           score(line.eval, white),
           cutoff,
           line.variation.to_string().to_lowercase());
  println!("bestmove {}", mv.to_string().to_lowercase());
}

/// The engine's evaluation, in pawns from White's side, as a UCI score from the mover's side.
fn score(eval: f32, white: bool) -> String {
  let own = if white { eval } else { -eval };
  if own.is_nan() {
    return "cp 0".to_string();
  }
  if own.abs() > 100.0 {
    // A mate in n plies scores 201 - n (src/chess/engine/eval/position.rs).
    let plies = (201.0 - own.abs()).max(1.0) as i32;
    let moves = (plies + 1) / 2;
    return format!("mate {}", if own > 0.0 { moves } else { -moves });
  }
  format!("cp {}", (own * 100.0) as i32)
}

fn main() {
  let mut uci = Uci::new();
  let stdin = std::io::stdin();
  for line in stdin.lock().lines() {
    let Ok(line) = line else { break };
    let words: Vec<&str> = line.split_whitespace().collect();
    match words.first().copied() {
      Some("uci") => {
        println!("id name schnecken_engine {}", env!("CARGO_PKG_VERSION"));
        println!("id author Nicolas Woltmann");
        println!("option name Hash type spin default {} min 1 max 65536", DEFAULT_HASH_MB);
        println!("option name Random type check default true");
        println!("option name KeepCache type check default true");
        println!("option name play_style type combo default Normal var Conservative var Normal var Aggressive var Provocative");
        println!("uciok");
      },
      Some("isready") => println!("readyok"),
      Some("setoption") => {
        uci.halt();
        uci.setoption(&line);
      },
      Some("ucinewgame") => {
        uci.halt();
        uci.engine.reset();
        uci.forget_game();
      },
      Some("position") => {
        uci.halt();
        uci.position(&words);
      },
      Some("go") => {
        uci.halt();
        uci.go(&words);
      },
      Some("stop") => uci.halt(),
      Some("quit") => break,
      _ => {},
    }
  }
  uci.halt();
}
