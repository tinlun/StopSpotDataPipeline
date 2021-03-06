import sys
import argparse
from datetime import datetime
from ..ios import ios


class ArgInterface:

    def query_with_args(self, client, args):
        ctran = client.ctran
        flagged = client.flagged
        try:
            args = self._parse_cl_args(args)

            if args.flag:
                query = args.flag
                args.flag = client.lookup_flag_id(query)

                if args.flag is None:
                    ios.log_and_print(
                            "No flag by the name of \"{}\" exists in the database.".format(query),
                            ios.Severity.ERROR
                    )
                    ios.print("Available Flags:")
                    client.print_flag_names()
                    return None

                args.flag = args.flag.id

            if args.select:
                df = self._handle_flag_query(flagged, args)
            elif args.date_start:
                df = self._handle_range_query(client, args)
            elif args.daily:
                client.process_next_day(restart=True)
                return None
            else:
                ios.print("Insufficient arguments.")
                return None
        except ValueError:
            raise SystemExit(2)
        return df

    def _parse_cl_args(self, args):
        parser = self._create_parser(args)
        return parser.parse_args(args)

    def _handle_range_query(self, client, args):
        return client.process_data(args.date_start, args.date_end)

    def _handle_flag_query(self, flagged, args):
        if args.flag:
            limit = args.limit if args.limit else 100
            return flagged.query_by_flag_id(args.flag, limit)
        elif args.row:
            return flagged.query_by_row_id("service_periods", args.row, args.year, args.service_period)

    def _service_date(self, arg):
        try:
            return datetime.strptime(arg, "%Y-%m-%d")
        except ValueError:
            err_msg = "Invalid service date format: {0}, YYYY-MM-DD expected.".format(arg)
            ios.log_and_print(err_msg, ios.Severity.ERROR)
            raise argparse.ArgumentTypeError(err_msg)

    def _service_year(self, arg):
        try:
            return datetime.strptime(arg, "%Y")
        except ValueError:
            err_msg = "Invalid service year format: {0}, YYYY expected.".format(arg)
            ios.log_and_print(err_msg, ios.Severity.ERROR)
            raise argparse.ArgumentTypeError(err_msg)

    def _service_period(self, arg):
        try:
            try:
                p = int(arg)
                if p in [1, 2, 3]:
                    return p
                else:
                    raise ValueError
            except ValueError as e:
                names = ["first", "second", "third"]
                if arg in names:
                    return names.index(arg) + 1
                else:
                    raise e
        except ValueError:
            err_msg = "Invalid service period format: {0}, [1, 2, 3] or [first, second, third] expected.".format(arg)
            ios.log_and_print(err_msg, ios.Severity.ERROR)
            raise argparse.ArgumentTypeError(err_msg)

    def _limit(self, arg):
        try:
            lim = int(arg)
            if lim > 0:
                return lim
            else:
                raise ValueError
        except ValueError:
            err_msg = "Invalid limit: {0}, value must be at least 1.".format(arg)
            ios.log_and_print(err_msg, ios.Severity.ERROR)
            raise argparse.ArgumentTypeError(err_msg)

    def _create_parser(self, args):
        if args is None:
            raise SystemExit(2)

        parser = argparse.ArgumentParser()
        daily = self._is_present(args, None, "--daily")
        query = self._is_present(args, "-s", "--select")
        flag = self._is_present(args, "-f", "--flag")
        row = self._is_present(args, "-r", "--row_id")
        parser.add_argument("--daily",
                            help="Process data of the next unprocessed day. No arguments. This will restart on failure.",
                            required=self._is_present(args, None, "--daily") and len(args) == 1,
                            action="store_true")
        parser.add_argument("--date-start",
                            help="Format: --date-start=YYYY-MM-DD (ex. 2020-01-01)",
                            required=not daily and not query and self._is_present(args, None, "--date-end"),
                            type=self._service_date)
        parser.add_argument("--date-end",
                            help="Format: --date-end=YYYY-MM-DD (ex. 2020-01-01)",
                            required=not daily and not query and self._is_present(args, None, "--date-start"),
                            type=self._service_date)
        parser.add_argument("-s",
                            "--select",
                            help="Switch to activate handling of flag querying for utilizing --flag and --row.",
                            required=flag or row,
                            action="store_true")
        parser.add_argument("-f",
                            "--flag",
                            help="Specify the name of the flag you wish to query rows for.",
                            required=not daily and query and not row)
        parser.add_argument("-l",
                            "--limit",
                            help="Sets the number of rows to be returned (default=100).",
                            required=False,
                            type=self._limit)
        parser.add_argument("-r",
                            "--row",
                            help="Specify the row_id of the row you wish to query flags for.",
                            required=not daily and query and not flag,
                            type=int)
        parser.add_argument("-y",
                            "--year",
                            help="Specify the service year of the row you wish to query flags for.",
                            required=not daily and query and row and not flag,
                            type=self._service_year)
        parser.add_argument("-p",
                            "--service-period",
                            help="Specify the service period of the row you wish to query flags for.",
                            required=not daily and query and row and not flag,
                            type=self._service_period)
        return parser

    def _is_present(self, args, short, long):
        if short is None:
            return any(s.startswith(long) for s in args)
        else:
            return any(s.startswith(short) or s.startswith(long) for s in args)
