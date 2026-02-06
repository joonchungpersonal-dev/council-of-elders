"""Elder management and profiles."""

from council.elders.base import Elder, ElderRegistry
from council.elders.profiles.munger import MungerElder
from council.elders.profiles.aurelius import AureliusElder
from council.elders.profiles.franklin import FranklinElder
from council.elders.profiles.buffett import BuffettElder
from council.elders.profiles.bruce_lee import BruceLeeElder
from council.elders.profiles.musashi import MusashiElder
from council.elders.profiles.sun_tzu import SunTzuElder
from council.elders.profiles.buddha import BuddhaElder
from council.elders.profiles.branden import BrandenElder
from council.elders.profiles.kabatzinn import KabatZinnElder
from council.elders.profiles.clear import ClearElder
from council.elders.profiles.greene import GreeneElder
from council.elders.profiles.naval import NavalElder
from council.elders.profiles.rubin import RubinElder
from council.elders.profiles.oprah import OprahElder
from council.elders.profiles.thich import ThichElder
from council.elders.profiles.jung import JungElder
from council.elders.profiles.laotzu import LaoTzuElder
from council.elders.profiles.davinci import DaVinciElder
from council.elders.profiles.kahneman import KahnemanElder
from council.elders.profiles.tubman import TubmanElder
from council.elders.profiles.tetlock import TetlockElder
from council.elders.profiles.klein import KleinElder
from council.elders.profiles.meadows import MeadowsElder
from council.elders.profiles.hannibal import HannibalElder
from council.elders.profiles.boudicca import BoudiccaElder
from council.elders.profiles.genghis import GenghisElder
from council.elders.profiles.lauder import LauderElder

# Register built-in elders
ElderRegistry.register(MungerElder())
ElderRegistry.register(AureliusElder())
ElderRegistry.register(FranklinElder())
ElderRegistry.register(BuffettElder())
ElderRegistry.register(BruceLeeElder())
ElderRegistry.register(MusashiElder())
ElderRegistry.register(SunTzuElder())
ElderRegistry.register(BuddhaElder())
ElderRegistry.register(BrandenElder())
ElderRegistry.register(KabatZinnElder())
ElderRegistry.register(ClearElder())
ElderRegistry.register(GreeneElder())
ElderRegistry.register(NavalElder())
ElderRegistry.register(RubinElder())
ElderRegistry.register(OprahElder())
ElderRegistry.register(ThichElder())
ElderRegistry.register(JungElder())
ElderRegistry.register(LaoTzuElder())
ElderRegistry.register(DaVinciElder())
ElderRegistry.register(KahnemanElder())
ElderRegistry.register(TubmanElder())
ElderRegistry.register(TetlockElder())
ElderRegistry.register(KleinElder())
ElderRegistry.register(MeadowsElder())
ElderRegistry.register(HannibalElder())
ElderRegistry.register(BoudiccaElder())
ElderRegistry.register(GenghisElder())
ElderRegistry.register(LauderElder())

__all__ = [
    "Elder",
    "ElderRegistry",
    "MungerElder",
    "AureliusElder",
    "FranklinElder",
    "BuffettElder",
    "BruceLeeElder",
    "MusashiElder",
    "SunTzuElder",
    "BuddhaElder",
    "BrandenElder",
    "KabatZinnElder",
    "ClearElder",
    "GreeneElder",
    "NavalElder",
    "RubinElder",
    "OprahElder",
    "ThichElder",
    "JungElder",
    "LaoTzuElder",
    "DaVinciElder",
    "KahnemanElder",
    "TubmanElder",
    "TetlockElder",
    "KleinElder",
    "MeadowsElder",
    "HannibalElder",
    "BoudiccaElder",
    "GenghisElder",
    "LauderElder",
]
