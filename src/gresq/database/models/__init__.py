from .sample import Sample
from .recipe import Recipe
from .author import Author
from .preparation_step import PreparationStep
from .properties import Properties
from .raman_file import RamanFile
from .raman_spectrum import RamanSpectrum
from .raman_set import RamanSet
from .sem_file import SemFile
from .sem_analysis import SemAnalysis
from .mdf_forge import MdfForge
from .software import Software

Recipe.maximum_temperature.info["verbose_name"] = "Maximum Temperature"
Recipe.maximum_temperature.info["verbose_name"] = "Maximum Temperature"
Recipe.maximum_temperature.info["std_unit"] = "C"

Recipe.maximum_pressure.info["verbose_name"] = "Maximum Pressure"
Recipe.maximum_pressure.info["std_unit"] = "Torr"

Recipe.maximum_temperature.info["verbose_name"] = "Maximum Temperature"
Recipe.maximum_temperature.info["std_unit"] = "C"

Recipe.average_carbon_flow_rate.info["verbose_name"] = "Average Carbon Flow Rate"
Recipe.average_carbon_flow_rate.info["std_unit"] = "sccm"

Recipe.carbon_source.info["verbose_name"] = "Carbon Source"
Recipe.carbon_source.info["std_unit"] = None

Recipe.uses_helium.info["verbose_name"] = "Uses Helium"
Recipe.uses_helium.info["std_unit"] = None

Recipe.uses_argon.info["verbose_name"] = "Uses Argon"
Recipe.uses_argon.info["std_unit"] = None

Recipe.uses_hydrogen.info["verbose_name"] = "Uses Hydrogen"
Recipe.uses_hydrogen.info["std_unit"] = None

Author.full_name_and_institution.info["verbose_name"] = "Author"
Author.full_name_and_institution.info["std_unit"] = None
