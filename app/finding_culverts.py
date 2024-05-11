import cProfile
import pstats
from PyQt5.QtCore import QEventLoop
import json
from tasks.merge_vectors_task import MergeVectorLayersTask
from tasks.load_layer_task import LoadLayersTask
from tasks.save_layer_task import SaveLayerToFileTask
from tasks.rasterize_vector_task import RasterizeVectorTask
from tasks.add_rasters_task import AddRastersTask
from qgis.core import QgsApplication, QgsVectorLayer, QgsVectorFileWriter, QgsProject, QgsVectorFileWriter, QgsProcessingFeedback, QgsFeatureRequest, QgsFeature, QgsMessageLog, QgsTaskManager, QgsTask, QgsCoordinateReferenceSystem, QgsProviderRegistry
from qgis.analysis import QgsNativeAlgorithms
from processing_saga_nextgen.processing.provider import SagaNextGenAlgorithmProvider

# Initialize the QGIS Application
qgs = QgsApplication([], False)
qgs.initQgis()

# Import processing after initializing QGIS application
from qgis import processing

# Register algorithms
QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())

from processing.core.Processing import Processing

Processing.initialize()

# Initialize QGIS and Processing framework
feedback = QgsProcessingFeedback()


def load_paths_from_config(config_path):
    with open(config_path, 'r') as config_file:
        return json.load(config_file)


# Load the configuration
config_external = load_paths_from_config('paths/os/paths_external.json')
config_analysis = load_paths_from_config('paths/os/paths_analysis.json')


def main():
    provider = SagaNextGenAlgorithmProvider()
    QgsApplication.processingRegistry().addProvider(provider)

    # Initialize the project instance
    project = QgsProject.instance()
    project.clear()  # Clear any existing project data

    # Difference between the two culverts are "culvert_line" has opening < 1 meter
    building_culvert_polygon_name = ["Stikkrenne"]
    building_culvert_output_name = "Building_Culvert"
    building_culvert_line_task = LoadLayersTask(
        "Loading culvert line data",
        config_external['construction_layer_path'],
        building_culvert_polygon_name, building_culvert_output_name)

    road_culvert_polygon = [config_external['road_culvert_name']]
    road_culvert_output_name = "Road_Culvert"
    road_culvert_line_task = LoadLayersTask(
        "Loading road culvert line data", config_external['road_culvert_path'],
        road_culvert_polygon, road_culvert_output_name)

    water_name = ["ElvBekk", "KanalGrøft"]
    water_culvert_output_name = "Water_Culvert"
    water_culvert_line_task = LoadLayersTask(
        "Loading water culvert data",
        config_external['water_layer_path'],
        water_name,
        water_culvert_output_name,
        expression='"medium" = \'U\'')

    all_culverts_name = "AllCulverts"
    # Create the find touching polygons task without adding it to the task manager yet
    all_culverts_task = MergeVectorLayersTask(
        "Merge culverts from water and building data", all_culverts_name, [
            building_culvert_output_name, water_culvert_output_name,
            road_culvert_output_name
        ])

    # Add load layer tasks as subtasks to the find touching polygons task
    # Note: Adjust the addSubTask method according to your task class implementation
    all_culverts_task.addSubTask(building_culvert_line_task, [],
                                 QgsTask.ParentDependsOnSubTask)
    all_culverts_task.addSubTask(water_culvert_line_task, [],
                                 QgsTask.ParentDependsOnSubTask)
    all_culverts_task.addSubTask(road_culvert_line_task, [],
                                 QgsTask.ParentDependsOnSubTask)

    culverts_path = config_analysis['culverts_path']

    save_culverts_task = SaveLayerToFileTask("Saving layer with culverts",
                                             all_culverts_name, culverts_path)

    save_culverts_task.addSubTask(all_culverts_task, [],
                                  QgsTask.ParentDependsOnSubTask)

    height = -5
    reference_raster_path = config_analysis['dtm_with_buildings_path']
    raster_culvert_output_path = config_analysis['raster_culvert_path']
    culverts_name = config_analysis['culverts_name']
    culverts_negative_height_task = RasterizeVectorTask(
        f"Giving all culverts negative height {height} meters and making raster",
        culverts_path, [culverts_name], reference_raster_path,
        raster_culvert_output_path, height)
    culverts_negative_height_task.addSubTask(save_culverts_task, [],
                                             QgsTask.ParentDependsOnSubTask)

    add_rasters_culvert_task = AddRastersTask(
        f"Adding layers {reference_raster_path} and {raster_culvert_output_path}",
        reference_raster_path, raster_culvert_output_path,
        config_analysis['dtm_buildings_culverts_path'])

    add_rasters_culvert_task.addSubTask(culverts_negative_height_task, [],
                                        QgsTask.ParentDependsOnSubTask)

    QgsApplication.taskManager().addTask(add_rasters_culvert_task)

    water_output_name = "AllWaterLines"
    add_water_task = LoadLayersTask("Loading water data",
                                    config_external['water_layer_path'],
                                    water_name, water_output_name)

    all_culverts_and_water_name = "AllCulvertsAndWater"
    all_culverts_and_water_task = MergeVectorLayersTask(
        "Merge Culverts and Water", all_culverts_and_water_name,
        [all_culverts_name, water_output_name])

    all_culverts_and_water_task.addSubTask(all_culverts_task, [],
                                           QgsTask.ParentDependsOnSubTask)
    all_culverts_and_water_task.addSubTask(add_water_task, [],
                                           QgsTask.ParentDependsOnSubTask)

    water_culverts_path = config_analysis['water_culverts_path']
    save_all_task = SaveLayerToFileTask("Saving layer with water and culverts",
                                        all_culverts_and_water_name,
                                        water_culverts_path)

    save_all_task.addSubTask(all_culverts_and_water_task, [],
                             QgsTask.ParentDependsOnSubTask)

    water_culverts_name = config_analysis['water_culverts_name']
    raster_water_culverts_path = config_analysis['raster_water_culvert_path']
    water_culverts_negative_height_task = RasterizeVectorTask(
        f"Giving all culverts and water negative height {height} meters and making raster",
        water_culverts_path, [water_culverts_name], reference_raster_path,
        raster_water_culverts_path, height)
    water_culverts_negative_height_task.addSubTask(
        save_all_task, [], QgsTask.ParentDependsOnSubTask)

    add_rasters_culverts_water_task = AddRastersTask(
        f"Adding layers {reference_raster_path} and {raster_water_culverts_path}",
        reference_raster_path, raster_water_culverts_path,
        config_analysis['dtm_buildings_culverts_water_path'])

    add_rasters_culverts_water_task.addSubTask(water_culverts_negative_height_task,
                                               [],
                                               QgsTask.ParentDependsOnSubTask)

    QgsApplication.taskManager().addTask(add_rasters_culverts_water_task)

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
