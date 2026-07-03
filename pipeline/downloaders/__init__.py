from .sao_paulo import download as download_sao_paulo
from .rio_de_janeiro import download as download_rio_de_janeiro
from .belo_horizonte import download as download_belo_horizonte
from .porto_alegre import download as download_porto_alegre

DOWNLOADERS = {
    "sao_paulo":      download_sao_paulo,
    "rio_de_janeiro": download_rio_de_janeiro,
    "belo_horizonte": download_belo_horizonte,
    "porto_alegre":   download_porto_alegre,
}
