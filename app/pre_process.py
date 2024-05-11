from PyQt5.QtCore import QEventLoop
import cProfile
import pstats
import os
import json
import sys
from tasks.find_touching_polygons_task import FindTouchingPolygonsTask
from tasks.load_layer_task import LoadLayersTask
from tasks.create_mosaic_task import CreateMosaicTask, ClipMosaicByVectorTask, ReprojectRasterTask
import logging
from qgis.core import QgsApplication, QgsVectorLayer, QgsVectorFileWriter, QgsProject, QgsVectorFileWriter, QgsProcessingFeedback, QgsFeatureRequest, QgsFeature, QgsMessageLog, QgsTaskManager, QgsTask, QgsCoordinateReferenceSystem, QgsProviderRegistry
from dual_logger import log  # Make sure dual_logger.py is accessible

# Initialize the QGIS Application
QgsApplication.setPrefixPath('/usr', True)
qgs = QgsApplication([], False)
qgs.initQgis()

# Add the path to Processing framework
sys.path.append('/usr/share/qgis/python/plugins/')

# Import processing after initializing QGIS application
from qgis import processing
from processing.core.Processing import Processing
from processing.algs.gdal.GdalAlgorithmProvider import GdalAlgorithmProvider, GdalUtils

Processing.initialize()


def add_layer_to_storage(layer, saving_folder):
    log(f"Saved layer '{layer.name()}' to folder '{saving_folder}'. Feature count is: {layer.featureCount()}",
        level=logging.INFO)
    QgsVectorFileWriter.writeAsVectorFormatV3(
        layer, f"{saving_folder}{layer.name()}",
        QgsProject.instance().transformContext(),
        QgsVectorFileWriter.SaveVectorOptions())


def load_paths_from_config(config_path):
    with open(config_path, 'r') as config_file:
        return json.load(config_file)


# Load the configuration
config_external = load_paths_from_config('paths/os/paths_external.json')
config_analysis = load_paths_from_config('paths/os/paths_analysis.json')


def main():
    # Initialize the project instance
    project = QgsProject.instance()
    project.clear()  # Clear any existing project data

    project_crs = "EPSG:32632"
    project.setCrs = project_crs

    # Create the load layer tasks
    catchment_layer_name = "Nedborfelt_REGINEenhet"

    catchment_polygon_task = LoadLayersTask(
        "Loading catchment data", config_external['catchment_layer_path'],
        catchment_layer_name, catchment_layer_name)
    catchment_polygon_task.layerLoaded.connect(add_layer_to_storage)

    municipality_number_norway = 3430
    municipality_layer_name = "Kommune"
    municipality_polygon_task = LoadLayersTask(
        "Loading municipality polygon",
        config_external['municipality_layer_path'], municipality_layer_name,
        municipality_layer_name,
        f'"kommunenummer" = {municipality_number_norway}')
    municipality_polygon_task.layerLoaded.connect(add_layer_to_storage)

    touching_layer_name = "CompleteWatersheds"
    touching_task = FindTouchingPolygonsTask(
        "Make superset of entire polygon area", touching_layer_name,
        catchment_layer_name, municipality_layer_name)
    touching_task.layerLoaded.connect(add_layer_to_storage)

    # water_layer_name = "Elv"
    # lakes_output_name = "large_lakes"
    # large_lake_threshold = 100000
    # large_lakes_task = LoadLayersTask(
    #     "Large lakes",
    #     water_layer_name,
    #     config_external['water_layer_path'],
    #     lakes_output_name,
    #     expression=f'area($geometry) > {large_lake_threshold}')

    # Add load layer tasks as subtasks to the find touching polygons task
    # Note: Adjust the addSubTask method according to your task class implementation
    touching_task.addSubTask(catchment_polygon_task, [],
                             QgsTask.ParentDependsOnSubTask)
    touching_task.addSubTask(municipality_polygon_task, [],
                             QgsTask.ParentDependsOnSubTask)

    raster_files = [
        os.path.join(config_external['raster_data_folder'], f)
        for f in os.listdir(config_external['raster_data_folder'])
        if f.endswith('.tif')
    ]

    create_mosaic_task = CreateMosaicTask(
        "Create Mosaic of raster files", raster_files,
        config_analysis['complete_mosaic_path'])

    buffer_area_meters = 50
    clip_mosaic_task = ClipMosaicByVectorTask(
        "Clip mosaic by vector polygon",
        config_analysis['complete_mosaic_path'], touching_layer_name,
        buffer_area_meters, config_analysis['clipped_mosaic_path'])

    clip_mosaic_task.addSubTask(touching_task, [],
                                QgsTask.ParentDependsOnSubTask)
    clip_mosaic_task.addSubTask(create_mosaic_task, [],
                                QgsTask.ParentDependsOnSubTask)

    reproject_raster_task = ReprojectRasterTask(
        f"Reprojecting raster to {project_crs}",
        config_analysis['clipped_mosaic_path'], project_crs,
        config_analysis['reprojected_path'])

    reproject_raster_task.addSubTask(clip_mosaic_task, [],
                                     QgsTask.ParentDependsOnSubTask)

    QgsApplication.taskManager().addTask(reproject_raster_task)

    # Setup the event loop to wait for tasks to finish
    loop = QEventLoop()
    QgsApplication.taskManager().allTasksFinished.connect(loop.quit)
    loop.exec_()

    # Cleanup QGIS application
    qgs.exitQgis()


if __name__ == "__main__":
    cProfile.run('main()', 'profile_output.txt')
    p = pstats.Stats('profile_output.txt')
    p.sort_stats('cumulative').print_stats(10)
