from django.urls import include, re_path

from .views import (
    abort,
    notify,
    success,
)

event_patterns = [
    re_path(
        r"^oramge_money_mdg/",
        include(
            [
                re_path(r"^abort/$", abort, name="abort"),
                re_path(r"^success/$", success, name="success"),
                re_path(r"^notify/$", notify, name="notify"),
            ]
        ),
    ),
]
