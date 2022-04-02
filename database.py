from audioop import add
import sqlite3 as sql
import os
from tinytag import TinyTag

# Default location is the location of this module
db_path = os.path.dirname(__file__)
db_file = db_path + '/' + ".library.db"
con = sql.connect(db_file)


def cleardb():
    """
    Drop all the tables in the db
    """
    cur = con.cursor()
    cur.executescript('''DROP TABLE IF EXISTS artists;
                        DROP TABLE IF EXISTS songs;
                        DROP TABLE IF EXISTS albums;''')
    con.commit()
    cur.close()


def createdb():
    """
    Create the a hidden db file and the schema
    """
    cur = con.cursor()
    cur.executescript('''
            CREATE TABLE IF NOT EXISTS artists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            );
            CREATE TABLE IF NOT EXISTS albums (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL DEFAULT "UNKNOWN",
                artist_id INTEGER DEFAULT 0,
                UNIQUE (name,artist_id),
                FOREIGN KEY (artist_id) REFERENCES artists(id) ON DELETE SET DEFAULT
            ); 
            CREATE TABLE IF NOT EXISTS songs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL DEFAULT "UNKNOWN",
                album_id INTEGER DEFAULT 0,
                artist_id INTEGER DEFAULT 0,
                length INTEGER DEFAULT 0,
                added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                path TEXT,
                FOREIGN KEY (album_id)  REFERENCES albums(id)  ON DELETE SET DEFAULT,
                FOREIGN KEY (artist_id) REFERENCES artists(id) ON DELETE SET DEFAULT,
                UNIQUE (name, artist_id, album_id)
            );
            INSERT OR IGNORE INTO artists(id,name) VALUES (0,'UNKNOWN');
            INSERT OR IGNORE INTO albums(id,name) VALUES (0,"UNKNOWN");
            ''')

    con.commit()
    cur.close()


def addSingle(music_file: str):
    """ 
    Add a single song, artist and album to the database

    Parameters
    ----------
    music_file: string
                full path to the song

    Returns
    ---------
    name, album, artist, length, path
    """
    cur = con.cursor()
    audiofile = TinyTag.get(music_file)
    name = audiofile.title
    album = audiofile.album
    artist = audiofile.artist
    length = audiofile.duration
    if album:
        album = album.replace('"', "'")
        
    if artist:
        cur.execute(
            f'INSERT OR IGNORE INTO artists(name) VALUES ("{artist}");')

    if album and artist:
        cur.execute(f'''INSERT OR IGNORE INTO albums(name,artist_id) 
                            SELECT "{album}", 
                                    (SELECT id FROM artists WHERE name = "{artist}");''')

    if not name:
        name = music_file.split('/')[-1].split(".")[0]
    cur.execute(f'''INSERT OR IGNORE INTO songs(name, length, path, album_id, artist_id)
                            SELECT "{name}",{length}, "{music_file}",
                                    (SELECT COALESCE( (SELECT id FROM albums WHERE name = "{album}") ,0) ), 
                                    (SELECT COALESCE( (SELECT id FROM artists WHERE name = "{artist}"),0) );
                    ''')
    cur.close()
    return name, length

def addRecords(music_dir: str = "/home/mohamed/Downloads"):
    """
    Add the songs, artists, albums and lengths to the database

    Parameters
    ----------
    music_dir: string
                folder path that contains the songs you want to add to the database

    Returns
    -------
    n: integer
        number of succesfully added songs

    """
    if not os.path.isdir(music_dir):
        raise ValueError("Not a valid directory")

    n = 0
    names = []
    for file_ in os.listdir(music_dir):
        if file_.split('.')[-1] in ["mp3", "wav", "ogg"]:
            n += 1
            name, _ = addSingle(music_dir + '/' + file_)
            names.append(name)

    return n, names


def search(search_word: str, search_by: str = "name") -> dict:
    """
    Search the database for artists, songs, and albums 

    Parameters
    ----------
    search_word: string
                The search word used in the search 

    search_by: string
                Specifies the type of search "name" searches for artists,songs or albums with names similar to search_word
                "album" and "artist" returns songs ONLY that have album or artist with the EXACT match to search_word

    Returns
    -------
    results: dictionary [strings:list of tuples]
                dictionary with keys (songs, artists and albums) that match the search_word
                setting the search_by to either "album" or "artist" return a single key ("songs")

    """
    if search_by.lower() not in ["album", "artist", "name"]:
        raise ValueError("Wrong value for second argument")

    results = {"Songs": []}
    search_word = search_word.lower()
    cur = con.cursor()

    if search_by == "name":
        cur.execute(f'''SELECT songs.name, artists.name, songs.path, songs.length
                        FROM songs 
                            JOIN artists 
                            ON songs.artist_id = artists.id 
                        WHERE songs.name LIKE "%{search_word}%";''')
        for row in cur.fetchall():
            name, artist, path, length = row[0], row[1], row[2], f'{row[3]:.4f}'
            if not os.path.exists(path):
                cur.execute(f'DELETE FROM songs WHERE name = "{name}";')
                continue
            results["Songs"] += [(name, artist, path, length)]

        cur.execute(
            f'SELECT name FROM artists WHERE name LIKE "%{search_word}%" AND id != 0;')
        results["Artists"] = [(row[0],) for row in cur.fetchall()]

        cur.execute(
            f'SELECT name FROM albums WHERE name LIKE "%{search_word}%" AND id != 0;')
        results["Albums"] = [(row[0],) for row in cur.fetchall()]

    elif search_by == "artist" or search_by == "album":
        cur.execute(f''' SELECT songs.name, artists.name, songs.path
                        FROM songs
                            JOIN artists
                            ON songs.artist_id = artists.id
                        WHERE songs.{search_by}_id = (SELECT id 
                                                        FROM {search_by}s
                                                        WHERE name LIKE "{search_word}");
                    ''')
        for row in cur.fetchall():
            name, artist, path = row[0], row[1], row[2]
            if not os.path.exists(path):
                cur.execute(f'DELETE FROM songs WHERE name = "{name}";')
                continue
            results["Songs"] += [(name, artist, path)]

    con.commit()
    cur.close()
    return results

def deleteSong(song_name: str):
    """
    Delete certain song in the data base

    Parameters
    =========================
    song_name: string
        the name of the song to be deleted
    """
    cur = con.cursor()
    cur.executescript(f'DELETE FROM songs WHERE name = "{song_name}";')
    con.commit()
    cur.close()
