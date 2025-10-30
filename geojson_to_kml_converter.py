import argparse
import os

import geopandas as gpd


def convert_geojson_to_kml(input_file, output_file):
    """
    Converts a GeoJSON file to a KML file.
    """
    try:
        # Read the GeoJSON file
        print(f"Reading GeoJSON file: {input_file}")
        gdf = gpd.read_file(input_file)

        # Reproject to WGS84 (EPSG:4326), which is standard for KML
        print("Reprojecting to WGS84 (EPSG:4326)...")
        gdf = gdf.to_crs("EPSG:4326")

        # Enable KML driver
        gpd.io.file.fiona.drvsupport.supported_drivers["KML"] = "rw"

        # Write to KML file
        print(f"Writing KML file to: {output_file}")
        gdf.to_file(output_file, driver="KML")

        print(f"Successfully converted {input_file} to {output_file}")

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert a GeoJSON file to KML.")
    parser.add_argument(
        "input_file", type=str, help="The path to the input GeoJSON file."
    )

    args = parser.parse_args()

    input_path = args.input_file

    # Create an output filename by replacing the extension
    output_path = os.path.splitext(input_path)[0] + ".kml"

    convert_geojson_to_kml(input_path, output_path)
