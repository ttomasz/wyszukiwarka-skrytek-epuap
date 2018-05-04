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
    Also deletes '(miasto)', (dzielnica m.st. Warszawy), and '(wieś)' strings."""

    city = re.compile("\(miasto\)")
    village = re.compile("\(wieś\)")
    warsaw = re.compile("\(dzielnica m.st. Warszawy\)")
    delegatura = re.compile("\(delegaura\)")
    multi_spaces = re.compile("\s\s+")

    text = city.sub("", text)
    text = village.sub("", text)
    text = warsaw.sub(" - Warszawa ", text)
    text = delegatura.sub("", text)
    text = multi_spaces.sub(" ", text)

    return text.strip()


def load_into_db(tsv_skrytki: str, tsv_skrytki2: str):
    """Method loading csv in a string to the Database."""

    with psycopg2.connect(environ["DB_STRING"]) as conn:
        cur = conn.cursor()
        with StringIO(tsv_skrytki) as s:
            cur.copy_from(s, "skrytki", null="")
        conn.commit()
        with StringIO(tsv_skrytki2) as s:
            cur.copy_from(s, "skrytki2", null="")
        conn.commit()


def read_and_clean_csv(path: str):
    """ DEPRECATED.
    Method reads the csv from given path and applies cleaning function to all values
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


def read_csv(path: str):
    """Method reads the csv with data for our application from given path then returns pandas dataframe."""

    df = pd.read_csv(
        filepath_or_buffer=path,
        sep=",",
        dtype={"NAZWA": object, "REGON": object, "ADRES": object, "KOD_POCZTOWY": object, "MIEJSCOWOSC": object,
               "URI": object}
    )

    return df


def clean_df(df):
    """Method applies cleaning functions to dataframe."""

    df_trimmed = df[["ADRES", "MIEJSCOWOSC", "REGON", "KOD_POCZTOWY", "URI"]].astype(str).replace("nan", "").applymap(clean_text_gently)
    df_trimmed["NAZWA"] = df["NAZWA"].apply(clean_text)

    df_trimmed["ADR"] = df_trimmed["KOD_POCZTOWY"] + " " + df_trimmed["MIEJSCOWOSC"] + " " + df_trimmed["ADRES"]

    return df_trimmed[["NAZWA", "REGON", "ADR", "URI"]]


def split_dataframe(dataframe):
    """Method"""

    dataframe["id"] = (dataframe["NAZWA"].astype(str) + dataframe["REGON"].astype(str) + dataframe["ADR"].astype(str)).astype('category').cat.codes
    df1 = dataframe[["id", "NAZWA", "REGON", "ADR"]].drop_duplicates(subset=["id"])
    df2 = dataframe[["id", "URI"]].drop_duplicates()

    return df1, df2


def mark_territorial_entities(dataframe):
    """Method"""

    def t(s: str):
        if re.search(pattern="(urząd gmin)|(urząd miasta)|(urząd miejski)|(gmina)|(miasto)", string=s, flags=re.I) and \
            not re.search(
                pattern="(sąd)|(prokurat)|(ośrodek)|(szkoła)|(zespół)|(związek)|(biuro)|(EC1)|(centrum usług)|(centrum opiek)|(instytucja)|(powiatow)|(urząd skarbowy)|(urząd pracy)|(zarząd)",
                string=s,
                flags=re.I):
            return 2
        else:
            return 1

    df = dataframe
    df["KATEGORIA"] = df["NAZWA"].apply(t)
    return df


def pick_main_electronic_address(dataframe):
    """Method"""

    def ranking(uri):
        r = [
            ("SkrytkaESP", 0),
            ("skrytka", 1),
            ("test", 999)
        ]
        for tup in r:
            if tup[0] in uri:
                return tup[1]
        return 998

    # choose main electronic address
    rnk = dataframe
    rnk["rank"] = rnk["URI"].apply(ranking)
    temp = rnk.groupby(["id"])["rank"].transform(min) == rnk["rank"]
    rnk = rnk[temp]
    rnk = rnk.drop_duplicates(subset=["id"])

    return rnk


def dataframe_to_tsv(dataframe):
    """Method"""
    return dataframe.to_csv(sep='\t', header=False, index=False, quoting=3)


def prepare_schema():
    """Method creates table 'skrytki' and stored procedure that performs the search."""

    sql = """
    CREATE EXTENSION IF NOT EXISTS pg_trgm;
    
    DROP TABLE IF EXISTS skrytki2;
    DROP TABLE IF EXISTS skrytki;
    DROP FUNCTION IF EXISTS search(text,text,boolean,integer); -- was needed for migration to new schema
    
    CREATE TABLE skrytki (
        id integer PRIMARY KEY,
        nazwa text,
        regon text,
        adres text,
        skrytka text,
        kategoria smallint
    );
    
    CREATE TABLE skrytki2 (
        id integer REFERENCES skrytki,
        skrytki text
    );
    
    CREATE INDEX idx_nazwa ON skrytki USING GIN (nazwa gin_trgm_ops);
    CREATE INDEX idx_regon ON skrytki (regon);
    CREATE INDEX idx_adres ON skrytki USING GIN (adres gin_trgm_ops);
    CREATE INDEX idx_kategoria ON skrytki (kategoria);
    CREATE INDEX idx_id ON skrytki2 (id);
    
    CREATE OR REPLACE FUNCTION public.search(IN raw_txt text, IN wildcards_txt text, IN tylko_urzedy boolean, IN max_records integer)
      RETURNS TABLE(nazwa text, regon text, adres text, skrytka text, id integer) AS
    $BODY$
      DECLARE
        i integer := 0;
      BEGIN
      
        IF tylko_urzedy THEN i := 1; END IF;
      
        RETURN QUERY
          -- szukaj REGON
          SELECT s.nazwa, s.regon, s.adres, s.skrytka, s.id
          FROM skrytki s
          WHERE s.regon = raw_txt AND s.kategoria > i;
    
        -- jeżeli nic nie znaleziono
        IF NOT FOUND THEN 
          RETURN QUERY
          -- szukaj po adresie lub nazwie (metoda LIKE)
          SELECT s.nazwa, s.regon, s.adres, s.skrytka, s.id
          FROM skrytki s
          WHERE (s.nazwa ilike wildcards_txt OR s.adres ilike wildcards_txt) AND s.kategoria > i
          ORDER BY greatest(similarity(s.nazwa, raw_txt), similarity(s.adres, raw_txt)) DESC
          LIMIT max_records;
        END IF;
    
         -- jeżeli nic nie znaleziono
        IF NOT FOUND THEN 
          RETURN QUERY
          -- szukaj po adresie lub nazwie (metoda SIMILARITY)
          SELECT s.nazwa, s.regon, s.adres, s.skrytka, s.id
          FROM skrytki s
          WHERE (s.nazwa % raw_txt OR s.adres % raw_txt) AND s.kategoria > i
          LIMIT max_records;
        END IF;
    
      END; 
    $BODY$
    LANGUAGE plpgsql;
    
    GRANT SELECT ON skrytki TO appacc;
    GRANT SELECT ON skrytki2 TO appacc;
    """

    with psycopg2.connect(environ["DB_STRING"]) as conn:
        cur = conn.cursor()
        cur.execute(sql)
        conn.commit()


def truncate_table(table_name: str):
    """Method truncates table."""

    with psycopg2.connect(environ["DB_STRING"]) as conn:
        cur = conn.cursor()
        cur.execute("TRUNCATE TABLE %s;", table_name)
        conn.commit()


if __name__ == '__main__':
    prepare_schema()

    cdata = clean_df(read_csv(environ["CSV_PATH"]))
    df1, df2 = split_dataframe(cdata)

    df1 = mark_territorial_entities(df1)
    df3 = pick_main_electronic_address(df2)
    df4 = pd.merge(left=df1, right=df3, on="id")[["id", "NAZWA", "REGON", "ADR", "URI", "KATEGORIA"]]
    df2 = df2[["id", "URI"]]

    load_into_db(dataframe_to_tsv(df4), dataframe_to_tsv(df2))
