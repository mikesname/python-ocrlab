"""Asyncronous tasks, run with Celery."""

import json
from celery import task

from ocrlab import models, nodes, stages

from nodetree import script


class OcrTask(task.Task):
    name = "ocrlab.OcrTask"

    def run(self, preset_id, filepath):
        preset = models.Preset.objects.get(pk=preset_id)
        with open(filepath, "r") as handle:
            return self.run_preset(preset, handle)

    @classmethod
    def run_preset(cls, preset, handle):
        """Run a preset on the given handle."""
        s = script.Script(json.loads(preset.data))
        s = cls._set_script_input(s, handle)
        term = s.get_terminals()[0]
        return term.eval()

    @classmethod
    def _set_script_input(cls, tree, handle):
        """Modify the given script for a specific file."""
        # get the input node and replace it with out path
        input = tree.get_nodes_by_attr("stage", stages.INPUT)[0]
        input.set_param("path", handle)
        return tree


