#!/usr/bin/env python3
"""
Build n-gram next-word prediction tables in the existing SQLite database.

Reads Google Books English n-gram CSV files (2-5 grams) and populates
an 'ngrams' table in words_with_frequency_and_translation_and_ipa.sqlite3.

Usage:
    python3 dictionary/build_ngrams.py
"""

import csv
import os
import sqlite3
import sys

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GOOGLE_NGRAMS_DIR = os.path.join(
    os.path.dirname(BASE_DIR),
    "..",
    "google-books-ngram-frequency",
    "ngrams",
)
DB_PATH = os.path.join(BASE_DIR, "words_with_frequency_and_translation_and_ipa.sqlite3")

# English n-gram files
NGRAM_FILES = {
    2: os.path.join(GOOGLE_NGRAMS_DIR, "2grams_english.csv"),
    3: os.path.join(GOOGLE_NGRAMS_DIR, "3grams_english.csv"),
    4: os.path.join(GOOGLE_NGRAMS_DIR, "4grams_english.csv"),
    5: os.path.join(GOOGLE_NGRAMS_DIR, "5grams_english.csv"),
}


def build_ngrams():
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=OFF")

    # Create the ngrams table
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ngrams (
            n INTEGER NOT NULL,
            context TEXT NOT NULL,
            next_word TEXT NOT NULL,
            frequency INTEGER NOT NULL,
            PRIMARY KEY (n, context, next_word)
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_ngrams_context ON ngrams(n, context)
        """
    )

    # Clear existing ngram data
    conn.execute("DELETE FROM ngrams")

    total_rows = 0
    for n, filepath in sorted(NGRAM_FILES.items()):
        if not os.path.exists(filepath):
            print(f"WARNING: File not found: {filepath}", file=sys.stderr)
            continue

        print(f"Processing {n}-grams from {os.path.basename(filepath)}...")

        rows = []
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                ngram = row["ngram"].strip()
                freq = int(row["freq"])

                # Split into words
                words = ngram.split()
                if len(words) != n:
                    # Skip malformed rows
                    continue

                # Context = all words except the last
                # next_word = the last word
                context = " ".join(words[:-1]).lower()
                next_word = words[-1].lower()

                rows.append((n, context, next_word, freq))

        # Batch insert
        conn.executemany(
            "INSERT OR IGNORE INTO ngrams (n, context, next_word, frequency) VALUES (?, ?, ?, ?)",
            rows,
        )
        conn.commit()
        count = len(rows)
        total_rows += count
        print(f"  Inserted {count} {n}-grams")

    # Create the index after all inserts
    print("Creating index...")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ngrams_context ON ngrams(n, context)")

    # Print statistics
    row_count = conn.execute("SELECT COUNT(*) FROM ngrams").fetchone()[0]
    conn.close()

    print(f"\nDone! Total n-gram rows in database: {row_count}")
    print(f"Database size: {os.path.getsize(DB_PATH) / (1024*1024):.1f} MB")


if __name__ == "__main__":
    build_ngrams()
