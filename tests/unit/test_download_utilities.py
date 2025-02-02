""" Unit tests for the `harmony_netcdf_to_zarr.download_utilities` module. """
from logging import getLogger
from os import remove as remove_file
from os.path import dirname, exists as file_exists, join as join_path
from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp
from unittest import TestCase

from harmony.util import config

from harmony_netcdf_to_zarr.download_utilities import download_granules


class TestDownloadUtilities(TestCase):
    @classmethod
    def setUpClass(cls):
        """ Set test fixtures that can be defined once for all tests. """
        cls.access_token = 'access'
        cls.harmony_config = config(validate=False)
        cls.logger = getLogger('test')

        # `harmony.util.download` needs local files to have 'file://' prefix:
        cls.test_path = dirname(__file__)
        cls.netcdf_urls = [
            f'file://{join_path(cls.test_path, "data_one.nc4")}',
            f'file://{join_path(cls.test_path, "data_two.nc4")}',
            f'file://{join_path(cls.test_path, "data_three.nc4")}'
        ]
        cls.local_paths = [netcdf_url.replace('file://', '')
                           for netcdf_url in cls.netcdf_urls]

    def setUp(self):
        """ Set test fixtures the should be reset between tests. """
        self.temp_dir = mkdtemp()
        for local_path in self.local_paths:
            Path(local_path).touch()

    def tearDown(self):
        """ Remove test-specific items, for example temporary files. """
        for local_path in self.local_paths:
            if file_exists(local_path):
                remove_file(local_path)

        rmtree(self.temp_dir)

    def test_download_granules_successful(self):
        """ Check that a request to download all files returns the local paths
            from all workers, if all downloads complete successfully.

        """
        # Convert output to set, as order may not be preserved:
        self.assertSetEqual(
            set(download_granules(self.netcdf_urls, self.temp_dir,
                                  self.access_token, self.harmony_config,
                                  self.logger)),
            set(self.local_paths)
        )

    def test_download_granules_failure(self):
        """ Check that a RuntimeError is raises, as expected, if there is an
            error downloading one of the granules. In this test, the error will
            be caused by requesting a file with an unknown protocol.

            The `RuntimeError` that is raised should also preserve the message
            from the exception that was raised within the child process.

        """
        with self.assertRaises(RuntimeError) as context_manager:
            download_granules(['unknown_protocol_file.nc4'], self.temp_dir,
                              self.access_token, self.harmony_config,
                              self.logger)

            self.assertTrue(str(context_manager.exception).startswith(
                'Unable to download a url of unknown type'
            ))
