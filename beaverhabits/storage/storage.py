from .utils import (
    print_error,
    print_success,
    print_info,
    print_step,
    print_debug,
    print_warning,
)
from .loader import Loader, run_with_loader
import unittest
from unittest.mock import patch, MagicMock

__all__ = [
    "print_error",
    "print_success",
    "print_info",
    "print_step",
    "print_debug",
    "print_warning",
    "Loader",
    "run_with_loader",
]


class TestLoader(unittest.TestCase):
    @patch("click.echo")
    def test_loader_start_and_stop(self, mock_echo):
        loader = Loader()
        loader.start()
        loader.stop()
        self.assertTrue(mock_echo.called)

    @patch("click.echo")
    def test_run_with_loader(self, mock_echo):
        def mock_function():
            return "Result"

        result = run_with_loader(mock_function)
        self.assertEqual(result, "Result")
        self.assertTrue(mock_echo.called)


class TestClientRetrieval(unittest.TestCase):
    def test_client_retrieval_success(self):
        with patch(
            "your_module.retrieve_client", return_value=MagicMock()
        ) as mock_retrieve:
            client = retrieve_client()
            mock_retrieve.assert_called_once()
            self.assertIsNotNone(client)

    def test_client_retrieval_failure(self):
        with patch(
            "your_module.retrieve_client",
            side_effect=Exception("Failed to retrieve client"),
        ) as mock_retrieve:
            try:
                retrieve_client()
            except Exception as e:
                mock_retrieve.assert_called_once()
                print_error(str(e))

