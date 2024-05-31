"""
    @about: Convience wrapper allowing extended control of pandas upload to a database
"""
import os
import logging
from typing import Dict, List, Any
from concurrent.futures import ThreadPoolExecutor


from numpy import datetime64
import pandas as pd

from tqdm import tqdm
from psycopg2 import sql
from psycopg2.extras import RealDictCursor

log = logging.getLogger(__name__)


def chunk_list(input_list: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Splits a list into smaller sub-lists (chunks) of the given size.

    Parameters:
        input_list (list): The list to be chunked.
        chunk_size (int): The desired size of each chunk.

    Returns:
        list: A list of sub-lists, each containing 'chunk_size' number of elements.
    """
    return [input_list[i:i + chunk_size] for i in range(0, len(input_list), chunk_size)]


class PandaSqlPlus:
    """
    Object used to have finer control of uploading data from sql to pandas
    """

    def __init__(self, sql_engine: str, threads: int = os.cpu_count() * 2) -> None:
        self.connection = sql_engine
        self.threads = threads

    def pull_table_constraints(self, schema_name: str, table_name: str) -> Dict[str, str]:
        """
        [summary]

        Args:
            schema_name (str): [description]
            table_name (str): [description]

        Returns:
            Dict[str, str]: [description]
        """
        query = sql.SQL(
            """
            SELECT con.*
            FROM pg_catalog.pg_constraint con
                 INNER JOIN pg_catalog.pg_class rel
                            ON rel.oid = con.conrelid
                 INNER JOIN pg_catalog.pg_namespace nsp
                            ON nsp.oid = connamespace
            WHERE nsp.nspname = {schema_name}
             AND rel.relname = {table_name};
        """
        )

        query = query.format(schema_name=sql.Identifier(schema_name), table_name=sql.Identifier(table_name))

        query = query.as_string(self.connection)
        query = query.replace('"', "'")

        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, (table_name,))
            data = cursor.fetchall()

        # Converts data to list of dictionarys
        constaint_data = map(lambda x: dict(x), data)  # pylint: disable=unnecessary-lambda
        constaint_data = list(constaint_data)

        # Extracts out the values that are needed
        keys = map(lambda x: x.get("conname"), constaint_data)
        keys = list(keys)

        return keys

    def pull_table_details(self, schema_name: str, table_name: str) -> List[Dict[str, str]]:
        """
        [summary]

        Args:
            schema_name (str): [description]
            table_name (str): [description]

        Returns:
            List[Dict[str, str]]: [description]
        """
        table_query = (
            sql.SQL(
                """
            SELECT
                table_schema,
                table_name,
                column_name,
                data_type
            FROM INFORMATION_SCHEMA.columns
            WHERE table_schema = {table_schema}
            AND table_name = %s;
        """
            )
            .format(table_schema=sql.Identifier(schema_name))
            .as_string(self.connection)
        )

        table_query = table_query.replace('"', "'")
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(table_query, (table_name,))
            data = cursor.fetchall()

        # Converts data to list of dictionarys
        data = map(lambda x: dict(x), data)  # pylint: disable=unnecessary-lambda
        data = list(data)

        return data

    def _validate_columns_match_table(self, columns: List[str], schema_name: str, table_name: str) -> bool:

        data = self.pull_table_details(schema_name, table_name)
        column_names = map(lambda x: x.get("column_name"), data)
        column_names = list(column_names)
        diff = set(column_names) - set(columns)
        if diff not in set(column_names):
            print(diff)
            return True

        return False

    def _generate_prepared_upsert_query(
        self, schema_name: str, table_name: str, columns: List[str], update_rows: bool = False
    ) -> str:
        """
        Creates sql statement for upload handing for conflicts, can update all rows or ignore

        Args:
            schema_name (str): [description]
            table_name (str): [description]
            columns (List[str]): [description]
            update_rows (bool, optional): [description]. Defaults to False.

        Raises:
            ValueError: If table has no constraint key

        Returns:
            str: [description]
        """

        constraint_keys = self.pull_table_constraints(schema_name, table_name)
        if len(constraint_keys) == 0:
            raise ValueError("Can only upsert to tables with constraint keys set")
        elif len(constraint_keys) == 1:
            constraint_keys = constraint_keys[0]
        else:
            constraint_keys = ", ".join(constraint_keys)

        if update_rows is False:
            update_query = sql.Identifier("DO NOTHING")
        else:
            # https://dba.stackexchange.com/a/282199
            update_query = sql.SQL(
                "DO UPDATE SET ({column_names}) = ROW (excluded.*) WHERE ({table_name}.*) IS DISTINCT FROM (excluded.*)"
            ).format(
                column_names=sql.SQL(", ").join(sql.Identifier(n) for n in columns),
                table_name=sql.Identifier(table_name),
            )

        base_query = sql.SQL(
            """
            INSERT INTO {schema_name}.{table_name} ({column_names})
            VALUES ({column_placeholders})
            ON CONFLICT ON CONSTRAINT {contraints}
            {update_query};
        """
        )

        formatted_query = base_query.format(
            schema_name=sql.Identifier(schema_name),
            table_name=sql.Identifier(table_name),
            column_names=sql.SQL(", ").join(sql.Identifier(n) for n in columns),
            column_placeholders=sql.SQL(", ").join(sql.Placeholder() * len(columns)),
            contraints=sql.Identifier(constraint_keys),
            update_query=update_query,
        )

        formatted_query = formatted_query.as_string(self.connection)
        formatted_query = formatted_query.replace('"', "")

        return formatted_query

    def _clean_up_column_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Updates the columns in the dataframe to ensure that the correct format is used
        for uploading to select

        looks at datetime objects like np.datetime64

        Args:
            df (pd.DataFrame): [description]

        Returns:
            pd.DataFrame: [description]
        """
        temp_df = df.select_dtypes(include=[datetime64])

        # if no datetime, return the object
        if temp_df.empty is True:
            return df

        datetime_columns = list(temp_df.columns)
        for i in datetime_columns:
            df[i] = df[i].dt.strftime(date_format="%Y-%m-%d %H:%M:%S")

        return df

    def _upload_data(self, query: str, data: List[List[str]]) -> None:
        """
        [summary]

        Args:
            query (str): [description]
            data (List[List[str]]): [description]
        """

        with self.connection.cursor() as cursor:
            for row in data:
                cursor.execute(query, row)


    def upsert_dataframe(self, df: pd.DataFrame, schema_name: str, table_name: str, update_rows: bool = True) -> None:
        """
        Upserts Pandas DataFrame to postrgres database, handles both updating rows or ignoring if contraint is already met.
        Requires tables to be predefined and contraints set correctly to work

        Args:
            df (pd.DataFrame): [description]
            schema_name (str): [description]
            table_name (str): [description]
            update_rows (bool, optional): [description]. Defaults to True.
        """
        # Pre checks before inserting data into table
        self._validate_columns_match_table(list(df.columns), schema_name, table_name)

        # Sorts out columns types and order
        df = self._clean_up_column_types(df)
        table_data = self.pull_table_details(schema_name, table_name)
        column_names = map(lambda x: x.get("column_name"), table_data)
        column_names = list(column_names)
        df = df[column_names]

        logging.info("generating upsert query")
        upsert_query = self._generate_prepared_upsert_query(schema_name, table_name, list(df.columns), update_rows)
        logging.info(f"uploading {len(df)} rows to {schema_name}.{table_name}")

        # Converts to a list of list values for insertion into query
        df = df.to_dict("records")
        df = [[value for value in row.values()] for row in df]
        # df = chunk_list(df, self.threads)
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = []
            for chunk in tqdm(df, total=len(df), unit="chunks", desc="Submitting data to threads", leave=False):
                future = executor.submit(self._upload_data, upsert_query, [chunk])
                futures.append(future)

            for future in tqdm(futures, total=len(futures), unit="chunks", desc="uploading data", leave=False):
                future.result()

        return None





if __name__ == "__main__":
    pass
