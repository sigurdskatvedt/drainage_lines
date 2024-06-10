from qgis.core import QgsProject, QgsVectorLayer
from .base_task import BaseTask
from dual_logger import log
import logging

import sys

sys.path.append('/usr/share/qgis/python/plugins/')

from qgis import processing


class LoadLayersTask(BaseTask):
    """
    This class is responsible for loading, optionally filtering, and merging vector layers from GML files.
    
    Attributes:
        description (str): The description of the task.
        gml_path (str): The base path to the GML file containing the layers.
        layer_names (list of str): The names of the layers to be loaded from the GML file.
        output_name (str): The name assigned to the merged output layer.
        expression (str, optional): The expression used to filter features🤽‍♂️ within the layers. Default is None.
    
    Methods:
        task: Loading, optionally filtering, and merging the specified layers into a single vector layer.
    """

    def __init__(self,
                 description,
                 gml_path,
                 layer_names,
                 output_name,
                 crs=None,
                 expression=None):
        super().__init__(description)
        self.gml_path = gml_path
        self.layer_names = [layer_names] if isinstance(layer_names,
                                                       str) else layer_names
        self.output_name = output_name
        self.crs = crs
        self.expression = expression
        self.merged_layer = None

    def task(self):
        selected_layers = []

        for name in self.layer_names:
            vector_layer = QgsVectorLayer(self.gml_path, name, "ogr")
            if (self.crs):
                params = {
                    'INPUT': f"{self.gml_path}|layername={name}",
                    'TARGET_CRS': self.crs,
                    'OUTPUT': "memory:"
                }

                vector_layer = processing.run("native:reprojectlayer",
                                              params)['OUTPUT']
                log(vector_layer.sourceCrs().toProj())

            if self.expression is not None:
                # Extract features based on the attribute value
                result = processing.run(
                    "native:extractbyexpression", {
                        'INPUT': vector_layer,
                        'EXPRESSION': self.expression,
                        'OUTPUT': 'memory:'
                    })
                vector_layer = result['OUTPUT']

            if not vector_layer.isValid() or vector_layer.featureCount() == 0:
                log(f"Layer {name} is not valid or has no features.",
                    level=logging.ERROR)
                continue

            selected_layers.append(vector_layer)

        if selected_layers:
            if len(selected_layers) > 1:
                # Merge the layers that have passed the filtering
                self.merged_layer = processing.run(
                    "native:mergevectorlayers", {
                        'LAYERS': selected_layers,
                        'OUTPUT': 'memory:'
                    })['OUTPUT']
            else:
                self.merged_layer = selected_layers[0]

            if not self.merged_layer.isValid():
                log("Failed to merge layers into a valid layer.",
                    level=logging.ERROR)
                return False

            self.merged_layer.setName(self.output_name)
            QgsProject.instance().addMapLayer(self.merged_layer)
            log(f"Successfully merged layers into {self.output_name}",
                level=logging.INFO)
            return True
        else:
            log("No layers with features to merge after applying attribute filter.",
                level=logging.WARNING)
            return False
