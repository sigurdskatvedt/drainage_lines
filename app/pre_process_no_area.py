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
from tasks.create_mosaic_task import CreateMosaicTask, ClipMosaicByVectorTask
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
config = load_paths_from_config('paths_ringsaker.json')


def main():
    provider = SagaNextGenAlgorithmProvider()
    QgsApplication.processingRegistry().addProvider(provider)

    # Initialize the project instance
    project = QgsProject.instance()
    project.clear()  # Clear any existing project data

    raster_files = [os.path.join(config['raster_data_folder'], f)
                    for f in os.listdir(config['raster_data_folder']) if f.endswith('.tif')]

    create_mosaic_task = CreateMosaicTask("Create Mosaic of raster files",
                                          raster_files, config['complete_mosaic_path'])

    clip_mosaic_task = ClipMosaicByVectorTask("Clip mosaic by vector polygon",
                                              config['complete_mosaic_path'], config['area_file_path'], config['clipped_mosaic_path'])

    # clip_mosaic_task.addSubTask(create_mosaic_task, [], QgsTask.ParentDependsOnSubTask)

    QgsApplication.taskManager().addTask(clip_mosaic_task)


    # Setup the event loop to wait for tasks to finish
    loop = QEventLoop()
    QgsApplication.taskManager().allTasksFinished.connect(loop.quit)
    loop.exec_()

    # Cleanup QGIS application
    qgs.exitQgis()


if __name__ == "__main__":
    main()
