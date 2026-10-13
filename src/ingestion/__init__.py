from ingestion.ipmp import get_ipmp_store
from ingestion.rio_manual import get_rio_manual_store
from ingestion.acronyms import get_acronym_store
from ingestion.retrieval_profile import get_retrieval_profile_store
from ingestion.dependencias import get_dependency_store
from ingestion.genre_exemptions import get_genre_exemption_store

__all__ = [
    "get_ipmp_store",
    "get_rio_manual_store",
    "get_acronym_store",
    "get_retrieval_profile_store",
    "get_dependency_store",
    "get_genre_exemption_store",
]
