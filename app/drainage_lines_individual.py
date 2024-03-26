from qgis.analysis import QgsNativeAlgorithms
import processing
from processing.tools import dataobjects
import csv
from PyQt5.QtCore import QEventLoop
import os
from processing.core.Processing import Processing
import sys
import cProfile
import pstats
from tasks.find_touching_polygons_task import FindTouchingPolygonsTask
from tasks.create_layer_from_threshold import CreateLayerFromThresholdTask
from tasks.layer_difference_task import LayerDifferenceTask
from tasks.accumulation_task import AccumulationTask
from tasks.load_layer_task import LoadLayerTask
from tasks.create_mosaic_task import CreateMosaicTask, ClipMosaicByVectorTask
from tasks.depression_fill_task import DepressionFillTask
from tasks.accumulation_task import AccumulationTask
import logging
from qgis.core import QgsApplication, QgsVectorLayer, QgsVectorFileWriter, QgsProject, QgsVectorFileWriter, QgsProcessingFeedback, QgsFeatureRequest, QgsFeature, QgsMessageLog, QgsTaskManager, QgsTask, QgsCoordinateReferenceSystem, QgsProviderRegistry
from dual_logger import log  # Make sure dual_logger.py is accessible
from processing_saga_nextgen.processing.provider import SagaNextGenAlgorithmProvider

# Initialize the QGIS Application
qgs = QgsApplication([], False)
qgs.initQgis()

# Initialize QGIS and Processing framework
Processing.initialize()
feedback = QgsProcessingFeedback()


def write_file_paths(file_path, output_file):
    raster_files = [os.path.join(file_path, f)
                    for f in os.listdir(file_path) if f.endswith('.tif')]
    with open(output_file, 'w') as file:
        for file_path in raster_files:
            file.write(file_path + '\n')


def write_log_message(message, tag, level):
    with open(logfile_name, 'a') as logfile:
        logfile.write('{tag}({level}): {message}'.format(tag=tag, level=level, message=message))


def addLayerToStorage(layer):
    log(f"Saved layer '{layer.name()}' to folder '{saving_folder}'. Feature count is: {layer.featureCount()}", level=logging.INFO)
    QgsVectorFileWriter.writeAsVectorFormatV3(layer, f"{saving_folder}{layer.name()}", QgsProject.instance(
    ).transformContext(), QgsVectorFileWriter.SaveVectorOptions())


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


def main():
    provider = SagaNextGenAlgorithmProvider()
    QgsApplication.processingRegistry().addProvider(provider)

    # Initialize the project instance
    project = QgsProject.instance()
    project.clear()  # Clear any existing project data

    # Create the load layer tasks
    catchment_layer_name = "REGINEenhet"

    # Load catchment layer directly
    catchment_layer_path = '../data/regine_enhet/NVEData/Nedborfelt_RegineEnhet.gml'
    catchment_layer = QgsVectorLayer(catchment_layer_path, "Catchment Layer", "ogr")

    municipality_layer_name = "Kommune"
    municipality_polygon_task = LoadLayerTask("Loading municipality polygon", municipality_layer_name,
                                              '../data/kommune/Basisdata_3238_Nannestad_25832_Kommuner_GML.gml')
    municipality_polygon_task.layerLoaded.connect(addLayerToStorage)

    touching_layer_name = "CompleteWatersheds"
    # Create the find touching polygons task without adding it to the task manager yet
    touching_task = FindTouchingPolygonsTask(
        "Find Touching Polygons", touching_layer_name, catchment_layer_name, municipality_layer_name)
    touching_task.layerLoaded.connect(addLayerToStorage)

    raster_path = "../data/dtm1/dtm1/data/"
    

    complete_mosaic_path = "../data/dtm1/dtm1/clipped2/mosaic.tif"
    clipped_mosaic_path = "../data/dtm1/dtm1/clipped2/mosaic_clipped.tif"

    file_txt_path = os.path.join("../data/dtm1/dtm1/data/", "grid_paths.txt")
    write_file_paths(raster_path, file_txt_path)

    create_mosaic_task = CreateMosaicTask("Create Mosaic of raster files",
                                          file_txt_path, complete_mosaic_path)

    QgsApplication.taskManager().addTask(create_mosaic_task)

    # for feature in catchment_layer.getFeatures():
    #     catchment_id = feature['vassdragsnummer'].replace(".", "_")
    #     geom = feature.geometry()
    #     log(type(geom))
    #
    #     catchment_path = f"../data/dtm1/dtm1/catchment_layers/catchment_{catchment_id}.tif"
    #     accumulation_path = f"../data/dtm1/dtm1/catchment_layers/accumulation_{catchment_id}.tif"
    #     method = 2
    #
    #     clip_task = ClipMosaicByVectorTask(
    #         f"Clipping feature to {catchment_path}.", complete_mosaic_path, feature, catchment_path)
    #
    #     accumulation_task = AccumulationTask(
    #         f"Accumulation to {accumulation_path}", catchment_path, method, accumulation_path)
    #
    #
    #     log(f"Starting {catchment_id}")
    #     QgsApplication.taskManager().addTask(clip_task)

    # Setup the event loop to wait for tasks to finish
    loop = QEventLoop()
    QgsApplication.taskManager().allTasksFinished.connect(loop.quit)
    loop.exec_()

    # Cleanup QGIS application
    qgs.exitQgis()


if __name__ == "__main__":
    main()
