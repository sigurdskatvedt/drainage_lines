import cProfile
import pstats
import sys
import json
from dual_logger import log
from tasks.find_raster_difference_task import FindDifferenceRastersTask
from tasks.vectorize_raster_task import VectorizeRasterTask
from tasks.load_layer_task import LoadLayersTask
from tasks.save_layer_task import SaveLayerToFileTask
from tasks.set_nodata_task import SetNoDataRasterTask
from tasks.collect_geometries_task import CollectGeometriesTask
from tasks.vector_difference import VectorDifferenceTask
from PyQt5.QtCore import QEventLoop
from qgis.core import QgsApplication, QgsProcessingFeedback, QgsProject, QgsTask, QgsCoordinateReferenceSystem

sys.path.append('/usr/share/qgis/python/plugins/')
from processing.core.Processing import Processing

# Initialize the QGIS Application
qgs = QgsApplication([], False)
qgs.initQgis()

# Initialize QGIS and Processing framework
Processing.initialize()
feedback = QgsProcessingFeedback()


def load_paths_from_config(config_path):
    with open(config_path, 'r') as config_file:
        return json.load(config_file)


# Load the configuration
config_analysis = load_paths_from_config('paths/os/paths_analysis.json')
config_external = load_paths_from_config('paths/os/paths_external.json')


def main():
    # Initialize the project instance
    project = QgsProject.instance()
    project.clear()  # Clear any existing project data
    #
    project_crs = config_external['crs']
    crs = QgsCoordinateReferenceSystem()
    crs.createFromString(project_crs)
    project.setCrs(crs)

    # Define the new task for finding raster difference (for depressions in this case)
    find_difference_task = FindDifferenceRastersTask(
        "Finding differences between filled vs. original DTM",
        config_analysis['dtm_filled'], config_analysis['dtm_original'],
        config_analysis['depressions'])

    non_zero_path = config_analysis['depressions_no_zero']
    set_no_data_task = SetNoDataRasterTask(
        "Setting zero or less to nodata in depressions raster",
        config_analysis['depressions'], non_zero_path)

    set_no_data_task.addSubTask(find_difference_task, [],
                                QgsTask.ParentDependsOnSubTask)

    depressions_name = "Depressions"
    vectorize_raster_task = VectorizeRasterTask(
        "Vectorizing depression layer", non_zero_path,
        config_analysis['depressions_vector'], depressions_name)

    vectorize_raster_task.addSubTask(set_no_data_task, [],
                                     QgsTask.ParentDependsOnSubTask)

    lake_polygons_name = "LakePolygons"
    load_lakes_task = LoadLayersTask("Loading lake layer",
                                     config_external['water_layer_path'],
                                     ['Innsjø'],
                                     lake_polygons_name,
                                     crs=crs)

    depressions_no_lakes_name = "DepressionsNoLakes"
    depressions_path = config_analysis['depressions_vector']
    depressions_no_lakes_task = VectorDifferenceTask(
        "Finding depression layer with no lakes", depressions_name,
        lake_polygons_name, depressions_no_lakes_name)

    depressions_no_lakes_task.addSubTask(vectorize_raster_task, [],
                                         QgsTask.ParentDependsOnSubTask)
    depressions_no_lakes_task.addSubTask(load_lakes_task, [],
                                         QgsTask.ParentDependsOnSubTask)

    dissolve = CollectGeometriesTask("Merging overlapping depressions", depressions_no_lakes_name, depressions_path)

    dissolve.addSubTask(depressions_no_lakes_task, [],
                                     QgsTask.ParentDependsOnSubTask)

    QgsApplication.taskManager().addTask(dissolve)

    # Setup the event loop to wait for tasks to finish
    loop = QEventLoop()
    QgsApplication.taskManager().allTasksFinished.connect(loop.quit)
    loop.exec_()

    # Cleanup QGIS application
    qgs.exitQgis()


if __name__ == "__main__":
    output_file_name = f"{config_analysis['depressions'].split('.', 1)[0]}_output.txt"
    cProfile.run('main()', output_file_name)
    p = pstats.Stats(output_file_name)
    p.sort_stats('cumulative').print_stats(10)
