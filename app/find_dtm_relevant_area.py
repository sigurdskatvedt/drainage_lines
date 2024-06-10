import cProfile
import pstats
import os
import json
import sys
import logging
from tasks.find_touching_polygons_task import FindTouchingPolygonsTask
from tasks.load_layer_task import LoadLayersTask
from tasks.create_mosaic_task import CreateMosaicTask
from tasks.clip_raster_by_vector_task import ClipRasterByVectorTask
from tasks.dissolve_and_buffer_task import DissolveAndBufferVectorTask
from PyQt5.QtCore import QEventLoop
from dual_logger import log  # Make sure dual_logger.py is accessible
from qgis.core import QgsApplication, QgsVectorLayer, QgsVectorFileWriter, QgsProject, QgsVectorFileWriter, QgsProcessingFeedback, QgsFeatureRequest, QgsFeature, QgsMessageLog, QgsTaskManager, QgsTask, QgsCoordinateReferenceSystem, QgsProviderRegistry

# Initialize the QGIS Application
QgsApplication.setPrefixPath('/usr', True)
qgs = QgsApplication([], False)
qgs.initQgis()

# Add the path to Processing framework
sys.path.append('/usr/share/qgis/python/plugins/')

# Import processing after initializing QGIS application
from processing.core.Processing import Processing

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

    project_crs = config_external['crs']
    crs = QgsCoordinateReferenceSystem()
    crs.createFromString(project_crs)
    project.setCrs(crs)

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
        config_external['municipality_layer_path'],
        municipality_layer_name,
        municipality_layer_name,
        crs=project_crs,
        expression=f'"kommunenummer" = {municipality_number_norway}')
    municipality_polygon_task.layerLoaded.connect(add_layer_to_storage)

    touching_layer_name = "CompleteWatersheds"
    touching_task = FindTouchingPolygonsTask(
        "Make superset of entire polygon area", touching_layer_name,
        catchment_layer_name, municipality_layer_name)
    touching_task.layerLoaded.connect(add_layer_to_storage)

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
    dissolved_buffered_path = config_analysis['dissolved_buffered_path']

    dissolve_buffer_task = DissolveAndBufferVectorTask(
        "Dissolve and buffer vector layer", touching_layer_name,
        buffer_area_meters, dissolved_buffered_path)

    dissolve_buffer_task.addSubTask(touching_task, [],
                                    QgsTask.ParentDependsOnSubTask)
    dissolve_buffer_task.addSubTask(create_mosaic_task, [],
                                    QgsTask.ParentDependsOnSubTask)

    clip_mosaic_task = ClipRasterByVectorTask(
        "Clip mosaic by buffered vector polygon",
        config_analysis['complete_mosaic_path'], dissolved_buffered_path,
        config_analysis['clipped_mosaic_path'])

    clip_mosaic_task.addSubTask(dissolve_buffer_task, [],
                                QgsTask.ParentDependsOnSubTask)

    QgsApplication.taskManager().addTask(clip_mosaic_task)

    loop = QEventLoop()
    QgsApplication.taskManager().allTasksFinished.connect(loop.quit)
    loop.exec_()

    # Cleanup QGIS application
    qgs.exitQgis()


if __name__ == "__main__":
    cProfile.run('main()', 'profile_output.txt')
    p = pstats.Stats('pre_process_output.txt')
    p.sort_stats('cumulative').print_stats(10)
