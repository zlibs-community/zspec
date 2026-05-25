"""ZSpec — a specification pattern library for Python."""

from zspec.explain import (
    ExplainNode as ExplainNode,
)
from zspec.explain import (
    explain as explain,
)
from zspec.specification import (
    AndSpecification as AndSpecification,
)
from zspec.specification import (
    NotSpecification as NotSpecification,
)
from zspec.specification import (
    OrSpecification as OrSpecification,
)
from zspec.specification import (
    Specification as Specification,
)
from zspec.specification import (
    XorSpecification as XorSpecification,
)
from zspec.translator import (
    Translator as Translator,
)
from zspec.translators import (
    MongoTranslator as MongoTranslator,
)
from zspec.translators import (
    SqlFragment as SqlFragment,
)
from zspec.translators import (
    SqlTranslator as SqlTranslator,
)
