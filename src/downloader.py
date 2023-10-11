import glob
import os
import subprocess

import pandas as pd

from code.Z_playground.directories import Path
from src.logger import Logger


class DataDownloader(Logger):
    def __init__(self, debug=False, write=False):
        super().__init__(debug, write)
        self._raw_data = None
        self._validated_csv = None

    def download_data(self, script_path="src/download.sh"):
        try:
            output = subprocess.check_output(
                ["bash", script_path], stderr=subprocess.STDOUT, universal_newlines=True
            )
            self.log("info", "Downloaded data successfully.")
            self.log("debug", output)
        except subprocess.CalledProcessError as e:
            self.log("error", f"Error running the shell script: {e}")

    def start(self):
        if not glob.glob(
            os.path.join("data", "coronavirus-covid-19-pandemic-usa-counties.csv")
        ):
            self.log("info", "Data not found. Downloading data...")
            self.download_data()

        self.log("info", f"Validating {self.raw_data}...")

        if not glob.glob(os.path.join("data", "validated.csv")):
            status, df = self.create_validated_csv()

            if status == "pass" and df is not None:
                prompt = (
                    f"Data was read successfully from {self.raw_data}\n---\n{df.head()}"
                )
                self.log("info", prompt)
            else:
                self.log("error", "Error while validating data.")
        else:
            self.log("info", "Validated data found. Skipping validation.")

    def validate(self):
        """
        What's change:
        - Drop the column 'Admin 2 FIPS Code' because it is not needed for the model

        :return: Dataframe that has been validated
        """
        self.log("info", "Validating data...")
        df = pd.read_csv(self.raw_data, sep=";")
        df.drop("Admin 2 FIPS Code", axis=1, inplace=True)

        missing_rows = df[df.isnull().any(axis=1)]
        self.log("info", f"Number of rows with missing values: {len(missing_rows)}")
        self.log("debug", f"Sample null:--\n---\n {df.isnull().sum()} \n---\n")

        return df

    def create_validated_csv(self):
        """
        What's change:
        - This will create a new csv file that has been validated
        and drop the column 'Admin 2 FIPS Code' and also change the seperator from ';' to ','.
        """
        self.log("info", "Creating validated CSV...")
        try:
            df = self.validate()
            df.to_csv(self.validated_csv, index=False)
            self.log("info", "Validated CSV created successfully.")
            return "pass", df
        except FileNotFoundError as e:
            self.log("error", f"Error while creating validated CSV: {e}")
            return e, None

    @property
    def validated_csv(self):
        return Path.DATA.value + "/validated.csv"

    @property
    def raw_data(self):
        return Path.DATA.value + "/coronavirus-covid-19-pandemic-usa-counties.csv"

    @validated_csv.setter
    def validated_csv(self, value):
        self._validated_csv = value

    @raw_data.setter
    def raw_data(self, value):
        self._raw_data = value
