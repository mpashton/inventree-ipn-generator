import logging

from django.core.exceptions import ValidationError
from part.models import Part
from plugin import InvenTreePlugin
from plugin.mixins import EventMixin, SettingsMixin
from . import ipn_pattern

logger = logging.getLogger("inventree")


def validate_pattern(pattern):
    """Validates pattern groups"""
    regex = re.compile(r"(\{\d+\+?\})|(\[(?!\w\])(?:\w+|(?:\w-\w)+)+\])")
    if not regex.search(pattern):
        raise ValidationError("Pattern must include more than Literals")

    return True


class AutoGenIPNPlugin(EventMixin, SettingsMixin, InvenTreePlugin):
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

    def wants_process_event(self, event):
        """Lets InvenTree know what events to listen for."""

        if not self.get_setting("ACTIVE"):
            return False

        return event == "part_part.saved" or (
            event == "part_part.created" and self.get_setting("ON_CREATE")
        )

    def is_ipn_unique(self, ipn, exclude_pk=None):
        qs = Part.objects.filter(IPN__iexact=ipn)
        if exclude_pk is not None:
            qs = qs.exclude(pk=exclude_pk)
        return not qs.exists()

    def find_unique_ipn(self, pattern):
        ipn = ipn_pattern.IPN(pattern)
        while 1:
            ipns = str(ipn)
            if self.is_ipn_unique(ipns):
                return ipns
            ipn.inc()

    def process_event(self, event, *args, **kwargs):
        """Main plugin handler function"""

        #logger.warning(f"ipn_generator handling event: {event}")
        if not self.get_setting("ACTIVE"):
            return False

        id = kwargs.pop("id", None)
        model = kwargs.pop("model", None)

        # Events can fire on unrelated models
        if model != "Part":
            logger.warning("IPN Generator: Event Model is not part")
            return

        if event.endswith(".deleted"):
            logger.warning("IPN Generator: Event part deleted")
            return

        # Don't create IPNs for parts with IPNs
        part = Part.objects.get(id=id)
        #logger.warning(f"ipn generator: part: {part} / part.IPN: {part.IPN}")
        # but always regenerate if the IPN field is auto
        regen = False
        if part.IPN == "auto":
            regen = True
        elif (
            (event == "part_part.saved" and self.get_setting("ON_CHANGE"))
            or (event == "part_part.created" and self.get_setting("ON_CREATE"))
        ):
            if part.IPN is None or part.IPN == "":
                regen = True
        
        if not regen:
            return

        pattern = self.get_pattern_for_part(part)
        part.IPN = self.find_unique_ipn(pattern)
        part.save()

        return

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

        return pattern

