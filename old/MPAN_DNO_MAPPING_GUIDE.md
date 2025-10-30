# MPAN to DNO Mapping: Implementation Guide

This guide explains how to use the `mpan_dno_mapper.py` script to identify Distribution Network Operators (DNOs) from MPANs in your data, and how to integrate this information with your existing DNO DUoS data.

## Overview

The `mpan_dno_mapper.py` script implements the industry-standard approach for identifying DNOs from MPANs (Meter Point Administration Numbers), using the first two digits of the MPAN core (the Distributor ID).

The script:
1. Parses and validates MPANs according to official UK electricity industry standards
2. Extracts the Distributor ID (first 2 digits of the MPAN core)
3. Maps the Distributor ID to the corresponding DNO
4. Enriches CSV files with DNO information
5. Can optionally merge with your existing DUoS data

## MPAN Structure and Distributor ID

An MPAN in Great Britain is a 21-digit number, often displayed over two lines:

```
S    01     123     456     789
1234 5678 9012 3
```

The bottom line (13 digits) is called the **MPAN core** and includes:
1. **Distributor ID** — the first 2 digits of the core MPAN
2. A unique identifier (digits 3-10)
3. A check digit (digit 13)

The Distributor ID is what we use to map to DNOs.

## Check Digit Validation

The script validates the MPAN using the industry-standard check digit algorithm:

1. Take the first 12 digits of the MPAN core
2. Multiply each digit by the corresponding prime number from the sequence: [3, 5, 7, 13, 17, 19, 23, 29, 31, 37, 41, 43]
3. Sum the products
4. Take (sum mod 11) mod 10
5. The result should equal the 13th digit of the MPAN core

## DNO Lookup Table

The script includes a comprehensive DNO lookup table mapping Distributor IDs to DNO information:

| Distributor ID | DNO Key     | DNO Name                         | Short Code | Market Participant ID | GSP Group ID | GSP Group Name        |
|----------------|-------------|----------------------------------|------------|----------------------|--------------|----------------------|
| 10             | UKPN-EPN    | UK Power Networks (Eastern)      | EPN        | EELC                 | A            | Eastern              |
| 12             | UKPN-LPN    | UK Power Networks (London)       | LPN        | LOND                 | C            | London               |
| 19             | UKPN-SPN    | UK Power Networks (South Eastern)| SPN        | SEEB                 | J            | South Eastern        |
| 16             | ENWL        | Electricity North West           | ENWL       | NORW                 | G            | North West           |
| 15             | NPg-NE      | Northern Powergrid (North East)  | NE         | NEEB                 | F            | North East           |
| 23             | NPg-Y       | Northern Powergrid (Yorkshire)   | Y          | YELG                 | M            | Yorkshire            |
| ...            | ...         | ...                              | ...        | ...                  | ...          | ...                  |

## Usage

### Basic Usage

To process a CSV file containing MPANs and add DNO information:

```bash
python mpan_dno_mapper.py input.csv output_enriched.csv --mpan-column "MPAN"
```

Where:
- `input.csv` is your CSV file containing MPANs
- `output_enriched.csv` is where the enriched data will be written
- `--mpan-column` specifies the column containing MPANs (default: "MPAN")

### Merging with DUoS Data

To process MPANs and merge with your DNO DUoS data:

```bash
python mpan_dno_mapper.py input.csv output_enriched.csv --mpan-column "MPAN" --duos-file duos_outputs2/gsheets_csv/DNO_Reference_20250914_195528.csv
```

This will:
1. Process the MPANs in `input.csv`
2. Create an enriched file at `output_enriched.csv`
3. Merge this with the DUoS data from the specified file
4. Save the merged result as `output_enriched_with_duos.csv`

### Running Tests

To run test examples:

```bash
python mpan_dno_mapper.py --test
```

## Output Columns

The enriched CSV will include all original columns plus:

- `mpan_core`: The cleaned 13-digit MPAN core
- `distributor_id`: The 2-digit Distributor ID
- `mpan_valid`: Whether the MPAN is valid (True/False)
- `DNO_Key`: The DNO key (e.g., "UKPN-LPN")
- `DNO_Name`: The full DNO name
- `Short_Code`: The short code for the DNO
- `Market_Participant_ID`: The market participant ID
- `GSP_Group_ID`: The Grid Supply Point Group ID
- `GSP_Group_Name`: The Grid Supply Point Group name

## Integration with Your DUoS Data

The script can integrate with your existing DNO DUoS data in several ways:

1. **Direct Merge**: Use the `--duos-file` option to merge MPAN data with DUoS data based on DNO_Key
2. **Manual Merge**: Process your MPAN data separately and use other tools to join with DUoS data
3. **Enriched Analysis**: Use the enriched MPAN data to analyze patterns by DNO, region, etc.

## Example Workflow

1. **Identify Source Data**: Locate CSV files containing MPANs that need DNO identification
2. **Process with Script**: Run the script to extract DNO information
3. **Merge with DUoS**: Use the script to merge with your existing DUoS data
4. **Upload to Google Sheets**: Use your existing scripts to upload the enriched data to Google Sheets

## Common Issues and Solutions

### Missing or Malformed MPANs

If your data contains missing or malformed MPANs:
- The script will set `mpan_valid` to False
- The `distributor_id` will be None or incomplete
- The DNO fields will be None or marked as "UNKNOWN"

### Unknown Distributor IDs

If a Distributor ID is not in the lookup table:
- The script will set `DNO_Key` to "UNKNOWN"
- Consider adding the missing ID to the lookup table if it's a valid UK Distributor ID

### Performance with Large Files

For very large files:
- The script uses Pandas for efficient processing
- Consider processing in batches if memory is an issue

## References

1. Elexon "MSID and MPAN Guidance": Defines the MPAN structure and Distributor ID
2. EDF Energy: Confirms that the first two digits of the MPAN core identify the DNO
3. DCUSA / BSCP: Define roles, line loss classes, and meter time switch codes

## Next Steps

Consider extending the script to:
1. Handle specific edge cases in your data
2. Add more detailed validation or reporting
3. Integrate more deeply with your DUoS analysis workflow

For any questions or issues, refer to the comments in the script or the official MPAN documentation.
