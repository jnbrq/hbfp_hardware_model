import os
from typing import Callable, Dict, List, Optional, Union
from analyze_reports import read_area_data
from modules import Module
import pickle


class AreaDatabase:
    def __init__(self, dirpath: Optional[str] = None, force_rebuild: bool = False) -> None:
        self._data: Dict[Module, float] = {}
        self._on_miss: List[Callable[[Module], Union[float, None]]] = []

        if dirpath is not None:
            if not force_rebuild and os.path.exists(f"{dirpath}/cache.pickle"):
                print(f"Loading database from {dirpath}/cache.pickle")
                self.pickle_load(f"{dirpath}/cache.pickle")
            else:
                print(f"Rebuilding database")
                self.build_from(dirpath)
                self.pickle_save(f"{dirpath}/cache.pickle")

    def build_from(self, dirpath: str) -> None:
        entries = [x for x in os.listdir(
            dirpath) if os.path.isdir(f"{dirpath}/{x}")]
        for entry in entries:
            print(f"Found directory: {entry}")
            module = Module.from_string(entry)
            module_name = type(module).__name__
            print(f"    Instantiated module: {entry}")
            with open ( f"{dirpath}/{entry}/RPT/{module_name}/area.log") as f:
                area = read_area_data(f)[module_name]["global/absolute"]
            self._data[module] = area

    def pickle_load(self, fpath: str) -> None:
        with open(fpath, "rb") as f:
            self._data.update(pickle.load(f))

    def pickle_save(self, fpath: str) -> None:
        with open(fpath, "wb") as f:
            pickle.dump(self._data, f)
    
    def add_on_miss(self, on_miss: Callable[[Module], Union[float, None]]) -> None:
        self._on_miss.append(on_miss)
    
    def add(self, m: Module, area: float) -> None:
        self._data[m] = area

    def __call__(self, m: Module) -> float:
        r = self._data.get(m, None)
        if r is None:
            for on_miss in self._on_miss:
                r = on_miss(m)
                if r is not None:
                    self.add(m, r)
                    return r
            return None
        else:
            return r
    
    def data(self) -> Dict[Module, float]:
        return self._data
