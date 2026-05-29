import tempfile
import unittest
from pathlib import Path

from retail_algorithm.src.retail_algo.data_io import load_json
from retail_algorithm.src.retail_algo.pipeline import run_pipeline


class PipelineTest(unittest.TestCase):
    def test_pipeline_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = load_json("retail_algorithm/configs/default.json")
            config["output_dir"] = tmp
            summary = run_pipeline(config)

            self.assertGreater(summary["customers"], 0)
            self.assertGreater(summary["products"], 0)
            self.assertGreater(summary["rfm_rows"], 0)
            self.assertGreater(summary["cluster_rows"], 0)
            self.assertGreater(summary["multibehavior_recommendations"], 0)
            self.assertTrue((Path(tmp) / "rfm_segments.csv").exists())
            self.assertTrue((Path(tmp) / "cluster_segments.csv").exists())
            self.assertTrue((Path(tmp) / "association_rules.csv").exists())
            self.assertTrue((Path(tmp) / "multibehavior_recommendations.csv").exists())
            self.assertTrue((Path(tmp) / "evaluation_metrics.json").exists())


if __name__ == "__main__":
    unittest.main()
