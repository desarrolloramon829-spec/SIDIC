"""
Modelos del dominio S.I.D.I.C.

Exporta todos los modelos para uso conveniente:
    from sidic.domain.models import CrimeRecord, MentionedPerson, Apprehended
"""

from sidic.domain.models.crime_record import CrimeRecord
from sidic.domain.models.mentioned_person import MentionedPerson
from sidic.domain.models.apprehended import Apprehended
from sidic.domain.models.report_data import PeriodData, ReportData, MAX_PERIODOS
from sidic.domain.models.simbolo_delito import SimboloDelito

__all__ = [
    "Apprehended",
    "CrimeRecord",
    "MAX_PERIODOS",
    "MentionedPerson",
    "PeriodData",
    "ReportData",
    "SimboloDelito",
]
