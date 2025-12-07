import json
from pathlib import Path
import re
from typing import List, Optional, Union, Any


class JsonHandler:
    """
    Class to handle json files
    """

    def load_json(self, file_path: Union[str, Path]) -> Any:
        """
        Load json file.

        Args:
          file_path (str): json file path.
        Returns:
          dict: dictionary loaded from json file.
        """
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data

    def save_json(self, data: Union[dict, List], file_path: Union[str, Path]):
        """
        Save json file.

        Args:
          data (dict): dictionary to be saved.
          file_path (str): json file path.
        """
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

    def get_json_files_by_pattern(
        self, dir_path: Path, pattern: Optional[str] = None
    ) -> List[str]:
        """
        Get a list of json file names in a directory.

        Args:
          dir_path (Path):  directory path in which json files are saved.
          pattern (Optional[str]): regular expression to filter json files.
        Returns:
          List[str]: list of json file names.
        """
        if not pattern:
            pattern = r"^.+\.json$"
        regex = re.compile(pattern)
        files = [
            f.name for f in dir_path.iterdir() if f.is_file() and regex.match(f.name)
        ]
        return files


JSON_HANDLER = JsonHandler()
