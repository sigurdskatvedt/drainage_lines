from qgis.analysis import QgsNativeAlgorithms
import processing
from processing.core.Processing import Processing
import sys
import cProfile
import pstats

from qgis.core import QgsApplication, QgsVectorLayer, QgsProject, QgsVectorFileWriter

# Initialize the QGIS Application
qgs = QgsApplication([], False)
qgs.initQgis()

def perform_gis_operations(input_layer_path, output_path, buffer_distance):
    """
    Performs the core GIS operations: loading a layer, buffering, and saving.

    Args:
        input_layer_path (str): Path to the input shapefile.
        output_path (str): Path to save the resulting buffered shapefile.
        buffer_distance: The buffer distance in the units of the layer's CRS.
    """

    # Load the shapefile
    layer = QgsVectorLayer(input_layer_path, 'example', 'ogr')
    if not layer.isValid():
        print("Layer failed to load!")
        return  # Exit early if there's an error

    QgsProject.instance().addMapLayer(layer)

    # Create a buffer
    buffer_layer = processing.run("native:buffer", {
        'INPUT': layer,
        'DISTANCE': buffer_distance,
        'SEGMENTS': 5, 
        'END_CAP_STYLE': 0, 
        'JOIN_STYLE': 0, 
        'MITER_LIMIT': 2,
        'DISSOLVE': False,
        'OUTPUT': 'memory:'
    })['OUTPUT']

    # Save the buffered layer to a new shapefile
    output_format = 'ESRI Shapefile'
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = output_format
    options.fileEncoding = "UTF-8"

    error = QgsVectorFileWriter.writeAsVectorFormatV3(layer=buffer_layer,
                                                     fileName=output_path,
                                                     transformContext=QgsProject.instance().transformContext(),
                                                     options=options)

    if error[0] == QgsVectorFileWriter.NoError:
        print("Buffer created successfully!")
    else:
        print("Error creating buffer:", error)

def main():
    # Initialize Processing framework
    Processing.initialize()

    input_layer_path = '../data/omrade.shp'
    output_path = '../data/result.shp'
    buffer_distance = 10

    perform_gis_operations(input_layer_path, output_path, buffer_distance)

    qgs.exitQgis() 

if __name__ == "__main__":
    cProfile.run('main()', 'profile_output.txt')
    p = pstats.Stats('profile_output.txt')
    p.sort_stats('cumulative').print_stats(10) 

