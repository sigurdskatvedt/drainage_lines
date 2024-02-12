from qgis.analysis import QgsNativeAlgorithms
import processing
import os
from processing.core.Processing import Processing
import sys
import cProfile
import pstats

from qgis.core import QgsApplication, QgsVectorLayer, QgsProject, QgsVectorFileWriter

# Initialize the QGIS Application
qgs = QgsApplication([], False)
qgs.initQgis()


def perform_gis_operations(input_layer, output_path, buffer_distance):
    """
    Performs GIS operations on a GML layer: loading, buffering, and saving.

    Args:
      input_layer_path (str): Path to the input GML file.
      output_path (str): Path to save the buffered output as GML.
      buffer_distance: The buffer distance in the units of the layer's CRS.
    """

    # Load the GML layer
    if not input_layer.isValid():
        print("Layer failed to load!")
        return  # Exit early if there's an error

    QgsProject.instance().addMapLayer(input_layer)

    # Create a buffer (Same as before)
    buffer_layer = processing.run("native:buffer", {
        'INPUT': input_layer,
        'DISTANCE': buffer_distance,
        'SEGMENTS': 5,
        'END_CAP_STYLE': 0,
        'JOIN_STYLE': 0,
        'MITER_LIMIT': 2,
        'DISSOLVE': False,
        'OUTPUT': 'memory:'
    })['OUTPUT']

    # Save the buffered layer as GML
    output_format = 'GML'  # Specify GML output
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = output_format
    options.fileEncoding = "UTF-8"
    options.layerOptions = ['FORCE_XY=YES']  # Option for 2D output, if needed

    error = QgsVectorFileWriter.writeAsVectorFormatV3(layer=buffer_layer,
                                                      fileName=output_path,
                                                      transformContext=QgsProject.instance().transformContext(),
                                                      options=options)

    if error[0] == QgsVectorFileWriter.NoError:
        print("Buffer created successfully!")
    else:
        print("Error creating buffer:", error)


def load_layers(file_paths):
    """Loads multiple GML files and returns them as a list of QgsVectorLayer objects.

    Args:
        file_paths (list): A list of paths to GML files.
    """
    layers = []

    # Load GML files
    for file_path in file_paths:
        layer = QgsVectorLayer(file_path, os.path.basename(
            file_path), 'ogr')  # Use basename for layer name
        if not layer.isValid():
            print(f"Error loading layer: {file_path}")
            continue  # Skip to the next file if there's an error
        layers.append(layer)

    return layers


def main():
    # Initialize QGIS and Processing framework
    Processing.initialize()

    # File paths for GML layers
    gml_file_paths = [
        '../data/vann/Basisdata_3238_Nannestad_5972_FKB-Vann_GML.gml',
        '../data/bygning/Basisdata_3238_Nannestad_5972_FKB-Bygning_GML.gml',
        '../data/stikkrenner/StikkrenneKulvert_79_KURVE.gml',
        '../data/stikkrenner/StikkrenneKulvert_79_PUNKT.gml',
        '../data/bygnanlegg/Basisdata_3238_Nannestad_5972_FKB-BygnAnlegg_GML.gml',
        '../data/kommune/Basisdata_3238_Nannestad_25832_Kommuner_GML.gml',
        '../data/regine_enhet/NVEData/Nedborfelt_RegineEnhet.gml',
    ]

    # Load layers individually
    layers = load_layers(gml_file_paths)

    # Access and add layers to the map (assuming layers are valid)
    water_layer = layers[0]
    building_layer = layers[1]
    culvert_curve = layers[2]
    culvert_point = layers[3]
    structure_layer = [4]
    municipality_layer = [5]
    watershed_layer = [6]

    # ----- Perform GIS operations on individual layers --------

    # Example: Buffer the first layer (vann_layer)
    perform_gis_operations(water_layer, 'output_vann.gml', 10) 


    # Wrap up: Exit QGIS
    qgs.exitQgis()

    # Profiling code
    cProfile.run('main()', 'profile_output.txt')
    p = pstats.Stats('profile_output.txt')
    p.sort_stats('cumulative').print_stats(10)


if __name__ == "__main__":
    cProfile.run('main()', 'profile_output.txt')
    p = pstats.Stats('profile_output.txt')
    p.sort_stats('cumulative').print_stats(10)
