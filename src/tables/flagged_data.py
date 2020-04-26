from .table import Table

class Flagged_Data(Table):

    def __init__(self, user=None, passwd=None, hostname="localhost", db_name="aperture", verbose=False, engine=None):
        super().__init__(user, passwd, hostname, db_name, verbose, engine)
        self._table_name = "flagged_data"
        self._index_col = None
        self._expected_cols = set([
            "flag_id",
            "row_id"
        ])
        # flag_id is ON UPDATE CASCADE to anticipate flags table changing.
        # service_key shouldn't change.
        self._creation_sql = "".join(["""
            CREATE TABLE IF NOT EXISTS """, self._schema, ".", self._table_name, """
            (
                flag_id INTEGER REFERENCES """, self._schema, """.flags(flag_id) ON UPDATE CASCADE,
                service_key INTEGER REFERENCES """, self._schema, """.service_periods(service_key),
                row_id INTEGER,
                PRIMARY KEY (flag_id, service_key, row_id)
            );"""])


    def write_table(self, flags, append=True):
       pass 
