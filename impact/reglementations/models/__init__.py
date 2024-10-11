from .bdse import *  # noqa
from .csrd import *  # noqa
from .index_egapro import *  # noqa

# This uncommon structure of modules (included in a heigh-level package)
# can be useful for domains / apps with a big number of models and/or complex ones.
# BDSE models are "big ones".
# For backward compatibility, importing `reglementations.models` will import all sub-modules.
