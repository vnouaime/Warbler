"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy.exc import IntegrityError

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test cases for User model."""

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

        self.u1 = u1
        self.u2 = u2

        self.client = app.test_client()

    # Added tearDown function which should be included in each test case
    def tearDown(self): 
        """ Closes current session of database """ 
        res = super().tearDown()
        db.session.close()
        return res

    ##################################################################################
    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    def test_user_repr(self):
        """Tests repr method of User model."""
        
        repr_output = repr(self.u1)

        self.assertEqual(repr_output, "<User #1: test123, email1@gmail.com>")

    ##################################################################################    
    # Following Tests
    def test_is_following(self):
        """Tests is_following method from User."""

        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertTrue(self.u1.is_following(self.u2))
        self.assertFalse(self.u2.is_following(self.u1))

    def test_is_followed_by(self):
        """Tests is_followed_by method from User.""" 

        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertTrue(self.u2.is_followed_by(self.u1))
        self.assertFalse(self.u1.is_followed_by(self.u2)) 

    ##################################################################################    
    # Signup Tests
    def test_signup(self):
        """Tests signup method to create new user."""

        new_user = User.signup(username="testing123", email="testing123@gmail.com", password="testing123456", image_url=None)

        db.session.add(new_user)
        db.session.commit()

        self.assertEqual(repr(new_user), "<User #3: testing123, testing123@gmail.com>")

    def test_fail_duplicate_signup(self):
        """Tests signup method when creating user fails. Testing duplicate value error."""
        
        with self.assertRaises(IntegrityError):
            fail_user = User.signup(username="test123", email="sdjfldsa@gmail.com", password="hello123", image_url=None)

            db.session.add(fail_user)
            db.session.commit()
       
    def test_fail_empty_signup(self):
        """Test signup method when creating user fails. Testing null value error."""

        with self.assertRaises(IntegrityError):
            fail_user_2 = User.signup(username="testing456", email=None, password="hello123", image_url=None)

            db.session.add(fail_user_2)
            db.session.commit()

    ##################################################################################    
    # Authenticate Tests
    def test_success_authenticate(self):
        """Tests successfull authentication of user with authenticate class method."""

        u = User.authenticate(username="test123", password="test456")
        
        db.session.commit()

        self.assertEqual(repr(u), "<User #1: test123, email1@gmail.com>")

    def test_fail_username_authenticate(self):
        """Tests unsuccessfull authenitcation of incorrect username with authenticate class method."""

        fail_user = User.authenticate(username="test789", password="test456")

        db.session.commit()

        self.assertFalse(fail_user)

    def test_fail_password_authenticate(self):
        """Tests unsuccessfull authentication of incorrect password with authenticate class method."""

        fail_user = User.authenticate(username="test123", password="incorrectpassword")

        db.session.commit()

        self.assertFalse(fail_user)
            












# print("######################################################################")
# print(new_user)
# print("######################################################################")