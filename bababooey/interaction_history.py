from collections.abc import Sequence
import datetime
import json
import os
import sqlite3

import discord

_DB_DIR = 'data/'
_DB_NAME = 'interaction_history.db'
_TABLE_NAME = 'interaction_history'


class InteractionHistory:
    """Stores a history of ApplicationInteractions."""

    def __init__(self):
        if not os.path.exists(_DB_DIR):
            os.makedirs(_DB_DIR)
        self._con = sqlite3.connect(_DB_DIR + _DB_NAME)
        self._create_table_if_missing()

    def _create_table_if_missing(self):
        cur = self._con.cursor()
        res = cur.execute('SELECT name FROM sqlite_master').fetchone()
        if res is not None and _TABLE_NAME in res:
            return
        cur.execute(
            f'CREATE TABLE {_TABLE_NAME}(datetime, user_id, guild_id, channel_id, message_id, type, raw_data)'
        )
        self._con.commit()
        cur.close()

    def record_usage(self, interaction: discord.Interaction) -> None:
        """Records someone triggering and interaction."""
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        cur = self._con.cursor()

        message_id = 'None'
        if interaction.message is not None:
            message_id = str(interaction.message.id)

        cur.execute(f'INSERT INTO {_TABLE_NAME} VALUES(?, ?, ?, ?, ?, ?, ?)',
                    (now, interaction.user.id, str(interaction.guild_id),
                     str(interaction.channel_id), message_id,
                     interaction.type.name, json.dumps(interaction.data)))
        self._con.commit()
        cur.close()

    def fetch_all_history(
            self) -> Sequence[tuple[datetime.datetime, int, str, dict]]:
        """Return all the history.
        
        Each row is in this format:
        (utc_datetime, user_id, type, raw_data)
        """
        cur = self._con.cursor()

        def none_or_int(x: None | str) -> None | int:
            if x.lower() == 'none':
                return None
            return int(x)

        res = [{
            'datetime': datetime.datetime.fromisoformat(row[0]),
            'user_id': row[1],
            'guild_id': none_or_int(row[2]),
            'channel_id': none_or_int(row[3]),
            'message_id': none_or_int(row[4]),
            'type': row[5],
            'raw_data': json.loads(row[6]),
        } for row in cur.execute(
            f'SELECT datetime, user_id, guild_id, channel_id, message_id, type, raw_data FROM {_TABLE_NAME}'
        )]
        res.sort(key=lambda x: x['datetime'], reverse=True)
        return res