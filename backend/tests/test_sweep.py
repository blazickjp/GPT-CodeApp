import subprocess
import unittest


class TestSweep(unittest.TestCase):
    def test_pytest_command(self):
        result = subprocess.run(["pytest"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        self.assertEqual(result.returncode, 0)
        self.assertIn("collected", result.stdout.decode())
        self.assertIn("passed", result.stdout.decode())
        self.assertNotIn("ERROR", result.stdout.decode())
        self.assertNotIn("FAILED", result.stdout.decode())


if __name__ == "__main__":
    unittest.main()
