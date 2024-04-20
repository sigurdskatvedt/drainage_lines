from qgis.analysis import QgsNativeAlgorithms
from qgis import processing
from processing.tools import dataobjects
import csv
import os
from processing.core.Processing import Processing
import sys
import cProfile
import pstats

from qgis.core import QgsApplication, QgsVectorLayer, QgsProject, QgsVectorFileWriter, QgsProcessingFeedback, QgsFeatureRequest, QgsFeature

# Initialize the QGIS Application
qgs = QgsApplication([], False)
qgs.initQgis()

# Initialize QGIS and Processing framework
Processing.initialize()
feedback = QgsProcessingFeedback()


def save_algos_to_csv():
    algos = []  # Store algorithm details
    print(qgs.processingRegistry().algorithms())

    for alg in qgs.processingRegistry().algorithms():
        algos.append([alg.id(), alg.displayName()])

    # Save to CSV file
    with open('algos.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Algorithm ID', 'Display Name'])  # Header row
        writer.writerows(algos)


def find_touching_polygons(primary_layer, touching_layer):
    """
    Finds all polygons in the primary layer that touch another layer
    and returns the result as a new QgsVectorLayer with the original geometries from the primary layer.

    Args:
        primary_layer (QgsVectorLayer): The primary layer containing polygons.
        touching_layer (QgsVectorLayer): The touching layer containing polygons.

    Returns:
        QgsVectorLayer: A new layer containing the original polygons that touch the input polygons.
    """
    # Define the parameters for the spatial join
    params = {
        'INPUT': primary_layer,
        'JOIN': touching_layer,
        'PREDICATE': [0],  # 6 corresponds to 'touches'
        # 1 means take attributes of the first matching feature only (not creating duplicates)
        'METHOD': 1,
        'DISCARD_NONMATCHING': True,  # Only include matching features
        'PREFIX': '',
        'OUTPUT': 'memory:'
    }

    result = processing.run(
        "native:joinattributesbylocation", params, feedback=feedback)

    # The result['OUTPUT'] is a temporary layer
    joined_layer = result['OUTPUT']

    if joined_layer:
        print("Join by location completed successfully. Result is stored in a temporary layer.")
        return joined_layer
    else:
        print("Error during join by location operation.")
        return None

def clip_and_mosaic_rasters(raster_folder, vector_layer, clipped_rasters_folder, mosaic_output_path):
    """
    Clips all raster layers in a folder by a vector layer and creates a mosaic of the clipped rasters.

    Args:
        raster_folder (str): Path to the folder containing raster files.
        vector_layer_path (str): Path to the vector layer used as the mask for clipping.
        clipped_rasters_folder (str): Folder where clipped rasters will be saved.
        mosaic_output_path (str): Path for the output mosaic raster.
    """
    if not vector_layer.isValid():
        print("Error loading vector layer.")
        return

    # Ensure the output directory exists
    os.makedirs(clipped_rasters_folder, exist_ok=True)

    clipped_rasters = []

    # Iterate through each raster file in the folder
    for filename in os.listdir(raster_folder):
        if filename.endswith(('.tif', '.tiff', '.TIF', '.TIFF')):  # Check for TIFF files, adjust if necessary
            print(f'Clipping: {filename}')
            raster_path = os.path.join(raster_folder, filename)
            output_path = os.path.join(clipped_rasters_folder, f"clipped_{filename}")
            clipped_rasters.append(output_path)

            # Clip the raster
            clip_raster_by_vector(raster_path, vector_layer, output_path)

    # Create a mosaic from the clipped rasters
    params = {
        'INPUT': ';'.join(clipped_rasters),
        'OUTPUT': mosaic_output_path
    }

    processing.run("gdal:merge", params, feedback=feedback)
    print(f"Mosaic created successfully. Output saved to: {mosaic_output_path}")

def clip_raster_by_vector(raster_path, vector_layer, output_path):
    """
    Clips a raster layer by a vector layer.

    Args:
        raster_path (str): Path to the raster file to be clipped.
        vector_layer (QgsVectorLayer): The vector layer used as the mask for clipping.
        output_path (str): The file path for the output clipped raster.
    """
    params = {
        'INPUT': raster_path,
        'MASK': vector_layer,
        'NODATA': None,
        'CROP_TO_CUTLINE': True,
        'KEEP_RESOLUTION': True,
        'OPTIONS': 'COMPRESS=LZW',  # Add compression option here
        'OUTPUT': output_path
    }

    result = processing.run("gdal:cliprasterbymasklayer", params, feedback=feedback)

    if result and os.path.exists(output_path):
        print("Raster clipped successfully. Output saved to:", output_path)
    else:
        print("Error during raster clipping operation.")

def create_mosaic(raster_files, mosaic_output_path):
    """
    Creates a mosaic from a list of raster files.

    Args:
        raster_files (list): A list of paths to raster files to be merged.
        mosaic_output_path (str): The file path for the output mosaic raster.
    """
    params = {
        'INPUT': ';'.join(raster_files),
        'OUTPUT': mosaic_output_path,
        'OPTIONS': 'COMPRESS=LZW'  # Use compression for the output mosaic
    }

    result = processing.run("gdal:merge", params, feedback=feedback)

    if result and os.path.exists(mosaic_output_path):
        print("Mosaic created successfully. Output saved to:", mosaic_output_path)
    else:
        print("Error during mosaic creation.")

def clip_mosaic_by_vector(mosaic, vector_layer_path, clipped_output_path):
    """
    Clips a mosaic raster by a vector layer.

    Args:
        mosaic_path (str): Path to the mosaic raster to be clipped.
        vector_layer_path (str): Path to the vector layer used as the mask for clipping.
        clipped_output_path (str): The file path for the output clipped raster.
    """
    vector_layer = QgsVectorLayer(vector_layer_path, "vector_mask", "ogr")
    if not vector_layer.isValid():
        print("Error loading vector layer.")
        return

    params = {
        'INPUT': mosaic,
        'MASK': vector_layer,
        'NODATA': None,
        'CROP_TO_CUTLINE': True,
        'KEEP_RESOLUTION': True,
        'OPTIONS': 'COMPRESS=LZW',  # Add compression option here
        'OUTPUT': clipped_output_path
    }

    result = processing.run("gdal:cliprasterbymasklayer", params, feedback=feedback)

    if result and os.path.exists(clipped_output_path):
        print("Mosaic clipped successfully. Output saved to:", clipped_output_path)
    else:
        print("Error during mosaic clipping operation.")


def dissolve_layer(input_layer, dissolve_field=None):
    """
    Dissolves features in a given layer, optionally based on a specific attribute.

    Args:
        input_layer (QgsVectorLayer): The layer to be dissolved.
        dissolve_field (str, optional): The attribute field based on which features will be dissolved. If None, all features are dissolved into a single feature.

    Returns:
        QgsVectorLayer: A new layer with dissolved features.
    """
    # Define the parameters for the dissolve operation
    params = {
        'INPUT': input_layer,
        'FIELD': dissolve_field,
        'OUTPUT': 'memory:'
    }

    result = processing.run("native:dissolve", params, feedback=feedback)

    # The result['OUTPUT'] is a temporary layer
    dissolved_layer = result['OUTPUT']

    if dissolved_layer:
        print("Dissolve operation completed successfully.")
        return dissolved_layer
    else:
        print("Error during dissolve operation.")
        return None


def layer_difference(input_layer, overlay_layer):
    """
    Removes geometries or a selection of geometries from one layer from another layer.

    Args:
        input_layer (QgsVectorLayer): The layer from which geometries will be removed.
        overlay_layer (QgsVectorLayer): The layer containing geometries to be removed from the input layer.

    Returns:
        QgsVectorLayer: A new layer containing the result of the removal.
    """
    # Define the parameters for the difference operation
    params = {
        'INPUT': input_layer,
        'OVERLAY': overlay_layer,
        'OUTPUT': 'memory:'
    }

    result = processing.run("native:difference", params, feedback=feedback)

    # The result['OUTPUT'] is a temporary layer
    difference_layer = result['OUTPUT']

    if difference_layer:
        print("Difference operation completed successfully. Result is stored in a temporary layer.")
        return difference_layer
    else:
        print("Error during difference operation.")
        return None


def create_layer_from_area_threshold(input_layer, area_threshold):
    """
    Creates a new layer from polygons in the input layer that are over a certain area threshold.

    Args:
        input_layer (QgsVectorLayer): The input layer containing polygons.
        area_threshold (float): The minimum area threshold for polygons to be included in the new layer.

    Returns:
        QgsVectorLayer: A new memory layer containing only the polygons that meet or exceed the area threshold.
    """
    # Create a new memory layer with the same CRS and fields as the input layer
    crs = input_layer.crs().toWkt()
    fields = input_layer.fields()
    output_layer = QgsVectorLayer(
        f"Polygon?crs={crs}", "FilteredPolygons", "memory")
    output_layer_data_provider = output_layer.dataProvider()
    output_layer_data_provider.addAttributes(fields)
    output_layer.updateFields()

    # Iterate through each feature in the input layer
    for feature in input_layer.getFeatures():
        geometry = feature.geometry()
        # Check if the feature's geometry area meets the area threshold
        if geometry and geometry.area() >= area_threshold:
            # If it does, add the feature to the new layer
            new_feature = QgsFeature(fields)
            new_feature.setGeometry(geometry)
            for field in fields:
                new_feature.setAttribute(field.name(), feature[field.name()])
            output_layer_data_provider.addFeature(new_feature)

    # Update the layer's extent to the features it contains
    output_layer.updateExtents()


def fix_invalid_geometries(input_layer):
    """
    Fixes invalid geometries in a given layer.

    Args:
        input_layer (QgsVectorLayer): The layer to fix.

    Returns:
        QgsVectorLayer: A new layer with fixed geometries.
    """
    result = processing.run("native:fixgeometries", {
        'INPUT': input_layer,
        'OUTPUT': 'memory:'
    })
    fixed_layer = result['OUTPUT']

    return fixed_layer


def load_layer(file_path, layer_name):
    """
    Loads a GML file, fixes invalid geometries, and returns it as a QgsVectorLayer object
    with fixed geometries. Now also checks if the layer contains features.

    Args:
        file_path (str): The path to a GML file.
        layer_name (str): The name for the layer.

    Returns:
        QgsVectorLayer or None: A QgsVectorLayer object with fixed geometries if the layer is valid
        and contains features, None otherwise.
    """
    # Load GML file and fix geometries
    layer = QgsVectorLayer(file_path, layer_name, 'ogr')

    # Check if the layer contains no features
    if layer.featureCount() == 0:
        print(f"Layer contains no features: {file_path}")
        return None  # or return fixed_layer if you wish to return the layer even if it's empty

    # Check if layer is valid
    if not layer.isValid():
        print(f"Layer is not valid: {file_path}")
        return None

    # Fix invalid geometries
    fixed_layer = fix_invalid_geometries(layer)

    print(f"Fixed geometries for layer: {file_path}")
    return fixed_layer


def create_raster_mosaic(input_folder, output_path):
    """
    Creates a mosaic from all raster files in the specified folder.

    Args:
        input_folder (str): The path to the folder containing raster files.
        output_path (str): The path where the output mosaic raster will be saved.
    """
    # List all raster files in the input folder
    raster_files = [os.path.join(input_folder, f) for f in os.listdir(
        input_folder) if f.endswith(('.tif', '.tiff'))]

    # Check if there are raster files in the folder
    if not raster_files:
        print("No raster files found in the specified folder.")
        return

    # Use GDAL's merge algorithm. Adjust the 'DATA_TYPE' and other parameters as needed.
    params = {
        'INPUT': raster_files,
        'PCT': False,  # Set to True if you want to use a color palette
        'SEPARATE': False,  # Set to True to keep each input file in a separate band
        'DATA_TYPE': 5,  # 5 corresponds to Float32, adjust based on your input rasters
        'OPTIONS': 'COMPRESS=LZW',  # Add compression option here
        'OUTPUT': output_path
    }

    result = processing.run("gdal:merge", params)
    mosaic = result['OUTPUT']
    return mosaic


def main():

    # File paths for GML layers
    gml_file_paths = [
        '../data/vann/Basisdata_3238_Nannestad_5972_FKB-Vann_GML.gml',
        '../data/bygning/Basisdata_3238_Nannestad_5972_FKB-Bygning_GML.gml',
        '../data/stikkrenner/StikkrenneKulvert_79_KURVE.gml',
        '../data/stikkrenner/StikkrenneKulvert_79_PUNKT.gml',
        '../data/bygnanlegg/Basisdata_3238_Nannestad_5972_FKB-BygnAnlegg_GML.gml',
    ]

    # Load layers individually
    # Access and add layers to the map (assuming layers are valid)
    # water_layer = layers[0]
    # building_layer = layers[1]
    # culvert_curve = layers[2]
    # culvert_point = layers[3]
    # structure_layer = [4]

    catchment_polygon = load_layer(
        '../data/regine_enhet/NVEData/Nedborfelt_RegineEnhet.gml', "REGINEenhet")
    municipality_polygon = load_layer(
        '../data/kommune/Basisdata_3238_Nannestad_25832_Kommuner_GML.gml', "Kommune")
    ocean_polygon = load_layer(
        "../data/vann/Basisdata_3238_Nannestad_5972_FKB-Vann_GML.gml", "Havflate")
    # large_lakes_polygons = create_layer_from_area_threshold(load_layer(
    #     "../data/vann/Basisdata_3238_Nannestad_5972_FKB-Vann_GML.gml", "Innsjø"), 10000)

    # ----- Perform GIS operations on individual layers --------

    complete_watersheds = find_touching_polygons(
        catchment_polygon, municipality_polygon)

    dissolved_watersheds = dissolve_layer(complete_watersheds)

    # Fix invalid geometries
    if dissolved_watersheds.isValid():
        print(f"Dissolved layer is valid: {dissolved_watersheds}")
    else:
        print(f"Failed to fix geometries for layer: {dissolved_watersheds}")

    watershed_no_ocean = layer_difference(dissolved_watersheds, ocean_polygon)

    # height_mosaic = clip_and_mosaic_rasters("../data/dtm1/dtm1/data/", watershed_no_ocean, "../data/dtm1/dtm1/clipped/", "../data/dtm1/dtm1/mosaic.tif")

    raster_files = [os.path.join("../data/dtm1/dtm1/data/", f) for f in os.listdir("../data/dtm1/dtm1/data/") if f.endswith('.tif')]
    mosaic = create_raster_mosaic("../data/dtm1/dtm1/data/", "../data/dtm1/dtm1/clipped2/mosaic.tif")
    height_mosaic2 = clip_mosaic_by_vector(mosaic, watershed_no_ocean, "../data/dtm1/dtm1/mosaic2.tif")

    # Wrap up: Exit QGIS
    qgs.exitQgis()


if __name__ == "__main__":
    cProfile.run('main()', 'profile_output.txt')
    p = pstats.Stats('profile_output.txt')
    p.sort_stats('cumulative').print_stats(10)

