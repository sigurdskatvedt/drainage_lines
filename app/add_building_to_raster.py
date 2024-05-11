import json
import sys
import cProfile
import pstats
from PyQt5.QtCore import QEventLoop
from tasks.rasterize_vector_task import RasterizeVectorTask
from tasks.add_rasters_task import AddRastersTask
from qgis.core import QgsApplication, QgsProject, QgsProcessingFeedback, QgsTask
from dual_logger import log  # Make sure dual_logger.py is accessible

# Initialize the QGIS Application
QgsApplication.setPrefixPath('/usr', True)
qgs = QgsApplication([], False)
qgs.initQgis()

# Add the path to Processing framework
sys.path.append('/usr/share/qgis/python/plugins/')

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
    # Initialize the project instance
    project = QgsProject.instance()
    project.clear()  # Clear any existing project data

    vector_layer_path = config_external['building_layer_path']
    building_polygon_layer = config_external['building_polygon_name']
    building_point_layer = config_external['building_point_name']
    reference_raster_path = config_analysis['reprojected_path']
    raster_output_path = config_analysis['building_raster_path']
    dtm_with_buildings_path = config_analysis['dtm_with_buildings_path']
    height = 10
    vectorize_buildings_task = RasterizeVectorTask(
        f"Giving all buildings height {height} meters and making raster",
        vector_layer_path, [building_polygon_layer, building_point_layer],
        reference_raster_path, raster_output_path, height)

    add_rasters_task = AddRastersTask(
        f"Adding layers {reference_raster_path} and {raster_output_path}",
        reference_raster_path, raster_output_path, dtm_with_buildings_path)

    add_rasters_task.addSubTask(vectorize_buildings_task, [],
                                QgsTask.ParentDependsOnSubTask)
    QgsApplication.taskManager().addTask(add_rasters_task)

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
