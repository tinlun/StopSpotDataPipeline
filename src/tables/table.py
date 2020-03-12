import abc
import sys
import getpass
import pandas
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError


""" Subclasses should declare/initialize:
str self._schema
str self._table_name
str self._index_col
    For the purposes of loading via Pandas' index_col parameter.
str set self._expected_cols
    This will contain a set of strings of the columns in the table.
str self._creation_sql

Additionally, subclasses should not alter self._engine in any capacity.
"""
class Table(abc.ABC):

    ###########################################################################
    # Public Methods

    # passwd is not stored as member data, it is destroyed after use.
    def __init__(self, user=None, passwd=None, hostname="localhost", db_name="aperature", verbose=False, engine=None):
        self.verbose = verbose
        self._chunksize = 1000
        self._engine = None

        if engine is not None:
            self._engine = create_engine(engine)

        else:
            user = None
            passwd = None
            hostname = hostname
            db_name = db_name

            if user is None:
                user = self._prompt("Enter username: ")
            else:
                user = user

            if passwd is None:
                passwd = self._prompt("Enter password: ", hide_input=True)
            else:
                passwd = passwd

            self._build_engine(user, passwd, hostname, db_name)

    #######################################################

    def get_engine(self):
        return self._engine

    #######################################################
    
    # NOTE: if there is no ctran_data table, this will not work, obviously.
    def get_full_table(self):
        if self._engine is None:
            self._print("ERROR: self._engine is None, cannot continue.")
            return None

        df = None
        sql = "".join(["SELECT * FROM ", self._schema, ".", self._table_name, ";"])
        self._print(sql)
        try:
            df = pandas.read_sql(sql, self._engine, index_col=self._index_col)

        except SQLAlchemyError as error:
            print("SQLAclchemy:", error)
            return None
        except ValueError as error:
            print("Pandas:", error)
            return None
        
        # You may be tempted to attempt to optimize this by doing list
        # comparisons, but that can be weirdly unpredictable.
        if set(list(df)) != self._expected_cols:
            self._print("ERROR: the columns of read data does not match the specified columns.")
            return None

        return df

    #######################################################

    def create_schema(self):
        if self._engine is None:
            self._print("ERROR: self._engine is None, cannot continue.")
            return False

        self._print("Connecting to DB.")
        sql = "".join(["CREATE SCHEMA IF NOT EXISTS ", self._schema, ";"])
        try:
            with self._engine.connect() as conn:
                self._print(sql)
                conn.execute(sql)

        except SQLAlchemyError as error:
            print("SQLAclchemy:", error)
            return False

        self._print("Done.")
        return True

    #######################################################

    def delete_schema(self):
        if self._engine is None:
            self._print("ERROR: self._engine is None, cannot continue.")
            return False

        self._print("Connecting to DB.")
        sql = "".join(["DROP SCHEMA IF EXISTS ", self._schema, " CASCADE;"])
        try:
            with self._engine.connect() as conn:
                self._print(sql)
                conn.execute(sql)

        except SQLAlchemyError as error:
            print("SQLAclchemy:", error)
            return False

        self._print("Done.")
        return True

    #######################################################
    
    def create_table(self):
        if self._engine is None:
            self._print("ERROR: self._engine is None, cannot continue.")
            return False

        if not self.create_schema():
            self._print("ERROR: failed to create schema, cancelling operation.")
            return False

        self._print("Connecting to DB.")
        try:
            with self._engine.connect() as conn:
                self._print(self._creation_sql)
                conn.execute(self._creation_sql)

        except SQLAlchemyError as error:
            print("SQLAclchemy:", error)
            return False

        self._print("Done.")
        return True

    #######################################################

    def delete_table(self):
        if self._engine is None:
            self._print("ERROR: self._engine is None, cannot continue.")
            return False

        self._print("Connecting to DB.")
        sql = "".join(["DROP TABLE IF EXISTS " + self._schema + "." + self._table_name + ";"])
        try:
            with self._engine.connect() as conn:
                self._print(sql)
                conn.execute(sql)

        except SQLAlchemyError as error:
            print("SQLAclchemy:", error)
            return False

        self._print("Done.")
        return True

    ###########################################################################
    # Private Methods

    def _build_engine(self, user, passwd, hostname, db_name):
        engine_info = ["postgresql://", user, ":", passwd, "@", hostname, "/", db_name]
        self._engine = create_engine("".join(engine_info))
        
        self._print("Your engine has been created: ", self._engine)
        return True

    #######################################################

    def _prompt(self, prompt="", hide_input=False):
        while True:
            try:
                value = None
                if hide_input:
                    value = getpass.getpass(prompt)
                else:
                    value = input(prompt)
                return value
            except EOFError:
                print()

    #######################################################

    def _print(self, string, obj=None, force=False):
        if not force:
            if not self.verbose:
                return

        if obj is None:
            print(string)

        else:
            print(string, end="")
            print(obj)