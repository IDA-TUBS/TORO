#!/usr/bin/env python
# -*- coding: utf-8 -*- 
from abc import ABC, abstractmethod
from typing import Dict, List, Union, Tuple

from pycpa import model
from .. import model as toroModel

class ModelParser(ABC):
    """ """

    def __init__(self, args, file_name:str):
        """ constructor """
        self.system = None
        self.chains = list()

    @abstractmethod
    def parse(self, folder:str) -> Tuple[model.System, List[toroModel.extEffectChain]]:
        """ process a complete system description model """
        pass

    @abstractmethod
    def _get_tasks(self) -> None:
        """ retrieve all tasks from the system description model """
        pass

    @abstractmethod
    def _get_resources(self) -> None:
        """ retrieve all resources from the system description model """
        pass

    # @abstractmethod
    # def _get_taskMapping(self):
    #     """ """
    #     pass

    @abstractmethod
    def _get_chains(self) -> None:
        """ retrieve all cause-effect chains from the system description model """
        pass



