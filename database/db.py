import sqlite3

def init_db():
    """Initialize the SQLite database with metadata tables."""
    conn = sqlite3.connect("metadata.db")
    cursor = conn.cursor()

    # Table for storing document-level metadata
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS document_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            file_type TEXT,
            chunking_method TEXT,
            embedding_model TEXT,
            chunk_count INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Table for storing individual chunk text
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chunk_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER,
            chunk_index INTEGER,
            chunk_text TEXT,
            FOREIGN KEY(document_id) REFERENCES document_metadata(id)
        )
    ''')

    # Table for storing interview booking details
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS interview_bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL,
            date TEXT NOT NULL,  -- 'YYYY-MM-DD' format
            time TEXT NOT NULL,  -- 'HH:MM' 24-hour format
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()

def insert_document_metadata(filename, file_type, chunking_method, embedding_model, chunk_count):
    """Insert metadata about a document and return its document_id."""
    conn = sqlite3.connect("metadata.db")
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO document_metadata (filename, file_type, chunking_method, embedding_model, chunk_count)
        VALUES (?, ?, ?, ?, ?)
    ''', (filename, file_type, chunking_method, embedding_model, chunk_count))

    document_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return document_id

def insert_chunk_metadata(document_id, chunks):
    """Insert each chunk associated with a document_id."""
    conn = sqlite3.connect("metadata.db")
    cursor = conn.cursor()

    for index, chunk in enumerate(chunks):
        cursor.execute('''
            INSERT INTO chunk_metadata (document_id, chunk_index, chunk_text)
            VALUES (?, ?, ?)
        ''', (document_id, index, chunk))

    conn.commit()
    conn.close()


# NEW: Insert a booking record into interview_bookings table
def insert_booking(full_name: str, email: str, date: str, time: str):
    """
    Insert a new interview booking.

    Args:
        full_name (str): Full name of the candidate.
        email (str): Email address.
        date (str): Date in 'YYYY-MM-DD' format.
        time (str): Time in 'HH:MM' 24-hour format.
    """
    conn = sqlite3.connect("metadata.db")
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO interview_bookings (full_name, email, date, time)
        VALUES (?, ?, ?, ?)
    ''', (full_name, email, date, time))

    conn.commit()
    conn.close()