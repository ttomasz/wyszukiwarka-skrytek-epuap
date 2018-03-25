"""This file contains functions used to setup the DB schema, clean and load the csv file and upload the data to DB.
Requires environmental variables:
CSV_PATH - path to csv file with data to load
DB_STRING - psycopg2 string to connect to database
"""

import psycopg2
import pandas as pd
from os import environ
import re
from io import StringIO


def clean_text(text: str):
    """Method applies cleaning rules to text strings."""

    if type(text) != str:
        return text

    # list of tuples containing regex to match and what to substitute the match with along with a description
    rules = [
        (re.compile("\t"), " ", "Replace tab with a space."),
        (re.compile("[,;_]"), " ", "Replace commas, semicolons and '_' with spaces."),
        (re.compile("'"), "", "Remove single apostrophe ( ' )."),
        (re.compile("[\"]{2,}"), "\"", "Remove duplicate apostrophes."),
        (re.compile("\."), ". ", "Add a space after dot."),
        (re.compile("\s?-\s?"), " - ", "Add spaces around minus sign ( - )."),
        (re.compile("([^\s])(\".+\")"), "\\1 \\2", "Add space before quoted string if not exists."),
        (re.compile("(\".+\")([^\s])"), "\\1 \\2", "Add space after quoted string if not exists."),
        (re.compile("\s\s+"), " ", "Replace multi character whitespace with a single space."),
        (re.compile("^(\")(.+)(\"\s*)$"), "\\2", "Remove apostrophes from the beginning and the end of the string.")
    ]

    # apply all the rules to the string and return it
    for r in rules:
        text = r[0].sub(r[1], text)

    # trim the string
    s = text.strip()

    return s


def clean_text_gently(text: str):
    """Method tries to clean redundant whitespaces and similar without too much interference with the data.
    Also deletes '(miasto)' and '(wieś)' strings."""

    city = re.compile("\(miasto\)")
    village = re.compile("\(wieś\)")
    multi_spaces = re.compile("\s\s+")

    text = city.sub("", text)
    text = village.sub("", text)
    text = multi_spaces.sub(" ", text)

    return text.strip()


def load_into_db(csv: str):
    """Method loading csv in a string to the Database."""

    with psycopg2.connect(environ["DB_STRING"]) as conn:
        cur = conn.cursor()
        with StringIO(csv) as s:
            cur.copy_from(s, "skrytki", null="")
        conn.commit()


def read_and_clean_csv(path: str):
    """Method reads the csv from given path and applies cleaning function to all values
    then returns tab separated csv as a string."""

    df = pd.read_csv(
        filepath_or_buffer=path,
        sep=",",
        dtype={"NAZWA": object, "REGON": object, "ADRES": object, "KOD_POCZTOWY": object, "MIEJSCOWOSC": object,
               "URI": object}
    )

    df_trimmed = df[["ADRES", "MIEJSCOWOSC", "REGON", "KOD_POCZTOWY", "URI"]].astype(str).replace("nan", "").applymap(clean_text_gently)
    df_trimmed["NAZWA"] = df["NAZWA"].apply(clean_text)

    df_trimmed["ADR"] = df_trimmed["KOD_POCZTOWY"] + " " + df_trimmed["MIEJSCOWOSC"] + " " + df_trimmed["ADRES"]

    return df_trimmed[["NAZWA", "REGON", "ADR", "URI"]].to_csv(sep='\t', header=False, index=False, quoting=3)


def prepare_schema():
    """Method create table 'skrytki'."""

    sql = """
    CREATE EXTENSION IF NOT EXISTS pg_trgm;
    
    DROP TABLE IF EXISTS skrytki;
    
    CREATE TABLE skrytki (
        nazwa text,
        regon text,
        adres text,
        skrytka text
    );
    
    CREATE INDEX idx_nazwa ON skrytki USING GIN (nazwa gin_trgm_ops);
    CREATE INDEX idx_regon ON skrytki (regon);
    CREATE INDEX idx_adres ON skrytki USING GIN (adres gin_trgm_ops);
    
    CREATE OR REPLACE FUNCTION search(x text)
      RETURNS TABLE(nazwa text, regon text, adres text, skrytka text) AS
    $$
    BEGIN
     RETURN QUERY
     
        with 
        r as (
        select * from skrytki where skrytki.regon = x 
        ),
        n as (
        select * from skrytki where skrytki.nazwa ilike '%' || x || '%' limit 100
        ),
        a as (
        select * from skrytki where skrytki.adres ilike '%' || x || '%' limit 100
        )
        
        select * from r
        union all
        select * from n
        union all
        select * from a
        ;
     
    END; $$
     
    LANGUAGE plpgsql;
    """

    with psycopg2.connect(environ["DB_STRING"]) as conn:
        cur = conn.cursor()
        cur.execute(sql)
        conn.commit()


def truncate_table():
    """Method truncates table 'skrytki'."""

    with psycopg2.connect(environ["DB_STRING"]) as conn:
        cur = conn.cursor()
        cur.execute("TRUNCATE TABLE skrytki;")
        conn.commit()


if __name__ == '__main__':
    # print(read_and_clean_csv(environ["CSV_PATH"]))
    prepare_schema()
    truncate_table()
    load_into_db(read_and_clean_csv(environ["CSV_PATH"]))
