import json

from shapely.geometry import shape
from shapely.ops import unary_union


# Load GeoJSON files
def load_geojson(file_path):
    with open(file_path, "r") as f:
        return json.load(f)


def save_geojson(data, file_path):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)


def compare_and_merge_features(base_file, compare_files, output_file):
    base_data = load_geojson(base_file)
    base_features = base_data["features"]

    for compare_file in compare_files:
        compare_data = load_geojson(compare_file)
        compare_features = compare_data["features"]

        for compare_feature in compare_features:
            compare_geom = shape(compare_feature["geometry"])
            duplicate_found = False

            for base_feature in base_features:
                base_geom = shape(base_feature["geometry"])

                # Check for overlapping geometries
                if base_geom.equals(compare_geom):
                    duplicate_found = True
                    break

            if not duplicate_found:
                base_features.append(compare_feature)

    # Save the merged GeoJSON
    base_data["features"] = base_features
    save_geojson(base_data, output_file)


if __name__ == "__main__":
    base_geojson = "system_regulatory/gis/tnuosgenzones_geojs.geojson"
    compare_geojsons = [
        "system_regulatory/gis/dno_license_areas_20200506.geojson",
        "system_regulatory/gis/gsp_regions_20181031.geojson",
        "system_regulatory/gis/gb-dno-license-areas-20240503-as-geojson.geojson",
    ]
    output_geojson = "system_regulatory/gis/merged_geojson.geojson"

    compare_and_merge_features(base_geojson, compare_geojsons, output_geojson)
    print(f"Merged GeoJSON saved to {output_geojson}")
