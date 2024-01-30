#!/usr/bin/env python
# coding: utf-8

import os
import pandas as pd
import argparse
from urllib.parse import urlparse
from time import time
from sqlalchemy import create_engine

parser = argparse.ArgumentParser(description="Ingest data from csv file into postgres DB.",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-s", "--chunk-size", default=100000, type=int, help="Number of lines to process at a time")
parser.add_argument("-t", "--table-name", default="yellow_taxi_tripdata", help="Table name")
parser.add_argument("DB_URL", help="Postgres URL in format: user:pw@host/dbname")
parser.add_argument("CSV_URL", help="URL to CSV file")
args = vars(parser.parse_args())

chunksize = args["chunk_size"]
table_name = args["table_name"]
csv_url = args["CSV_URL"]
db_url = args["DB_URL"]

# Extract filename from URL
csv_filename = urlparse(csv_url)
if csv_filename.scheme != 'file':
    # Remote download
    os.system(f"wget -c {csv_url} ")
    csv_filename = f'./{csv_filename.path.split("/")[-1]}'
    os.system(f"yes n | gzip -k -d {csv_filename}")
    csv_filename = csv_filename.replace(".gz","")
else:
    csv_filename = f'/{csv_filename.netloc+csv_filename.path}'

engine = create_engine(f'postgresql+psycopg2://{db_url}')

file_iter = pd.read_csv(csv_filename,
                        dtype={'store_and_fwd_flag': 'string'},
                        parse_dates=['tpep_pickup_datetime', 'tpep_dropoff_datetime'],
                        chunksize=chunksize)

total_time_start = time()
for df in file_iter:
    time_start = time()
    # df.tpep_pickup_datetime = pd.to_datetime(df.tpep_pickup_datetime)
    # df.tpep_dropoff_datetime = pd.to_datetime(df.tpep_dropoff_datetime)
    df.to_sql(name=table_name, con=engine, if_exists='append')
    print(f'A chunk has been inserted. Took {time() - time_start}')
print(f'Total time: {time() - total_time_start}')
os.system(f'wc -l {csv_filename}')
