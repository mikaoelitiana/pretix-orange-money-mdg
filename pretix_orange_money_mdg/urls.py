from django.urls import include, re_path

from .views import (
    abort,
    redirect_view,
    success,
)

event_patterns = [
    re_path(
        r"^oramge_money_mdg/",
        include(
            [
                re_path(r"^abort/$", abort, name="abort"),
                re_path(r"^return/$", success, name="return"),
                re_path(r"^redirect/$", redirect_view, name="redirect"),
            ]
        ),
    ),
]
