#!/usr/bin/env python3
import os
import csv
import argparse
from pathlib import Path


def extract_headers_from_folder(input_folder: Path, output_folder: Path) -> None:
    """
    Goes through all CSV files in `input_folder`, extracts the header row,
    and writes it to a new CSV file named X_headers.csv inside `output_folder`.
    """
    if not input_folder.is_dir():
        raise NotADirectoryError(f"{input_folder} is not a valid directory")

    # Create the output folder (e.g. "headers") if it doesn't exist
    output_folder.mkdir(parents=True, exist_ok=True)

    for file_path in input_folder.iterdir():
        # Process only CSV files
        if file_path.is_file() and file_path.suffix.lower() == ".csv":
            # Avoid re-processing header files if script is rerun
            if file_path.stem.endswith("_headers"):
                continue

            print(f"Processing: {file_path.name}")
            try:
                with file_path.open("r", encoding="utf-8-sig", newline="") as infile:
                    reader = csv.reader(infile)
                    header = next(reader, None)

                if header is None:
                    print(f"  -> Skipped (empty file or no header): {file_path.name}")
                    continue

                # Build output file path: X_headers.csv
                out_name = f"{file_path.stem}_headers.csv"
                out_path = output_folder / out_name

                with out_path.open("w", encoding="utf-8-sig", newline="") as outfile:
                    writer = csv.writer(outfile)
                    # Write the header row as a single row
                    writer.writerow(header)

                print(f"  -> Header saved to: {out_path}")

            except Exception as e:
                print(f"  -> Error processing {file_path.name}: {e}")


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Extract headers from all CSV files in a folder and save them as "
            "X_headers.csv in a 'headers' folder (or a custom output folder)."
        )
    )
    parser.add_argument(
        "input_folder",
        help="Path to the folder containing the CSV files."
    )
    parser.add_argument(
        "--output-folder",
        "-o",
        help="Folder where header CSVs will be saved (default: 'headers' inside input folder).",
        default=None,
    )

    args = parser.parse_args()

    input_folder = Path(args.input_folder).resolve()
    if args.output_folder is None:
        output_folder = input_folder / "headers"
    else:
        output_folder = Path(args.output_folder).resolve()

    extract_headers_from_folder(input_folder, output_folder)


if __name__ == "__main__":
    main()
