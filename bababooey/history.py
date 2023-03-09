from collections.abc import Sequence
import datetime
import os
import sqlite3

import discord


class UserSoundEffectHistory:
    """Stores a mapping from users to sound effect usage history."""

    def __init__(self):
        if not os.path.exists('data/'):
            os.makedirs('data/')
        self._con = sqlite3.connect('data/user_sound_effect_history.db')
        self._create_table_if_missing()

    def _create_table_if_missing(self):
        cur = self._con.cursor()
        res = cur.execute('SELECT name FROM sqlite_master').fetchone()
        if res is not None and 'user_history' in res:
            return
        cur.execute(
            'CREATE TABLE user_history(datetime, user_id, guild_id, num)')
        self._con.commit()
        cur.close()

    def record_usage(self, user: discord.Member, effect_num: int) -> None:
        """Records user playing sound effect with effect_num."""
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        cur = self._con.cursor()
        cur.execute('INSERT INTO user_history VALUES(?, ?, ?, ?)',
                    (now, user.id, user.guild.id, effect_num))
        self._con.commit()
        cur.close()

    def users_most_recent(self, user: discord.Member,
                          limit: int) -> Sequence[int]:
        """Returns at most limit number of most recent sfx_nums that user used."""
        cur = self._con.cursor()
        res = [
            row[1] for row in cur.execute(
                'SELECT MAX(datetime) AS most_recent_use, num FROM user_history WHERE user_id=? GROUP BY num ORDER BY most_recent_use DESC',
                (user.id,))
        ]
        return res[0:limit]

    def fetch_all_history(
            self) -> Sequence[tuple[datetime.datetime, int, int, int]]:
        """Return all the history.
        
        Each row is in this format:
        (utc_datetime, user_id, guild_id, sfx_num)
        """
        cur = self._con.cursor()
        res = [[
            datetime.datetime.fromisoformat(row[0]), row[1], row[2], row[3]
        ] for row in cur.execute(
            'SELECT datetime, user_id, guild_id, num FROM user_history')]
        res.sort(key=lambda x: x[0], reverse=True)
        return res