from qgis.analysis import QgsNativeAlgorithms
import processing
from processing.tools import dataobjects
import csv
from PyQt5.QtCore import QEventLoop
import os
import json
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
from tasks.catchment_task import AccumulationTask
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


def write_log_message(message, tag, level):
    with open(logfile_name, 'a') as logfile:
        logfile.write('{tag}({level}): {message}'.format(tag=tag, level=level, message=message))


def addLayerToStorage(layer, saving_folder):
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


def load_paths_from_config(config_path):
    with open(config_path, 'r') as config_file:
        return json.load(config_file)


# Load the configuration
config = load_paths_from_config('paths_config.json')


def main():
    provider = SagaNextGenAlgorithmProvider()
    QgsApplication.processingRegistry().addProvider(provider)

    # Initialize the project instance
    project = QgsProject.instance()
    project.clear()  # Clear any existing project data

    # Create the load layer tasks
    catchment_layer_name = "REGINEenhet"

    catchment_polygon_task = LoadLayerTask("Loading catchment data", catchment_layer_name,
                                           config['catchment_layer_path'])
    catchment_polygon_task.layerLoaded.connect(addLayerToStorage)

    municipality_layer_name = "Kommune"
    municipality_polygon_task = LoadLayerTask("Loading municipality polygon", municipality_layer_name,
                                              config['municipality_layer_path'])
    municipality_polygon_task.layerLoaded.connect(addLayerToStorage)

    touching_layer_name = "CompleteWatersheds"
    # Create the find touching polygons task without adding it to the task manager yet
    touching_task = FindTouchingPolygonsTask(
        "Find Touching Polygons", touching_layer_name, catchment_layer_name, municipality_layer_name)
    touching_task.layerLoaded.connect(addLayerToStorage)

    water_layer_name = "Elv"
    water_task = LoadLayerTask("Test open layer task", water_layer_name,
                               config['water_layer_path'])

    # Add load layer tasks as subtasks to the find touching polygons task
    # Note: Adjust the addSubTask method according to your task class implementation
    touching_task.addSubTask(catchment_polygon_task, [], QgsTask.ParentDependsOnSubTask)
    touching_task.addSubTask(municipality_polygon_task, [], QgsTask.ParentDependsOnSubTask)

    

    raster_files = [os.path.join(config['raster_data_folder'], f)
                    for f in os.listdir(config['raster_data_folder']) if f.endswith('.tif')]

    create_mosaic_task = CreateMosaicTask("Create Mosaic of raster files",
                                          raster_files, config['complete_mosaic_path'])

    clip_mosaic_task = ClipMosaicByVectorTask("Clip mosaic by vector polygon",
                                              config['complete_mosaic_path'], touching_layer_name, config['clipped_mosaic_path'])

    clip_mosaic_task.addSubTask(touching_task, [], QgsTask.ParentDependsOnSubTask)
    clip_mosaic_task.addSubTask(create_mosaic_task, [], QgsTask.ParentDependsOnSubTask)

    QgsApplication.taskManager().addTask(clip_mosaic_task)


    # Setup the event loop to wait for tasks to finish
    loop = QEventLoop()
    QgsApplication.taskManager().allTasksFinished.connect(loop.quit)
    loop.exec_()

    # Cleanup QGIS application
    qgs.exitQgis()


if __name__ == "__main__":
    main()
