import sqlite3
import pandas as pd
from typing import Optional
import psycopg2


class DBEngine:
    def __init__(self, db_type: str = "sqlite", connection_string: Optional[str] = None):
        """
        db_type: sqlite / postgres / mysql (extensible)
        connection_string: path or URI
        """
        self.db_type = db_type
        self.connection_string = connection_string
        self.conn = None

    def connect(self):
        """
        Establish DB connection (read-only where possible)
        """
        if self.db_type == "sqlite":
            uri = f"file:{self.connection_string}?mode=ro"
            self.conn = sqlite3.connect(uri, uri=True)

        elif self.db_type == "postgres":
            # connection_string should be DSN
            self.conn = psycopg2.connect(self.connection_string)

        else:
            raise NotImplementedError(f"{self.db_type} not supported yet")

        print(f"[DB] Connected to {self.db_type}")

    def list_tables(self):
        """
        List available tables
        """
        if self.db_type == "sqlite":
            query = "SELECT name FROM sqlite_master WHERE type='table';"
            df = pd.read_sql(query, self.conn)
            return df["name"].tolist()

        elif self.db_type == "postgres":
            query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            """
            df = pd.read_sql(query, self.conn)
            return df["table_name"].tolist()

        return []

    def get_schema(self):
        """
        Returns schema info: tables + columns + types
        """
        schema = {}

        if self.db_type == "sqlite":
            tables = self.list_tables()

            for table in tables:
                query = f"PRAGMA table_info({table});"
                df = pd.read_sql(query, self.conn)

                schema[table] = []
                for _, row in df.iterrows():
                    schema[table].append({
                        "column": row["name"],
                        "type": row["type"]
                    })

        elif self.db_type == "postgres":
            query = """
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
            ORDER BY table_name
            """
            df = pd.read_sql(query, self.conn)

            for _, row in df.iterrows():
                table = row["table_name"]
                if table not in schema:
                    schema[table] = []

                schema[table].append({
                    "column": row["column_name"],
                    "type": row["data_type"]
                })

        return schema

    def safe_query(self, query: str, limit: int = 10000) -> pd.DataFrame:
        """
        Execute ONLY SELECT queries safely
        """
        query_clean = query.strip().lower()

        # prevent multiple statements
        if ";" in query_clean[:-1]:
            raise ValueError("Multiple statements not allowed")

        if not query_clean.startswith("select"):
            raise ValueError("Only SELECT queries are allowed (read-only mode)")

        # enforce LIMIT if not present
        if "limit" not in query_clean:
            query = query.rstrip(";") + f" LIMIT {limit}"

        print(f"[DB] Executing query: {query}")

        try:
            df = pd.read_sql(query, self.conn)
        except Exception as e:
            raise RuntimeError(f"Query execution failed: {e}")

        return df

    def preview_table(self, table_name: str, limit: int = 5):
        """
        Quick preview of a table
        """
        query = f"SELECT * FROM {table_name} LIMIT {limit}"
        return self.safe_query(query)

    def close(self):
        if self.conn:
            self.conn.close()
            print("[DB] Connection closed")


# --- Utility function ---
def load_table_as_df(db_path: str, table_name: str) -> pd.DataFrame:
    """
    Quick helper to load full table (safe)
    """
    db = DBEngine(db_type="sqlite", connection_string=db_path)
    db.connect()
    df = db.safe_query(f"SELECT * FROM {table_name}")
    db.close()
    return df
