import zipfile
import os
import requests
from glob import glob
from datetime import datetime, date
from typing import Tuple

from tqdm import tqdm
import pandas as pd
import numpy as np
from constants import constants

# get quarter and year for today
def get_quarter_and_year() -> Tuple[int, int]:
    """ Get quarter and year for today """

    today = date.today()
    year = today.year
    month = today.month
    quarter = (month - 1) // 3 + 1
    return quarter, year


def get_url_from_template(year: int, quarter: int) -> str:
    """Return the url for the PNAD microdata file for a given year and month.

    Args:
        url (str): url template
        year (int): year
        month (int): month

    Returns:
        str: url
    """
    today = date.today().strftime("%Y%m%d")
    template = constants.URL_PREFIX.value + "/{year}/PNADC_0{quarter}{year}_{today}.zip"
    return template.format(year=year, quarter=quarter, today=today)


def download_txt(url, chunk_size=128, mkdir=False) -> str:
    """
    Gets all csv files from a url and saves them to a directory.
    """
    if mkdir:
        os.system("mkdir -p /tmp/data/input/")

    request_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36",
    }
    r = requests.get(url, headers=request_headers, stream=True, timeout=10)
    save_path = "/tmp/data/"
    save_path = save_path + url.split("/")[-1]
    with open(save_path, "wb") as fd:
        for chunk in tqdm(r.iter_content(chunk_size=chunk_size)):
            fd.write(chunk)

    with zipfile.ZipFile(save_path) as z:
        z.extractall("/tmp/data/input")
    os.system('cd /tmp/data/input; find . -type f ! -iname "*.txt" -delete')
    filepath = glob("/tmp/data/input/*.txt")[0]

    return filepath


def build_partitions(filepath: str) -> str:
    """
    Build partitions from a given file.
    """

    os.system("mkdir -p /tmp/data/output/")
    # read file
    df = pd.read_fwf(
        filepath,
        widths=constants.COLUMNS_WIDTHS.value,
        names=constants.COLUMNS_NAMES.value,
        header=None,
        encoding="latin-1",
        nrows=1000,
        dtype=str,
    )

    # partition by year, quarter and region
    trimestre = df["Trimestre"].unique()[0]
    ano = df["Ano"].unique()[0]
    df.rename(
        columns={
            "UF": "id_uf",
            "Estrato": "id_estrato",
            "UPA": "id_upa",
            "Capital": "capital",
            "RM_RIDE": "rm_ride",
            "Trimestre": "trimestre",
            "Ano": "ano",
        },
        inplace=True,
    )
    df["sigla_uf"] = df["id_uf"].map(constants.map_codigo_sigla_uf.value)
    df["id_domicilio"] = df["id_estrato"] + df["V1008"] + df["V1014"]

    ordered_columns = constants.COLUMNS_ORDER.value

    # # reorder columns to match schema
    # print(ordered_columns)
    df["habitual"] = [np.nan] * len(df)
    df["efetivo"] = [np.nan] * len(df)
    df = df[ordered_columns]

    df.drop(columns=["trimestre", "ano"], inplace=True)

    print(df.head())

    for uf in ufs:
        df_uf = df[df['sigla_uf']==uf]
        df_uf.drop(columns=['sigla_uf'], inplace=True)
        os.system("mkdir -p /tmp/data/output/ano={ano}/trimestre={trimestre}/sigla_uf={uf}".format(ano=ano, trimestre=trimestre, uf=uf))
        df_uf.to_csv(f'/tmp/data/output/ano={ano}/trimestre={trimestre}/sigla_uf={uf}/microdados.csv', index=False)

    return '/tmp/data/output/'


def main():
    # parameters
    year = 2021
    quarter = 4
    url = get_url_from_template(year, 4)
    input_file = download_txt(url, mkdir=True)
    output_path = build_partitions(input_file)

    print(os.system("tree /tmp/data/output/"))


if __name__ == "__main__":
    main()
