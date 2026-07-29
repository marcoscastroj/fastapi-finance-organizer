from slowapi import Limiter
from slowapi.util import get_remote_address

# Instância global do Limiter isolada de ciclos de importação
limiter = Limiter(key_func=get_remote_address)