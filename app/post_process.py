import cProfile
import pstats
import sys
import json
from tasks.classify_flow_task import ClassifyFlowTask
from tasks.raster_to_int_task import RasterToIntTask
from tasks.thin_task import ThinRasterTask
from tasks.vectorize_grass_task import GrassRasterToVectorTask
from tasks.douglaspeucker_task import DouglasPeuckerTask
from tasks.smooth_geometries_task import SmoothGeometriesTask
from tasks.save_layer_task import SaveLayerToFileTask
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
config_flows = load_paths_from_config('paths/os/paths_flows.json')
config_external = load_paths_from_config('paths/os/paths_external.json')


def main():
    # Initialize the project instance
    project = QgsProject.instance()
    project.clear()  # Clear any existing project data

    project_crs = config_external['crs']
    crs = QgsCoordinateReferenceSystem()
    crs.createFromString(project_crs)
    project.setCrs(crs)

    classify_task = ClassifyFlowTask("Classifying flow accumulation raster",
                                     config_flows['flow'],
                                     config_flows['flow_classified'])

    transform_task = RasterToIntTask("Transforming raster to Int16",
                                     config_flows['flow_classified'],
                                     config_flows['flow_classified_integer'])

    transform_task.addSubTask(classify_task, [],
                              QgsTask.ParentDependsOnSubTask)

    thin_task = ThinRasterTask("Thinning raster",
                               config_flows['flow_classified_integer'],
                               config_flows['flow_classified_thinned'],
                               "thinned")

    thin_task.addSubTask(transform_task, [], QgsTask.ParentDependsOnSubTask)

    vector_task = GrassRasterToVectorTask(
        "Converting raster to vector", config_flows['flow_classified_thinned'],
        config_flows['flow_channels_raw'])

    vector_task.addSubTask(thin_task, [], QgsTask.ParentDependsOnSubTask)

    douglaspeucker_task = DouglasPeuckerTask(
        "Simplifying geometries", config_flows['flow_channels_raw'],
        config_flows['flow_channels_simplified'])

    douglaspeucker_task.addSubTask(vector_task, [],
                                   QgsTask.ParentDependsOnSubTask)

    smooth_task = SmoothGeometriesTask(
        "Smoothing geometries", config_flows['flow_channels_simplified'],
        config_flows['flow_channels'])

    smooth_task.addSubTask(douglaspeucker_task, [],
                           QgsTask.ParentDependsOnSubTask)

    QgsApplication.taskManager().addTask(smooth_task)

    # Setup the event loop to wait for tasks to finish
    loop = QEventLoop()
    QgsApplication.taskManager().allTasksFinished.connect(loop.quit)
    loop.exec_()

    # Cleanup QGIS application
    qgs.exitQgis()


if __name__ == "__main__":
    output_file_name = f"{config_flows['flow_classified'].split('.', 1)[0]}_output.txt"
    cProfile.run('main()', output_file_name)
    p = pstats.Stats(output_file_name)  # not sure if works
    p.sort_stats('cumulative').print_stats(10)
