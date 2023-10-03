import sqlite3


class SystemPromptHandler:
    def __init__(self, db_connection):
        self.conn = db_connection
        self.cur = self.conn.cursor()
        self.create_table()

    def create_table(self):
        """Create a table for system prompts if it doesn't exist."""
        self.cur.execute(
            """
            CREATE TABLE IF NOT EXISTS system_prompts (
                id INTEGER PRIMARY KEY,
                prompt TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        self.conn.commit()

    def create_prompt(self, prompt_id, prompt):
        """Create a new system prompt."""
        try:
            self.cur.execute(
                """
                INSERT INTO system_prompts (id, prompt) VALUES (?, ?)
            """,
                (prompt_id, prompt),
            )
            self.conn.commit()
        except sqlite3.IntegrityError:
            print(f"Prompt '{prompt}' with ID '{prompt_id}' already exists.")

    def read_prompt(self, prompt_id):
        """Read a system prompt by ID."""
        self.cur.execute(
            """
            SELECT * FROM system_prompts WHERE id = ?
        """,
            (prompt_id,),
        )
        return self.cur.fetchone()

    def update_prompt(self, prompt_id, new_prompt):
        """Update a system prompt by ID."""
        self.cur.execute(
            """
            UPDATE system_prompts
            SET prompt = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """,
            (new_prompt, prompt_id),
        )
        self.conn.commit()

    def delete_prompt(self, prompt_id):
        """Delete a system prompt by ID."""
        self.cur.execute(
            """
            DELETE FROM system_prompts WHERE id = ?
        """,
            (prompt_id,),
        )
        self.conn.commit()

    def list_prompts(self):
        """List all system prompts."""
        self.cur.execute(
            """
            SELECT * FROM system_prompts
        """
        )
        return self.cur.fetchall()
