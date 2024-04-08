import csv
from PyQt5.QtCore import QEventLoop
import os
from processing.core.Processing import Processing
import sys
import cProfile
import pstats
from tasks.classify_flow_task import ClassifyFlowTask
import logging
from qgis.core import QgsApplication, QgsVectorLayer, QgsVectorFileWriter, QgsProject, QgsVectorFileWriter, QgsProcessingFeedback, QgsFeatureRequest, QgsFeature, QgsMessageLog, QgsTaskManager, QgsTask, QgsCoordinateReferenceSystem, QgsProviderRegistry
from dual_logger import log  # Make sure dual_logger.py is accessible

# Initialize the QGIS Application
qgs = QgsApplication([], False)
qgs.initQgis()

# Initialize QGIS and Processing framework
Processing.initialize()
feedback = QgsProcessingFeedback()


def addLayerToStorage(layer):
    log(f"Saved layer '{layer.name()}' to folder '{saving_folder}'. Feature count is: {layer.featureCount()}", level=logging.INFO)
    QgsVectorFileWriter.writeAsVectorFormatV3(layer, f"{saving_folder}{layer.name()}", QgsProject.instance(
    ).transformContext(), QgsVectorFileWriter.SaveVectorOptions())


def main():
    # Initialize the project instance
    project = QgsProject.instance()
    project.clear()  # Clear any existing project data

    classify_task = ClassifyFlowTask("Classifying flow accumulation raster",
                                     "../data/ringsaker/hoyde/flow_d8.tif", "../data/ringsaker/hoyde/classified_d8.tif", "../data/classification_rules.csv")

    QgsApplication.taskManager().addTask(classify_task)

    # Setup the event loop to wait for tasks to finish
    loop = QEventLoop()
    QgsApplication.taskManager().allTasksFinished.connect(loop.quit)
    loop.exec_()

    # Cleanup QGIS application
    qgs.exitQgis()


if __name__ == "__main__":
    main()
