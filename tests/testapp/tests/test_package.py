"""Release checks for the independent django-fsm distribution."""

import io
import subprocess
import sys

from django.core.management import call_command
from django.test import SimpleTestCase
from django_fsm import Transition

from django_fsm.management.commands.graph_transitions import generate_dot
from .test_fsm__legacy_fields import DynamicLegacyJob


class PackageTests(SimpleTestCase):
    def test_legacy_metadata_has_consistent_name_hash(self):
        job = DynamicLegacyJob()
        item = next(iter(job.get_available_status_transitions()))
        expected = Transition(method=item.method, source=item.source, target=item.target)
        self.assertEqual(item, expected)
        self.assertEqual(hash(item), hash(expected))
        self.assertIn(expected, {item})

    def test_core_import_and_execution_need_no_settings_or_viewflow(self):
        code = """
import sys
import django_fsm as fsm
class Flow:
    state = fsm.State(None, default='new')
    @state.transition('new', 'done', conditions=[fsm.this.ready])
    def finish(self):
        pass
    def ready(self):
        return True
flow = Flow()
flow.finish()
assert flow.state == 'done'
assert not any(name.split('.')[0] in {'viewflow', 'rest_framework', 'drf_spectacular'} for name in sys.modules)
"""
        result = subprocess.run(
            [sys.executable, "-c", code], capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_graph_command_accepts_app_and_field_selection(self):
        for spec in ("testapp", "testapp.DynamicLegacyJob.status"):
            with self.subTest(spec=spec):
                output = io.StringIO()
                call_command("graph_transitions", spec, stdout=output)
                self.assertIn("digraph", output.getvalue())
                self.assertIn("running", output.getvalue())
                self.assertNotIn("GET_STATE(", output.getvalue())

    def test_graph_expands_dynamic_targets(self):
        field = DynamicLegacyJob._meta.get_field("status")
        dot = generate_dot([(field, DynamicLegacyJob)]).source
        self.assertIn("rejected", dot)
        self.assertIn("running", dot)
        self.assertIn("done", dot)
        self.assertNotIn("GET_STATE(", dot)
        self.assertNotIn("RETURN_VALUE(", dot)
