import argparse
import csv
import json
import sys


def parse_args():
    parser = argparse.ArgumentParser(description="Audit CSV records")
    parser.add_argument("input_file", help="data.csv file to be audited")
    parser.add_argument(
        "--output",
        default="summary.json",
        help="Output JSON file"
    )
    parser.add_argument(
        "--group-by",
        default="department",
        help="Field to group valid records by"
    )
    args = parser.parse_args()
    print(f"Input file: {args.input_file}")
    return args


def read_records(filename, group_by=None):
    """
    Generator that yields CSV rows as dictionaries.
    Validates that the group-by field exists in the CSV header.
    """
    with open(filename, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)

        if group_by and group_by not in reader.fieldnames:
            raise ValueError(
                f"Group-by field '{group_by}' not found in CSV header: {reader.fieldnames}"
            )

        for row in reader:
            yield row


def validate_record(row):
    """
    Validates a single CSV row.
    Returns a list of error codes (empty if valid).
    """
    errors = []

    # ID validation
    if not row.get('id', '').strip().isdigit():
        errors.append('invalid_id')

    # Age validation
    age = row.get('age', '').strip()
    if not age:
        errors.append('missing_age')
    elif not age.isdigit():
        errors.append('invalid_age')

    # Department validation
    if not row.get('department', '').strip():
        errors.append('missing_department')

    return errors


def audit_records(records, group_by):
    """
    Processes all records and returns a summary dictionary.
    """
    total = 0
    valid_records = 0
    invalid_records = 0

    all_errors = []
    group_count = {}
    errors_count = {}

    for row in records:
        total += 1
        errors = validate_record(row)

        if errors:
            invalid_records += 1

            for error in errors:
                errors_count[error] = errors_count.get(error, 0) + 1

            all_errors.append({
                'id': row.get('id', '').strip(),
                'errors': errors
            })
        else:
            valid_records += 1
            group_value = row.get(group_by, '').strip()
            group_count[group_value] = group_count.get(group_value, 0) + 1

    return {
        'total_records': total,
        'valid_records': valid_records,
        'invalid_records': invalid_records,
        'invalid_records_detail': all_errors,
        'group_summary': group_count,
        'error_summary': errors_count
    }


def print_summary(summary, group_by):
    """
    Prints the audit summary to the terminal.
    """
    print("\nAudit Summary")
    print(f"Total records: {summary['total_records']}")
    print(f"Valid records: {summary['valid_records']}")
    print(f"Invalid records: {summary['invalid_records']}")

    print("\nInvalid Records")
    for error in summary['invalid_records_detail']:
        print(error)

    print(f"\nGroup Summary ({group_by})")
    for value, count in summary['group_summary'].items():
        print(f"{value}: {count}")

    print("\nValidation Error Summary")
    for error, count in summary['error_summary'].items():
        print(f"{error}: {count}")


def write_summary(summary, output_file):
    """
    Writes the summary dictionary to a JSON file.
    """
    with open(output_file, mode='w', encoding='utf-8') as file:
        json.dump(summary, file, indent=4)
    print(f"\nJSON report created: {output_file}")


def main():
    args = parse_args()

    try:
        records = read_records(args.input_file, args.group_by)
        summary = audit_records(records, args.group_by)
        print_summary(summary, args.group_by)
        write_summary(summary, args.output)

    except FileNotFoundError:
        print(f"Error: Input file '{args.input_file}' not found.", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except OSError as e:
        print(f"Error: Could not write output file '{args.output}': {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()