import csv
from PyQt5.QtCore import QEventLoop
import os
import json
import sys
import cProfile
import pstats
from tasks.merge_vectors_task import MergeVectorLayersTask
from tasks.load_layer_task import LoadLayersTask
from tasks.save_layer_task import SaveLayerToFileTask
import logging
from qgis.core import QgsApplication, QgsVectorLayer, QgsVectorFileWriter, QgsProject, QgsVectorFileWriter, QgsProcessingFeedback, QgsFeatureRequest, QgsFeature, QgsMessageLog, QgsTaskManager, QgsTask, QgsCoordinateReferenceSystem, QgsProviderRegistry
from qgis.analysis import QgsNativeAlgorithms
from dual_logger import log  # Make sure dual_logger.py is accessible
from processing_saga_nextgen.processing.provider import SagaNextGenAlgorithmProvider

# Initialize the QGIS Application
qgs = QgsApplication([], False)
qgs.initQgis()

# Import processing after initializing QGIS application
from qgis import processing

# Register algorithms
QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())

# Initialize QGIS and Processing framework
feedback = QgsProcessingFeedback()

def load_paths_from_config(config_path):
    with open(config_path, 'r') as config_file:
        return json.load(config_file)


# Load the configuration
config = load_paths_from_config('paths/paths.json')


def main():
    provider = SagaNextGenAlgorithmProvider()
    QgsApplication.processingRegistry().addProvider(provider)

    # Initialize the project instance
    project = QgsProject.instance()
    project.clear()  # Clear any existing project data


    # Difference between the two culverts are "culvert_line" has opening < 1 meter
    building_culvert_polygon_name = ["Stikkrenne"]
    building_culvert_output_name = "Building_Culvert"
    building_culvert_line_task = LoadLayersTask("Loading culvert line data", config['construction_layer_path'], building_culvert_polygon_name, building_culvert_output_name)

    road_culvert_polygon = [config['road_culvert_name']]
    road_culvert_output_name = "Road_Culvert"
    road_culvert_line_task = LoadLayersTask("Loading road culvert line data", config['road_culvert_path'], road_culvert_polygon, road_culvert_output_name)

    water_name = ["ElvBekk", "KanalGrøft"]
    water_culvert_output_name = "Water_Culvert"
    water_culvert_line_task = LoadLayersTask("Loading water culvert data",config['water_layer_path'], water_name, water_culvert_output_name, attribute_field="medium", attribute_value="U")

    all_culverts_name = "AllCulverts"
    # Create the find touching polygons task without adding it to the task manager yet
    all_culverts_task = MergeVectorLayersTask(
        "Merge culverts from water and building data", all_culverts_name, [building_culvert_output_name, water_culvert_output_name, road_culvert_output_name])

    # Add load layer tasks as subtasks to the find touching polygons task
    # Note: Adjust the addSubTask method according to your task class implementation
    all_culverts_task.addSubTask(building_culvert_line_task, [], QgsTask.ParentDependsOnSubTask)
    all_culverts_task.addSubTask(water_culvert_line_task, [], QgsTask.ParentDependsOnSubTask)
    all_culverts_task.addSubTask(road_culvert_line_task, [], QgsTask.ParentDependsOnSubTask)

    water_output_name = "AllWaterLines"
    add_water_task = LoadLayersTask("Loading water data", config['water_layer_path'], water_name, water_output_name)

    all_culverts_and_water_name = "AllCulvertsAndWater"
    all_culverts_and_water_task = MergeVectorLayersTask(
        "Merge Culverts and Water", all_culverts_and_water_name, [all_culverts_name, water_output_name])

    all_culverts_and_water_task.addSubTask(all_culverts_task, [], QgsTask.ParentDependsOnSubTask)
    all_culverts_and_water_task.addSubTask(add_water_task, [], QgsTask.ParentDependsOnSubTask)

    save_all_task = SaveLayerToFileTask("Saving layer with water and culverts", all_culverts_and_water_name, config['water_and_culverts_path'])
    save_culverts_task= SaveLayerToFileTask("Saving layer with culverts", all_culverts_name, config['culverts_path'])
    save_all_task.addSubTask(all_culverts_and_water_task, [], QgsTask.ParentDependsOnSubTask)
    save_culverts_task.addSubTask(save_all_task, [], QgsTask.ParentDependsOnSubTask)
    
    QgsApplication.taskManager().addTask(save_culverts_task)


    # Setup the event loop to wait for tasks to finish
    loop = QEventLoop()
    QgsApplication.taskManager().allTasksFinished.connect(loop.quit)
    loop.exec_()

    # Cleanup QGIS application
    qgs.exitQgis()


if __name__ == "__main__":
    main()
