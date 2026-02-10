"""Elder management and profiles."""

from council.elders.base import Elder, ElderRegistry, NominatedElder
from council.elders.custom import CustomElder, load_custom_elders

# Historical / IP-safe elders
from council.elders.profiles.aurelius import AureliusElder
from council.elders.profiles.boudicca import BoudiccaElder
from council.elders.profiles.branden import BrandenElder
from council.elders.profiles.buddha import BuddhaElder
from council.elders.profiles.davinci import DaVinciElder
from council.elders.profiles.franklin import FranklinElder
from council.elders.profiles.genghis import GenghisElder
from council.elders.profiles.hannibal import HannibalElder
from council.elders.profiles.jung import JungElder
from council.elders.profiles.laotzu import LaoTzuElder
from council.elders.profiles.meadows import MeadowsElder
from council.elders.profiles.musashi import MusashiElder
from council.elders.profiles.sun_tzu import SunTzuElder
from council.elders.profiles.tubman import TubmanElder

# New replacement elders (IP-safe historical figures)
from council.elders.profiles.bacon import BaconElder
from council.elders.profiles.dogen import DogenElder
from council.elders.profiles.epicurus import EpicurusElder
from council.elders.profiles.graham import GrahamElder
from council.elders.profiles.machiavelli import MachiavelliElder
from council.elders.profiles.rumi import RumiElder
from council.elders.profiles.seneca import SenecaElder
from council.elders.profiles.sojourner_truth import SojournerTruthElder
from council.elders.profiles.thucydides import ThucydidesElder
from council.elders.profiles.walker import WalkerElder
from council.elders.profiles.william_james import WilliamJamesElder

# Expansion: 20 new historical elders
from council.elders.profiles.hypatia import HypatiaElder
from council.elders.profiles.newton import NewtonElder
from council.elders.profiles.curie import CurieElder
from council.elders.profiles.darwin import DarwinElder
from council.elders.profiles.socrates import SocratesElder
from council.elders.profiles.aristotle import AristotleElder
from council.elders.profiles.confucius import ConfuciusElder
from council.elders.profiles.weil import WeilElder
from council.elders.profiles.douglass import DouglassElder
from council.elders.profiles.wollstonecraft import WollstonecraftElder
from council.elders.profiles.khayyam import KhayyamElder
from council.elders.profiles.cleopatra import CleopatraElder
from council.elders.profiles.ashoka import AshokaElder
from council.elders.profiles.nzinga import NzingaElder
from council.elders.profiles.adam_smith import AdamSmithElder
from council.elders.profiles.ibn_khaldun import IbnKhaldunElder
from council.elders.profiles.hildegard import HildegardElder
from council.elders.profiles.hippocrates import HippocratesElder
from council.elders.profiles.tesla import TeslaElder
from council.elders.profiles.tagore import TagoreElder

# Register built-in elders
ElderRegistry.register(AureliusElder())
ElderRegistry.register(BoudiccaElder())
ElderRegistry.register(BrandenElder())
ElderRegistry.register(BuddhaElder())
ElderRegistry.register(DaVinciElder())
ElderRegistry.register(FranklinElder())
ElderRegistry.register(GenghisElder())
ElderRegistry.register(HannibalElder())
ElderRegistry.register(JungElder())
ElderRegistry.register(LaoTzuElder())
ElderRegistry.register(MeadowsElder())
ElderRegistry.register(MusashiElder())
ElderRegistry.register(SunTzuElder())
ElderRegistry.register(TubmanElder())

# New replacement elders
ElderRegistry.register(BaconElder())
ElderRegistry.register(DogenElder())
ElderRegistry.register(EpicurusElder())
ElderRegistry.register(GrahamElder())
ElderRegistry.register(MachiavelliElder())
ElderRegistry.register(RumiElder())
ElderRegistry.register(SenecaElder())
ElderRegistry.register(SojournerTruthElder())
ElderRegistry.register(ThucydidesElder())
ElderRegistry.register(WalkerElder())
ElderRegistry.register(WilliamJamesElder())

# Expansion elders
ElderRegistry.register(HypatiaElder())
ElderRegistry.register(NewtonElder())
ElderRegistry.register(CurieElder())
ElderRegistry.register(DarwinElder())
ElderRegistry.register(SocratesElder())
ElderRegistry.register(AristotleElder())
ElderRegistry.register(ConfuciusElder())
ElderRegistry.register(WeilElder())
ElderRegistry.register(DouglassElder())
ElderRegistry.register(WollstonecraftElder())
ElderRegistry.register(KhayyamElder())
ElderRegistry.register(CleopatraElder())
ElderRegistry.register(AshokaElder())
ElderRegistry.register(NzingaElder())
ElderRegistry.register(AdamSmithElder())
ElderRegistry.register(IbnKhaldunElder())
ElderRegistry.register(HildegardElder())
ElderRegistry.register(HippocratesElder())
ElderRegistry.register(TeslaElder())
ElderRegistry.register(TagoreElder())

# Load persisted custom elders from ~/.council/elders/custom/
load_custom_elders()

__all__ = [
    "Elder",
    "ElderRegistry",
    "NominatedElder",
    "CustomElder",
    "AureliusElder",
    "BoudiccaElder",
    "BrandenElder",
    "BuddhaElder",
    "DaVinciElder",
    "FranklinElder",
    "GenghisElder",
    "HannibalElder",
    "JungElder",
    "LaoTzuElder",
    "MeadowsElder",
    "MusashiElder",
    "SunTzuElder",
    "TubmanElder",
    "BaconElder",
    "DogenElder",
    "EpicurusElder",
    "GrahamElder",
    "MachiavelliElder",
    "RumiElder",
    "SenecaElder",
    "SojournerTruthElder",
    "ThucydidesElder",
    "WalkerElder",
    "WilliamJamesElder",
    "HypatiaElder",
    "NewtonElder",
    "CurieElder",
    "DarwinElder",
    "SocratesElder",
    "AristotleElder",
    "ConfuciusElder",
    "WeilElder",
    "DouglassElder",
    "WollstonecraftElder",
    "KhayyamElder",
    "CleopatraElder",
    "AshokaElder",
    "NzingaElder",
    "AdamSmithElder",
    "IbnKhaldunElder",
    "HildegardElder",
    "HippocratesElder",
    "TeslaElder",
    "TagoreElder",
]
