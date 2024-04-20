from qgis.core import QgsProcessingFeedback, QgsProject
import processing
from .base_task import BaseTask
from dual_logger import log
from variables import saving_folder
import logging


class FindTouchingPolygonsTask(BaseTask):
    def __init__(self, description, output_layer_name, primary_layer_name, touching_layer_name):
        super().__init__(description, output_layer_name)
        self.primary_layer_name = primary_layer_name
        self.touching_layer_name = touching_layer_name
        self.joined_layer = None

    def task(self):
        project = QgsProject.instance()
        mapLayers = project.mapLayers().values()
        print("Maplayers: ", mapLayers)

        primary_layer = None
        touching_layer = None

        # Search for the layers by name
        for layer in mapLayers:
            if layer.name() == self.primary_layer_name:
                primary_layer = layer
            elif layer.name() == self.touching_layer_name:
                touching_layer = layer

        if not primary_layer or not touching_layer:
            log(f'Could not find layers with names {self.primary_layer_name} and {self.touching_layer_name}', level=logging.ERROR)
            return False

        log(f'Task "{self.description()}" starting, inputs are {primary_layer.name()} and {touching_layer.name()}', level=logging.INFO)

        params = {
            'INPUT': primary_layer,
            'JOIN': touching_layer,
            'PREDICATE': [0],  # Touches
            'METHOD': 1,
            'DISCARD_NONMATCHING': True,
            'PREFIX': '',
            'OUTPUT': f'{saving_folder}{self.output_name}.gml'
        }
        feedback = QgsProcessingFeedback()
        try:
            result = processing.run("native:joinattributesbylocation", params, feedback=feedback)
            self.output = result['OUTPUT']
            log(f'Completed task "{self.description()}", joined {result["JOINED_COUNT"]} features', level=logging.INFO)
            return True
        except Exception as e:
            log(f'Error in task "{self.description()}": {e}', level=logging.ERROR)
            return False
