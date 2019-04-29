from django.test import TestCase

from django_fsm import ConcurrentTransition
from testapp.models import LockedBlogPost, ExtendedBlogPost


class TestLockMixin(TestCase):
    def test_create_succeed(self):
        LockedBlogPost.objects.create(text='test_create_succeed')

    def test_crud_succeed(self):
        post = LockedBlogPost(text='test_crud_succeed')
        post.publish()
        post.save()

        post = LockedBlogPost.objects.get(pk=post.pk)
        self.assertEqual('published', post.state)
        post.text = 'test_crud_succeed2'
        post.save()

        post = LockedBlogPost.objects.get(pk=post.pk)
        self.assertEqual('test_crud_succeed2', post.text)

    def test_save_and_change_succeed(self):
        post = LockedBlogPost(text='test_crud_succeed')
        post.publish()
        post.save()

        post.remove()
        post.save()

    def test_concurent_modifications_raise_exception(self):
        post1 = LockedBlogPost.objects.create()
        post2 = LockedBlogPost.objects.get(pk=post1.pk)

        post1.publish()
        post1.save()

        post2.text = 'aaa'
        post2.publish()
        with self.assertRaises(ConcurrentTransition):
            post2.save()

    def test_inheritance_crud_succeed(self):
        post = ExtendedBlogPost(text='test_inheritance_crud_succeed', notes='reject me')
        post.publish()
        post.save()

        post = ExtendedBlogPost.objects.get(pk=post.pk)
        self.assertEqual('published', post.state)
        post.text = 'test_inheritance_crud_succeed2'
        post.reject()
        post.save()

        post = ExtendedBlogPost.objects.get(pk=post.pk)
        self.assertEqual('rejected', post.review_state)
        self.assertEqual('test_inheritance_crud_succeed2', post.text)
