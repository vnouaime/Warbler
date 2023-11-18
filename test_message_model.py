"""Message model tests."""

import os
from unittest import TestCase
from sqlalchemy.exc import IntegrityError

from models import db, User, Message, Follows

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app

class MessageModelTestCase(TestCase):
    """Test cases for Message model."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        u1 = User.signup(username="test123", password="test456", email="email1@gmail.com", image_url=None)
        u2 = User.signup(username="test789", password="test101112", email="email2@gmail.com", image_url=None)
        
        db.session.commit()

        m1 = Message(text="testing testing123", user_id=u1.id)
        m2 = Message(text="testing testing456", user_id=u2.id)

        db.session.commit()

        self.u1 = u1
        self.u2 = u2
        self.m1 = m1
        self.m2 = m2

        self.client = app.test_client()

    # Added tearDown function which should be included in each test case
    def tearDown(self): 
        """ Closes current session of database """ 
        res = super().tearDown()
        db.session.close()
        return res

    ##################################################################################
    def test_success_new_message(self):
        """Tests a successfull creation of a new message."""

        new_msg = Message(text="testing testing")
        self.u1.messages.append(new_msg)

        db.session.commit()

        self.assertEqual(len(self.u1.messages), 1)

    def test_fail_new_message(self):
        """Tests a unsuccessfull creating of a new message. Testing that text cannot be null."""

        with self.assertRaises(IntegrityError):
            fail_msg = Message(text=None)
            self.u2.messages.append(fail_msg)

            db.session.commit()

    def test_like_message(self):
        """Tests a user being able to like a message."""

        self.u1.likes.append(self.m2)

        db.session.commit()

        self.assertEqual(len(self.u1.likes), 1)

    def test_unlike_message(self):
        """Tests a user being able to unlike a message."""

        self.u1.likes.append(self.m2)
        self.u1.likes.remove(self.m2)

        db.session.commit()

        self.assertEqual(len(self.u1.likes), 0)

