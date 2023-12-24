import argparse
import os
import sys
import csv
import sqlite3
import logging
import pathlib


here = pathlib.Path(__file__).resolve().parent
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler(sys.stderr)
stream_handler.setLevel(logging.DEBUG)
log.handlers.clear()
log.addHandler(stream_handler)


DEFAULT_DATABASE_PATH = 'instance_type_offerings.db'
DESCRIPTION_IMPORT_SUBCOMMAND = """If -k or --skip-header is specified, the first line of the source file is skipped.
In this case, the header line must be specified as follows:
  instance_type: InstanceType, LocationType, Location
  az           : ZoneId, ZoneName, RegionName, ZoneType, State
"""


def validate_row_shapes(rows: list) -> None | ValueError:
    """check if all rows have the same keys
    """
    keys = set(rows[0].keys())
    for row in rows[1:]:
        if keys != set(row.keys()):
            return ValueError('All rows must have the same keys')
    return None


def db_conn(database_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(here.joinpath(database_path))
    return conn


def db_init(database_path: str):
    conn = db_conn(database_path)
    cursor = conn.cursor()
    # create az table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS az (
            ZoneId TEXT NOT NULL PRIMARY KEY,
            ZoneName TEXT NOT NULL,
            RegionName TEXT NOT NULL,
            ZoneType TEXT NOT NULL,
            State TEXT NOT NULL
        );
    ''')
    # create instance_type_offerings table
    # pk on instance_type_offerings (Location, InstanceType)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS instance_type_offerings (
            InstanceType TEXT NOT NULL,
            LocationType TEXT NOT NULL,
            Location TEXT NOT NULL,
            PRIMARY KEY (Location, InstanceType)
        );
    ''')
    # cursor.execute('''
    #     CREATE INDEX IF NOT EXISTS idx_LocationType ON instance_type (LocationType);
    # ''')
    conn.commit()
    conn.close()
    log.debug(f'Initialized database: {database_path}')


def db_import_instance_type_offerings(
    database_path: str,
    source_file: str,
    with_no_header: bool,
    source_fmt: str,
):
    if not here.joinpath(source_file).exists():
        log.error(f'File not found: {source_file}')
        exit(1)

    rows = []
    with open(source_file, 'r') as f:
        args = {}
        if source_fmt == 'tsv':
            args['delimiter'] = '\t'

        if with_no_header:
            # assume column names are as follows:
            #   InstanceType, LocationType, Location
            reader = csv.reader(f, **args)
            for row in reader:
                rows.append({
                    'InstanceType': row[0],
                    'LocationType': row[1],
                    'Location': row[2],
                })
        else:
            reader = csv.DictReader(f, **args)
            rows = [row for row in reader]

    err = validate_row_shapes(rows)
    if err is not None:
        log.error('invalid row shapes. consider appropriate using -k option or check the source file')
        exit(1)

    conn = db_conn(database_path)
    cursor = conn.cursor()
    rows_to_insert = [
        (row['InstanceType'], row['LocationType'], row['Location'])
        for row in rows
    ]
    cursor.executemany('''
        INSERT INTO instance_type_offerings (InstanceType, LocationType, Location)
        VALUES (?, ?, ?)
    ''', rows_to_insert)
    conn.commit()
    conn.close()
    log.debug(f'Inserted {len(rows_to_insert)} rows')


def db_import_az(
    database_path: str,
    source_file: str,
    with_no_header: str,
    source_fmt: str,
):
    if not here.joinpath(source_file).exists():
        log.error(f'File not found: {source_file}')
        exit(1)

    rows = []
    with open(source_file, 'r') as f:
        args = {}
        if source_fmt == 'tsv':
            args['delimiter'] = '\t'

        if with_no_header:
            # assume column names are as follows:
            #   ZoneId, ZoneName, RegionName, ZoneType, State
            reader = csv.reader(f, **args)
            for row in reader:
                rows.append({
                    'ZoneId': row[0],
                    'ZoneName': row[1],
                    'RegionName': row[2],
                    'ZoneType': row[3],
                    'State': row[4],
                })
        else:
            reader = csv.DictReader(f, **args)
            rows = [row for row in reader]

    err = validate_row_shapes(rows)
    if err is not None:
        log.error('invalid row shapes. consider appropriate using -k option or check the source file')
        exit(1)

    conn = db_conn(database_path)
    cursor = conn.cursor()
    rows_to_insert = [
        (row['ZoneId'], row['ZoneName'], row['RegionName'], row['ZoneType'], row['State'])
        for row in rows
    ]
    cursor.executemany('''
        INSERT INTO az (ZoneId, ZoneName, RegionName, ZoneType, State)
        VALUES (?, ?, ?, ?, ?)
    ''', rows_to_insert)
    conn.commit()
    conn.close()
    log.debug(f'Inserted {len(rows_to_insert)} rows')


def main():
    parser = argparse.ArgumentParser(description='A tool to manage the database')
    subparsers = parser.add_subparsers(dest='subcommand')

    # subparser for init subcommand
    init_parser = subparsers.add_parser('init', help='initialize the database')
    init_parser.add_argument(
        '-d', '--database',
        default=DEFAULT_DATABASE_PATH,
        help=f'path to the database (default: {DEFAULT_DATABASE_PATH})',
    )

    # subparser for import subcommand
    import_parser = subparsers.add_parser(
        'import',
        # help='import data to the database',
        description=DESCRIPTION_IMPORT_SUBCOMMAND,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    import_parser.add_argument(
        '-d', '--database',
        dest='database',
        default=DEFAULT_DATABASE_PATH,
        help=f'path to the database (default: {DEFAULT_DATABASE_PATH})',
    )
    import_parser.add_argument(
        '-t', '--table',
        dest='table',
        choices=['instance_type_offerings', 'az'],
        help='table name',
    )
    import_parser.add_argument(
        '-f', '--source-file',
        dest='source_file',
        required=True,
        help='source file',
    )
    import_parser.add_argument(
        '-k', '--with-no-header',
        dest='with_no_header',
        action='store_true',
        help='either source file has a header line (at first line) or not',
    )
    import_parser.add_argument(
        '--fmt', '--format',
        dest='source_fmt',
        default='tsv',
        choices=['tsv', 'csv'],
        help='format of the source file (default: tsv)',
    )

    args = parser.parse_args()

    if args.subcommand == 'init':
        db_init(database_path=args.database)
    elif args.subcommand == 'import':
        if args.table == 'instance_type_offerings':
            db_import_instance_type_offerings(
                database_path=args.database,
                source_file=args.source_file,
                with_no_header=args.with_no_header,
                source_fmt=args.source_fmt,
            )
        elif args.table == 'az':
            db_import_az(
                database_path=args.database,
                source_file=args.source_file,
                with_no_header=args.with_no_header,
                source_fmt=args.source_fmt,
            )
        else:
            raise ValueError(f'Invalid table name: {args.table}')


if __name__ == '__main__':
    main()
