from django.utils.translation import gettext_lazy

from . import __version__

try:
    from pretix.base.plugins import PluginConfig
except ImportError:
    raise RuntimeError("Please use pretix 2.7 or above to run this plugin!")


class OrangeMoneyMadagascarPluginApp(PluginConfig):
    default = True
    name = "pretix_orange_money_mdg"
    verbose_name = "Orange Money Madagascar"

    class PretixPluginMeta:
        name = gettext_lazy("Orange Money Madagascar")
        author = "Mika Andrianarijaona"
        description = gettext_lazy("Orange Money Madagascar payment processor plugin")
        visible = True
        version = __version__
        category = "PAYMENT"
        compatibility = "pretix>=2.7.0"

    def ready(self):
        from . import signals  # NOQA
