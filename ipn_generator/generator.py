import logging
import re

from django.core.exceptions import ValidationError
from part.models import Part
from plugin import InvenTreePlugin
from plugin.mixins import SettingsMixin, ValidationMixin
from . import ipn_pattern

logger = logging.getLogger("inventree")


def validate_pattern(pattern):
    """Validates pattern groups"""
    regex = re.compile(r"(\{\d+\+?\})|(\[(?!\w\])(?:\w+|(?:\w-\w)+)+\])")
    if not regex.search(pattern):
        raise ValidationError("Pattern must include more than Literals")

    return True


class AutoGenIPNPlugin(ValidationMixin, SettingsMixin, InvenTreePlugin):
    """Plugin to generate IPN automatically"""

    AUTHOR = "Michael Ashton, Nichlas W., et al"
    DESCRIPTION = (
        "Plugin for automatically assigning IPN to parts created with empty IPN fields.\
        IPN pattern syntax can be found on the website linked here."
    )
    VERSION = "0.1"
    WEBSITE = "https://github.com/mpashton/inventree-ipn-generator"

    NAME = "IPNGenerator"
    SLUG = "ipngen"
    TITLE = "IPN Generator"

    SETTINGS = {
        "ACTIVE": {
            "name": "Active",
            "description": "IPN generator is active",
            "validator": bool,
            "default": True,
        },
        "ON_CREATE": {
            "name": "On Create",
            "description": "Active when creating new parts",
            "validator": bool,
            "default": True,
        },
        "ON_CHANGE": {
            "name": "On Edit",
            "description": "Active when editing existing parts",
            "validator": bool,
            "default": False,
        },
        "PATTERN": {
            "name": "IPN pattern",
            "description": "Pattern for IPN generation (See website for guide)",
            "default": "(IPN-){4}",
            "validator": validate_pattern,
        },
    }

    def is_ipn_unique(self, ipn, exclude_pk=None):
        qs = Part.objects.filter(IPN__iexact=ipn)
        if exclude_pk is not None:
            qs = qs.exclude(pk=exclude_pk)
        return not qs.exists()

    def find_unique_ipn(self, pattern, exclude_pk=None):
        ipn = ipn_pattern.IPN(pattern)
        while 1:
            ipns = str(ipn)
            if self.is_ipn_unique(ipns, exclude_pk=exclude_pk):
                return ipns
            ipn.inc()

    def validate_model_instance(self, instance, deltas=None):
        """Assign an IPN to a Part before it is written to the database.

        InvenTree (1.2+) calls this synchronously from Part.full_clean() and
        Part.save() via PluginValidationMixin, on the same instance the API
        serializes into its response, so the generated IPN is visible on the
        part page immediately. Never call save() here - the caller is saving.
        Return None (not True) so other validation plugins still run.
        """

        if not isinstance(instance, Part):
            return None

        if not self.get_setting("ACTIVE"):
            return None

        is_new = instance.pk is None or instance._state.adding

        # Always regenerate if the IPN field is "auto"
        regen = False
        if instance.IPN == "auto":
            regen = True
        elif instance.IPN is None or instance.IPN == "":
            if is_new:
                regen = bool(self.get_setting("ON_CREATE"))
            else:
                regen = bool(self.get_setting("ON_CHANGE"))

        if not regen:
            return None

        pattern = self.get_pattern_for_part(instance)
        instance.IPN = self.find_unique_ipn(pattern, exclude_pk=instance.pk)

        return None

    def get_pattern_for_part(self, part):
        """Return the pattern for a given part, applying category metadata overrides."""

        pattern = self.get_setting("PATTERN")

        if not part:
            return pattern

        category = getattr(part, "category", None)
        if not category:
            return pattern

        pattern = None
        pattern_param = category.get_parameter("IPN Pattern")
        if pattern_param:
            pattern = pattern_param.data
            logger.warning(f"pattern param for part '{part.id}' param: '{pattern}'")

        else:
            while category.parent is not None:
                category = category.parent
                pattern_param = category.get_parameter("IPN Pattern")
                if pattern_param:
                    pattern = pattern_param.data
                    break

        if not pattern:
            pattern = self.get_setting("PATTERN")

        return pattern

