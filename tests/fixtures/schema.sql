-- Test schema for the WESPA API.
--
-- This mirrors the schema produced by the aardvark-ng loader (modules/Constants.pm)
-- and the production database. Keep it in sync with the loader's TABLES map when
-- the schema changes.

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS player_results;
DROP TABLE IF EXISTS tournament_results;
DROP TABLE IF EXISTS games;
DROP TABLE IF EXISTS divisions;
DROP TABLE IF EXISTS tournaments;
DROP TABLE IF EXISTS events;
DROP TABLE IF EXISTS player_alt_names;
DROP TABLE IF EXISTS players;
DROP TABLE IF EXISTS lexicons;
DROP TABLE IF EXISTS loaded_tournaments;

CREATE TABLE events (
  id INT NOT NULL AUTO_INCREMENT,
  start_date DATE DEFAULT NULL,
  end_date DATE DEFAULT NULL,
  link VARCHAR(255) DEFAULT NULL,
  sponsor VARCHAR(255) DEFAULT NULL,
  country VARCHAR(3) DEFAULT NULL,
  location VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE players (
  id INT NOT NULL AUTO_INCREMENT,
  name VARCHAR(255) DEFAULT NULL,
  country VARCHAR(3) DEFAULT NULL,
  photo VARCHAR(255) DEFAULT NULL,
  suspended TINYINT(1) DEFAULT NULL,
  deceased TINYINT(1) DEFAULT NULL,
  current TINYINT(1) DEFAULT NULL,
  provisional TINYINT(1) DEFAULT NULL,
  total_games INT DEFAULT NULL,
  last_played DATE DEFAULT NULL,
  rating INT DEFAULT NULL,
  title VARCHAR(3) DEFAULT NULL,
  norms VARCHAR(3) DEFAULT NULL,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE player_alt_names (
  id INT NOT NULL AUTO_INCREMENT,
  alt_name VARCHAR(255) DEFAULT NULL,
  player_id INT NOT NULL,
  PRIMARY KEY (id),
  KEY player_id (player_id),
  CONSTRAINT player_alt_names_ibfk_1 FOREIGN KEY (player_id) REFERENCES players (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE lexicons (
  id INT NOT NULL AUTO_INCREMENT,
  name VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE tournaments (
  id INT NOT NULL AUTO_INCREMENT,
  event_id INT NOT NULL,
  td VARCHAR(255) DEFAULT NULL,
  start_date DATE DEFAULT NULL,
  end_date DATE DEFAULT NULL,
  name VARCHAR(255) DEFAULT NULL,
  country VARCHAR(3) DEFAULT NULL,
  filename VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (id),
  KEY event_id (event_id),
  KEY idx_tournaments_filename (filename),
  CONSTRAINT tournaments_ibfk_1 FOREIGN KEY (event_id) REFERENCES events (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE divisions (
  id INT NOT NULL AUTO_INCREMENT,
  tournament_id INT NOT NULL,
  name VARCHAR(255) DEFAULT NULL,
  length INT DEFAULT NULL,
  number INT DEFAULT NULL,
  PRIMARY KEY (id),
  KEY tournament_id (tournament_id),
  CONSTRAINT divisions_ibfk_1 FOREIGN KEY (tournament_id) REFERENCES tournaments (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE games (
  id INT NOT NULL AUTO_INCREMENT,
  division_id INT NOT NULL,
  round INT DEFAULT NULL,
  lexicon_id INT NOT NULL,
  gcg_filename VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (id),
  KEY division_id (division_id),
  KEY lexicon_id (lexicon_id),
  CONSTRAINT games_ibfk_1 FOREIGN KEY (division_id) REFERENCES divisions (id),
  CONSTRAINT games_ibfk_2 FOREIGN KEY (lexicon_id) REFERENCES lexicons (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE tournament_results (
  id INT NOT NULL AUTO_INCREMENT,
  division_id INT NOT NULL,
  player_id INT NOT NULL,
  player_name VARCHAR(255) DEFAULT NULL,
  position INT DEFAULT NULL,
  wins FLOAT DEFAULT NULL,
  losses FLOAT DEFAULT NULL,
  byes INT DEFAULT NULL,
  spread INT DEFAULT NULL,
  prize_money INT DEFAULT NULL,
  prize_currency VARCHAR(255) DEFAULT NULL,
  prize_ech_rate VARCHAR(255) DEFAULT NULL,
  start_rating INT DEFAULT NULL,
  end_rating INT DEFAULT NULL,
  date DATE DEFAULT NULL,
  tournament_name VARCHAR(255) DEFAULT NULL,
  expected_wins FLOAT DEFAULT NULL,
  old_world_rank INT DEFAULT NULL,
  new_world_rank INT DEFAULT NULL,
  old_national_rank INT DEFAULT NULL,
  new_national_rank INT DEFAULT NULL,
  old_rating_dev INT DEFAULT NULL,
  new_rating_dev INT DEFAULT NULL,
  PRIMARY KEY (id),
  KEY division_id (division_id),
  KEY idx_tr_player_date (player_id, date),
  CONSTRAINT tournament_results_ibfk_1 FOREIGN KEY (division_id) REFERENCES divisions (id),
  CONSTRAINT tournament_results_ibfk_2 FOREIGN KEY (player_id) REFERENCES players (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE player_results (
  id INT NOT NULL AUTO_INCREMENT,
  player_id INT NOT NULL,
  game_id INT NOT NULL,
  score INT DEFAULT NULL,
  result INT DEFAULT NULL,
  PRIMARY KEY (id),
  KEY idx_pr_player_score_result_game (player_id, score, result, game_id),
  KEY idx_pr_game_player_score (game_id, player_id, score),
  CONSTRAINT player_results_ibfk_1 FOREIGN KEY (player_id) REFERENCES players (id),
  CONSTRAINT player_results_ibfk_2 FOREIGN KEY (game_id) REFERENCES games (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE loaded_tournaments (
  id INT NOT NULL AUTO_INCREMENT,
  name VARCHAR(255) DEFAULT NULL,
  filename VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

SET FOREIGN_KEY_CHECKS = 1;
