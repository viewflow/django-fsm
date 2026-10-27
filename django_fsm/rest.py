# Copyright (c) 2017-2020, Mikhail Podgurskiy
# All Rights Reserved.

# This work is licensed under AGPL defined in file 'LICENSE' with the
# additional permissions of 'LICENSE_EXCEPTION', both part of this package.

from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.response import Response
from rest_framework.reverse import reverse
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from drf_spectacular.openapi import AutoSchema
from drf_spectacular.utils import extend_schema, inline_serializer
from .base import State, TransitionBoundMethod
from .chart import chart


class ChartSchema(AutoSchema):
    """Schema class for `chart/` response."""

    def _get_responses(self, path, method):
        return {
            "200": {
                "content": {
                    "application/json": {
                        "schema": {"properties": {"dot": {"type": "string"}}}
                    }
                },
            }
        }


class TransitionsSchema(AutoSchema):
    """Schema class for `transitions/` list response."""

    def _get_responses(self, path, method):
        transitions_data = {
            "type": "array",
            "items": {
                "properties": {
                    "label": {"type": "string"},
                    "conditions_met": {"type": "boolean"},
                    "has_permission": {"type": "boolean"},
                    "url": {"type": "string"},
                }
            },
        }

        return {
            "200": {
                "content": {
                    "application/json": {
                        "schema": {
                            "properties": {
                                "current_state": {"type": "object"},
                                "transitions": transitions_data,
                            }
                        }
                    }
                },
            }
        }


class FlowRESTMixin(object):
    """ModelViewSet mixing exposes transition methods."""

    flow_state: State

    def get_flow_state(self, request) -> State:
        return self.flow_state

    def get_object_flow(self, request, obj):
        owner = self.get_flow_state(request)._owner
        try:
            return owner(obj)
        except TypeError:
            raise ValueError(
                "%s has no constructor with single argument. Please "
                "redefine .get_object_flow(self, request, obj) on the "
                "model admin" % owner
            )

    def get_transition_fields(self, request, obj, slug):
        """Field names writable alongside a transition. Empty by default.

        A transition's `has_perm` only guards the state change itself;
        without this, any field writable by the viewset's serializer
        could be smuggled into a transition request regardless of the
        user's permission to change that field directly.
        """
        return []

    @extend_schema(
        responses={
            200: inline_serializer(
                name="Chart", fields={"dot": serializers.CharField()}
            )
        },
    )
    @action(methods=["GET"], detail=True, url_path="transition", schema=AutoSchema())
    def transitions(self, request, *args, **kwargs):
        obj = self.get_object()
        state = self.get_flow_state(request)
        flow = self.get_object_flow(request, obj)

        current_state = state.get(flow)

        def reverse_url(slug):
            if hasattr(request._request.resolver_match, "app"):
                app = request._request.resolver_match.app
                return app.reverse(f"{self.basename}-transition", args=[obj.pk, slug])
            else:
                namespace = request._request.resolver_match.namespace
                viewname = f"{self.basename}-transition"
                if namespace:
                    viewname = f"{namespace}:{viewname}"
                return reverse(
                    viewname,
                    args=[obj.pk, slug],
                    request=request,
                )

        return Response(
            {
                "current_state": current_state,
                "transitions": [
                    {
                        "label": transition.label,
                        "conditions_met": transition.conditions_met(flow),
                        "has_permission": transition.has_perm(flow, request.user),
                        "url": reverse_url(transition.slug),
                    }
                    for transition in state.get_outgoing_transitions(current_state)
                ],
            }
        )

    @extend_schema(
        responses={
            200: inline_serializer(
                name="Chart", fields={"dot": serializers.CharField()}
            )
        }
    )
    @action(methods=["GET"], detail=False, schema=AutoSchema())
    def chart(self, request, *args, **kwargs):
        state = self.get_flow_state(request)
        return Response({"dot": chart(state)})

    @action(
        methods=["POST"],
        detail=True,
        url_path="transition/(?P<slug>.+)",
        schema=AutoSchema(),
    )
    def transition(self, request, *args, **kwargs):
        slug = kwargs.get("slug")
        self.action = slug

        instance = self.get_object()
        flow = self.get_object_flow(request, instance)

        transition = getattr(flow, slug, None) if not slug.startswith("_") else None
        if not transition or not isinstance(transition, TransitionBoundMethod):
            raise ValidationError({"detail": _("Invalid transition")})

        if not transition.has_perm(request.user):
            raise PermissionDenied

        if not transition.can_proceed():
            raise ValidationError(_("Transition is not allowed"))

        transition_fields = self.get_transition_fields(request, instance, slug)
        data = {
            key: value
            for key, value in request.data.items()
            if key in transition_fields
        }
        serializer = self.get_serializer(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            self.perform_update(serializer)
            transition()

        if getattr(instance, "_prefetched_objects_cache", None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            # see: rest_framework.mixins.UpdateModelMixin:
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)
