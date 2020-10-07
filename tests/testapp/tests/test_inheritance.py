from collections import namedtuple
from enum import Enum
from functools import total_ordering

import inflection
from django.db import models
from django.test import TestCase
from django.utils.translation import gettext_lazy as _
from django_fsm import FSMField, can_proceed, transition


class AbstractOrder(models.Model):
    """
    Test abstract inheritance for Order workflow
    """

    @total_ordering
    class STATE(namedtuple("State", "human_readable path order_in_path description"), Enum):
        DRAFT = "Draft", "happy", 1, "Anything that is not sent to vendor"
        PENDING_VENDOR = (
            "Pending Vendor",
            "happy",
            2,
            "Anything that is in vendor inbox",
        )

        @staticmethod
        def _model_name():
            """
            use a static method instead of class or static attribute because Enum auto treats those as
            members and if use _ignore_ it will not be available via STATE.ModelName
            """
            return "Order"

        @classmethod
        def as_state_choices(cls, base_model_name=None):
            """
            get all members inside an iterable of 3-tuples
            where the 1st is the database value and 2nd is the human-readable display
            and 3rd is the proxy_model

            Note that this follows the conventions of Django choices in
            https://github.com/viewflow/django-fsm/blob/master/tests/testapp/tests/test_state_transitions.py
            """
            if base_model_name is None:
                base_model_name = cls._model_name()

            return [
                (
                    member.db_value,
                    member.human_readable,
                    inflection.camelize(member.name.lower()) + base_model_name,
                )
                for _, member in cls.__members__.items()
            ]

        @property
        def db_value(self):
            """
            Opinionated decision to use the member name as the database value to store
            """
            return self.name

    @transition(
        field="state",
        source=[STATE.DRAFT.db_value],
        target=STATE.PENDING_VENDOR.db_value,
    )
    def transition_to_pending_vendor_via_abstract_class(self):
        """
        This function may contain side-effects,
        like updating caches, notifying users, etc.
        The return value will be discarded.

        But only when those side effects require pass in new info not avail in entity attributes
        """
        pass

    class Meta:
        abstract = True
        app_label = "testapp"


class InPersonOrder(AbstractOrder):

    state = FSMField(
        _("state"),
        state_choices=AbstractOrder.STATE.as_state_choices("InPersonOrder"),
        default=AbstractOrder.STATE.DRAFT.db_value,
    )

    class Meta:
        app_label = "testapp"

    @transition(
        field="state",
        source=[AbstractOrder.STATE.DRAFT.db_value],
        target=AbstractOrder.STATE.PENDING_VENDOR.db_value,
    )
    def transition_to_pending_vendor(self):
        """
        This function may contain side-effects,
        like updating caches, notifying users, etc.
        The return value will be discarded.

        But only when those side effects require pass in new info not avail in entity attributes
        """
        pass


class DraftInPersonOrder(InPersonOrder):
    class Meta:
        app_label = "testapp"
        proxy = True


class PendingVendorInPersonOrder(InPersonOrder):
    class Meta:
        app_label = "testapp"
        proxy = True


class OnlineOrder(AbstractOrder):

    state = FSMField(
        _("state"),
        state_choices=AbstractOrder.STATE.as_state_choices("OnlineOrder"),
        default=AbstractOrder.STATE.DRAFT.db_value,
    )

    @transition(
        field="state",
        source=[AbstractOrder.STATE.DRAFT.db_value],
        target=AbstractOrder.STATE.PENDING_VENDOR.db_value,
    )
    def transition_to_pending_vendor(self):
        """
        This function may contain side-effects,
        like updating caches, notifying users, etc.
        The return value will be discarded.

        But only when those side effects require pass in new info not avail in entity attributes
        """
        pass

    class Meta:
        app_label = "testapp"


class DraftOnlineOrder(OnlineOrder):
    class Meta:
        app_label = "testapp"
        proxy = True


class PendingVendorOnlineOrder(OnlineOrder):
    class Meta:
        app_label = "testapp"
        proxy = True


class Test(TestCase):
    def setUp(self):
        self.draft_online_order = DraftOnlineOrder.objects.create()

    def test_transition_from_draft_to_pending_vendor_via_abstract(self):
        """
        Check when the transition method is defined at abstract model correctly transitions
        """

        if not can_proceed(self.draft_online_order.transition_to_pending_vendor_via_abstract_class):
            raise Exception
        self.assertEqual(self.draft_online_order.state, AbstractOrder.STATE.DRAFT.db_value)
        self.assertTrue(isinstance(self.draft_online_order, DraftOnlineOrder))
        # transition is triggered by this @transition decorated method
        self.draft_online_order.transition_to_pending_vendor_via_abstract_class()
        self.assertEqual(self.draft_online_order.state, AbstractOrder.STATE.PENDING_VENDOR.db_value)
        # These two asserts should work
        self.assertTrue(isinstance(self.draft_online_order, PendingVendorOnlineOrder))
        self.assertFalse(isinstance(self.draft_online_order, PendingVendorInPersonOrder))
        # end of should work
        # End up these two faulty asserts pass instead
        self.assertFalse(isinstance(self.draft_online_order, PendingVendorOnlineOrder))
        self.assertTrue(isinstance(self.draft_online_order, PendingVendorInPersonOrder))
        # End of faulty asserts

    def test_transition_from_draft_to_pending_vendor_direct(self):
        """
        Check when the transition method is defined at abstract model correctly transitions
        """

        if not can_proceed(self.draft_online_order.transition_to_pending_vendor):
            raise Exception
        self.assertEqual(self.draft_online_order.state, AbstractOrder.STATE.DRAFT.db_value)
        self.assertTrue(isinstance(self.draft_online_order, DraftOnlineOrder))
        # transition is triggered by this @transition decorated method
        self.draft_online_order.transition_to_pending_vendor()
        self.assertEqual(self.draft_online_order.state, AbstractOrder.STATE.PENDING_VENDOR.db_value)
        # These two asserts should work  andthey do work
        self.assertTrue(isinstance(self.draft_online_order, PendingVendorOnlineOrder))
        self.assertFalse(isinstance(self.draft_online_order, PendingVendorInPersonOrder))
        # end of should work
