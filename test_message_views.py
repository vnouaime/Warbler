"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User
from forms import MessageForm

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        db.create_all()
        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        self.testuser.id = 4444
        self.message = Message(text="Test Message", user_id=4444)
        self.message.id = 2345

        db.session.add(self.testuser)
        db.session.add(self.message)
        db.session.commit()

    # Added tearDown function which should be included in each test case
    def tearDown(self): 
        """ Closes current session of database """ 
        res = super().tearDown()
        db.drop_all()
        db.session.close()
        return res

    def test_add_message(self):
        """Can use add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            # UPDATE: Added follow_redirect=True to get proper html response
            resp = c.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)
            html = resp.get_data(as_text=True)

            # Make sure it redirects
            # UPDATE: updated to response code of 200 since we set follow_redirects = True
            self.assertEqual(resp.status_code, 200)

            # UPDATE: updated because I added a message in set up method. msg.id number changed.
            msg = Message.query.get(1)
           
            self.assertEqual(msg.text, "Hello")
            
            self.assertIn(f'<a href="/users/{msg.user_id}">@testuser</a>', html)
            self.assertIn('<p>Hello</p>', html)
    
    def test_messages_add_get(self):
        """Testing get request of add message form"""

        with self.client as c: 
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
        
            response = c.get("/messages/new")
            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('<textarea class="form-control" id="text" name="text" placeholder="What is happening?" required rows="3"></textarea>', html)

           
    def test_no_session_add_message(self):
        """Tests to see if message can be added when user is not logged in"""

        with self.client as c: 
            resp = c.post("/messages/new", data={"text": "TEST"}, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<div class="alert alert-danger">Access unauthorized.</div>', html)

    def test_invalid_user_add_message(self):
        """Tests to see if message can be added for a user by an invalid user."""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 985588

            resp = c.post("/messages/new", data={"text": "TEST"}, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<div class="alert alert-danger">Access unauthorized.</div>', html)
            

    def test_message_show(self):
        """Tests to see if message shows up."""

        with self.client as c: 

            response = c.get(f"/messages/{self.message.id}")
            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn(f'<a href="/users/{self.message.user_id}">@testuser</a>', html)
            self.assertIn('<p class="single-message">Test Message</p>', html)

    def test_message_delete(self):
        """Tests to see if message is deleted when user is logged in."""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            msg = Message(text="a Test", user_id=4444)
            
            db.session.add(msg)
            db.session.commit()

            response = c.post(f"/messages/{msg.id}/delete", follow_redirects=True)
            
            self.assertEqual(response.status_code, 200)
            self.assertNotIn("a Test", str(response.data))
            self.assertEqual(len(Message.query.all()), 1)

    def test_no_session_message_delete(self):
        """Tests to see if message is not deleted when user is not logged in."""

        with self.client as c:

            msg = Message(text="a Test", user_id=4444)
            
            db.session.add(msg)
            db.session.commit()

            response = c.post(f"/messages/{msg.id}/delete", follow_redirects=True)
            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('<div class="alert alert-danger">Access unauthorized.</div>', html)

    def test_unauthorized_message_delete(self):
        """Tests to see if message is not deleted when user in session tries to delete another user's message."""

        user = User.signup(username="unauthorized-user",
                        email="testtest@test.com",
                        password="notallowed",
                        image_url=None)
        user.id = 8766

        msg = Message(
            id=1234,
            text="a test message",
            user_id=self.testuser.id
        )
        db.session.add_all([user, msg])
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 8766

            response = c.post("/messages/1234/delete", follow_redirects=True)
            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('<div class="alert alert-danger">Access unauthorized.</div>', html)

            m = Message.query.get(1234)
            self.assertIsNotNone(m)
            
            
            

            

