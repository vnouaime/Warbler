"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase
from flask import session
from wtforms import HiddenField

from models import db, connect_db, Message, User
from forms import UserAddForm, LoginForm, UserEditForm

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app, CURR_USER_KEY

db.create_all()

app.config['WTF_CSRF_ENABLED'] = False

class UserViewTestCase(TestCase):
    """Test views for users."""

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
        self.message2 = Message(text="Test Message 2 User 1", user_id=4444)
        self.message2.id = 2346

        self.testuser2 = User.signup(username="testuser2",
                                    email="test2@test2.com",
                                    password="testuser2",
                                    image_url=None)
        self.testuser2.id = 8888
        self.messageuser2 = Message(text="Test Message User 2", user_id=8888)
        self.messageuser2.id = 4233
        self.message2user2 = Message(text="Test Message 2 User 2", user_id=8888)
        self.message2user2.id = 4234

        self.testuser.following.append(self.testuser2)
        self.testuser2.following.append(self.testuser)

        self.testuser.likes.append(self.messageuser2)
        self.testuser.likes.append(self.message2user2)

        db.session.add(self.testuser)
        db.session.add(self.message)
        db.session.add(self.message2) 
        db.session.add(self.testuser2) 
        db.session.add(self.messageuser2)
        db.session.add(self.message2user2)
        
        db.session.commit()

    # Added tearDown function which should be included in each test case
    def tearDown(self): 
        """ Closes current session of database """ 
        res = super().tearDown()
        db.drop_all()
        db.session.close()
        return res

    ###################################################################################
    # Tests for user signup/login/logout 
    def test_user_signup_get(self):
        """Tests get request of signup route of new user."""

        with self.client as c:
            
            response = c.get("/signup")
            html = response.get_data(as_text=True)
            form = UserAddForm()

            self.assertEqual(response.status_code, 200)
            self.assertIn('<h2 class="join-message">Join Warbler today.</h2>', html)

            for field in form: 
                if not isinstance(field, HiddenField):
                    self.assertIn(f'{field(placeholder=field.label.text, class_="form-control")}', html)

    def test_user_signup_post(self):
        """Tests post request of signup route of creating a new user."""

        with self.client as c:
            
            data = {
                "username": "test123",
                "password": "testingtesting", 
                "email": "testingtesting@gmail.com",
                "image_url": None
            }

            response = c.post("/signup", data=data, follow_redirects=True)
            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(session[CURR_USER_KEY], 1)
            self.assertIn('<img src="/static/images/default-pic.png"\n                 alt="Image for test123"\n                 class="card-image">\n', html)
            self.assertIn('<p>@test123</p>', html)

    def test_invalid_signup_post(self):
        """Tests invalid post request of signup route by trying to create a non unique username."""

        with self.client as c:
            
            data = {
                "username": "testuser",
                "password": "testingtesting", 
                "email": "testingtesting@gmail.com",
                "image_url": None
            }

            response = c.post("/signup", data=data, follow_redirects=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('Username already taken'.encode(), response.data)

    def test_user_login_get(self):
        """Tests get request of user login route."""

        with self.client as c:

            response = c.get("/login")
            html = response.get_data(as_text=True)
            form = LoginForm()

            self.assertEqual(response.status_code, 200)

            for field in form: 
                if not isinstance(field, HiddenField):
                    self.assertIn(f'{field(placeholder=field.label.text, class_="form-control")}', html)

    def test_user_login_post(self):
        """Tests post request of login route."""

        with self.client as c:

            data = {
                "username": self.testuser.username,
                "password": "testuser"
            }
            
            response = c.post("/login", data=data, follow_redirects=True)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(session[CURR_USER_KEY], 4444)
            self.assertIn('Hello, testuser!'.encode(), response.data)

    def test_invalid_login_post(self):
        """Tests invalid post request of login route with invalid password."""

        with self.client as c:

            data = {
                "username": self.testuser.username,
                "password": "invalidpassword"
            }

            response = c.post("/login", data=data, follow_redirects=True)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(session), 0)
            self.assertIn('Invalid credentials.'.encode(), response.data)

    def test_user_logout(self):
        """Tests request for user to logout."""

        with self.client as c: 
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            response = c.get("/logout", follow_redirects=True)
            html = response.get_data(as_text=True)
            form = LoginForm()

            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(session), 0)
            self.assertIn('Logout successful!'.encode(), response.data)

            for field in form: 
                if not isinstance(field, HiddenField):
                    self.assertIn(f'{field(placeholder=field.label.text, class_="form-control")}', html)
            
    def test_fail_user_logout(self):
        """Tests failed request of logging out when there is not currently a user in the session."""

        with self.client as c:

            response = c.get("/logout", follow_redirects=True)
            html = response.get_data(as_text=True)
            form = LoginForm()

            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(session), 0)
            self.assertIn('You are not logged in.'.encode(), response.data)

            for field in form: 
                if not isinstance(field, HiddenField):
                    self.assertIn(f'{field(placeholder=field.label.text, class_="form-control")}', html)

    ###################################################################################
    # Tests for User routes

    def test_list_users(self):
        """Tests get request for all users page."""

        with self.client as c:

            response = c.get("/users")
            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('<img src="/static/images/default-pic.png" alt="Image for testuser" class="card-image">', html)
            self.assertIn('<p>@testuser</p>', html)

    def test_users_show(self):
        """Tests individual user page."""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            response = c.get(f"/users/{self.testuser.id}")
            html = response.get_data(as_text=True)

            messages = (Message
                .query
                .filter(Message.user_id == self.testuser.id)
                .order_by(Message.timestamp.desc())
                .limit(100)
                .all()
            )

            self.assertEqual(response.status_code, 200)
            self.assertIn('<img src="/static/images/default-pic.png" alt="Image for testuser"', html)

            for message in messages:
                self.assertIn(f'<a href="/users/{self.testuser.id}">@{self.testuser.username}</a>', html)
                self.assertIn(f'<p>{message.text}</p>', html)
    
    def test_show_following(self):
        """Tests showing list people that user is following."""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            response = c.get(f"/users/{self.testuser.id}/following")
            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('<img src="/static/images/default-pic.png" alt="Image for testuser2" class="card-image">', html)
            self.assertIn('<p>@testuser2</p>', html)
            self.assertIn('<button class="btn btn-primary btn-sm">Unfollow</button>', html)

    def test_no_session_show_following(self):
        """Tests that user cannot gain access if not logged in."""

        with self.client as c:

            response = c.get(f"/users/{self.testuser.id}/following", follow_redirects=True)
            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('Access unauthorized.'.encode(), response.data)
            self.assertIn('<h4>New to Warbler?</h4>', html)
            self.assertIn('<p>Sign up now to get your own personalized timeline!</p>', html)
            self.assertIn('<a href="/signup" class="btn btn-primary">Sign up</a>', html)

    def test_users_followers(self):
        """Tests showing list of people that are following user."""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            response = c.get(f"/users/{self.testuser.id}/followers")
            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('<img src="/static/images/default-pic.png" alt="Image for testuser2" class="card-image">', html)
            self.assertIn('<p>@testuser2</p>', html)
            self.assertIn('<button class="btn btn-primary btn-sm">Unfollow</button>', html)

    def test_no_session_users_followers(self):
        """Tests that user cannot gain access if not logged in."""

        with self.client as c:

            response = c.get(f"/users/{self.testuser.id}/followers", follow_redirects=True)
            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('Access unauthorized.'.encode(), response.data)
            self.assertIn('<h4>New to Warbler?</h4>', html)
            self.assertIn('<p>Sign up now to get your own personalized timeline!</p>', html)
            self.assertIn('<a href="/signup" class="btn btn-primary">Sign up</a>', html)

    def test_add_follow(self):
        """Tests adding a follower to currently logged in user."""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            new_user = User.signup(username="tofollowuser", 
            password="tofollow", 
            email="tofollow@gmail.com",
            image_url=None)
            new_user.id = 2222
            
            db.session.add(new_user)
            db.session.commit()

            response = c.post(f"/users/follow/{new_user.id}", follow_redirects=True)
            html = response.get_data(as_text=True)

            self.testuser = User.query.get(self.testuser.id)
            
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(self.testuser.following), 2)
            
            for following in self.testuser.following:
                self.assertIn(f'<img src="/static/images/default-pic.png" alt="Image for {following.username}" class="card-image">', html)
                self.assertIn(f'<p>@{following.username}</p>', html)
                self.assertIn('<button class="btn btn-primary btn-sm">Unfollow</button>', html)

    def test_no_session_add_follow(self):
        """Tests to not allow user to follow someone else if not logged in."""

        with self.client as c:

            new_user = User.signup(username="tofollowuser", 
            password="tofollow", 
            email="tofollow@gmail.com",
            image_url=None)
            new_user.id = 2222
            
            db.session.add(new_user)
            db.session.commit()

            response = c.post(f"/users/follow/{new_user.id}", follow_redirects=True)
            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('Access unauthorized.'.encode(), response.data)
            self.assertIn('<h4>New to Warbler?</h4>', html)
            self.assertIn('<p>Sign up now to get your own personalized timeline!</p>', html)
            self.assertIn('<a href="/signup" class="btn btn-primary">Sign up</a>', html)

    def test_invalid_add_follow(self):
        """Tests to not allow user to follow themselves."""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            response = c.post(f"/users/follow/{self.testuser.id}", follow_redirects=True)
            html = response.get_data(as_text=True)

            messages = (Message
                .query
                .filter(Message.user_id == self.testuser.id)
                .order_by(Message.timestamp.desc())
                .limit(100)
                .all()
            )

            self.assertEqual(response.status_code, 200)
            self.assertIn('Action Not Allowed.'.encode(), response.data)

            for message in messages:
                self.assertIn(f'<a href="/users/{self.testuser.id}">@{self.testuser.username}</a>', html)
                self.assertIn(f'<p>{message.text}</p>', html)

    def test_stop_following(self):
        """Tests unfollowing to currently logged in user."""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            response = c.post("/users/stop-following/8888", follow_redirects=True)
            html = response.get_data(as_text=True)
            
            self.testuser = User.query.get(self.testuser.id)
            
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(self.testuser.following), 0)
            self.assertIn('<img src="/static/images/default-pic.png" alt="Image for testuser" id="profile-avatar">', html)
            self.assertIn('<h4 id="sidebar-username">@testuser</h4>', html)
            

    def test_no_session_stop_following(self):
        """Tests to not allow user to stop following someone else if not logged in."""

        with self.client as c:

            response = c.post(f"/users/stop-following/8888", follow_redirects=True)
            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('Access unauthorized.'.encode(), response.data)
            self.assertIn('<h4>New to Warbler?</h4>', html)
            self.assertIn('<p>Sign up now to get your own personalized timeline!</p>', html)
            self.assertIn('<a href="/signup" class="btn btn-primary">Sign up</a>', html)

    def test_users_profile_get(self):
        """Tests get request of editing user form."""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            response = c.get("/users/profile")
            html = response.get_data(as_text=True)

            self.testuser = User.query.get(self.testuser.id)
            form = UserEditForm(obj=self.testuser)

            self.assertEqual(response.status_code, 200)

            for field in form: 
                if not isinstance(field, HiddenField) and field.name != "password":
                    self.assertIn(f'{field(placeholder=field.label.text, class_="form-control")}', html)
                elif field.name == "password":
                    self.assertIn(f'{form.password(placeholder="Enter your password to confirm", class_="form-control")}', html)

    def test_no_session_users_profile_get(self):
        """Tests that user that is not logged in has no access to view form."""

        with self.client as c:

            response = c.get("/users/profile", follow_redirects=True)
            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('Access unauthorized.'.encode(), response.data)
            self.assertIn('<h4>New to Warbler?</h4>', html)
            self.assertIn('<p>Sign up now to get your own personalized timeline!</p>', html)
            self.assertIn('<a href="/signup" class="btn btn-primary">Sign up</a>', html)

    def test_users_profile_post(self):
        """Tests post request of editing user route."""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            data = {
                "username": "TestChangeUsername",
                "email": "test@test.com", 
                "image_url": "/static/images/default-pic.png",
                "header_image_url": "/static/images/warbler-hero.jpg", 
                "password": "testuser"
            }

            response = c.post("/users/profile", data=data, follow_redirects=True)
            html = response.get_data(as_text=True)

            self.testuser = User.query.get(self.testuser.id)
            messages = (Message
                .query
                .filter(Message.user_id == self.testuser.id)
                .order_by(Message.timestamp.desc())
                .limit(100)
                .all()
            )

            self.assertEqual(response.status_code, 200)
            self.assertIn('<img src="/static/images/default-pic.png" alt="TestChangeUsername"', html)

            for message in messages:
                self.assertIn(f'<a href="/users/{self.testuser.id}">@{self.testuser.username}</a>', html)
                self.assertIn(f'<p>{message.text}</p>', html)

    def test_invalid_password_profile_post(self):
        """Tests invalid post request when user that is logged in does not give the correct password."""

        with self.client as c: 
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            data = {
                "username": "TestChangeUsername",
                "email": "test@test.com", 
                "image_url": "/static/images/default-pic.png",
                "header_image_url": "/static/images/warbler-hero.jpg", 
                "password": "incorrectpassword"
            }

            response = c.post("/users/profile", data=data, follow_redirects=True)
            html = response.get_data(as_text=True)

            messages = (Message
                .query
                .filter(Message.user_id == self.testuser.id)
                .order_by(Message.timestamp.desc())
                .limit(100)
                .all()
            )

            self.assertEqual(response.status_code, 200)
            self.assertIn('Invalid Password'.encode(), response.data)

            for message in messages:
                self.assertIn(f'<a href="/users/{self.testuser.id}">@{self.testuser.username}</a>', html)
                self.assertIn(f'<p>{message.text}</p>', html)

    def test_form_error_profile_post(self):
        """Tests invalid post request when user attempts to fill in field that has to be unique."""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            data = {
                "username": "testuser2",
                "email": "test@test.com", 
                "image_url": "/static/images/default-pic.png",
                "header_image_url": "/static/images/warbler-hero.jpg", 
                "password": "testuser"
            }

            response = c.post("/users/profile", data=data, follow_redirects=True)
            html = response.get_data(as_text=True)
            form = UserEditForm(obj=self.testuser)

            self.assertEqual(response.status_code, 200)

            for field in form: 
                if not isinstance(field, HiddenField) and field.name != "password":
                    self.assertIn(f'{field(placeholder=field.label.text, class_="form-control")}', html)
                elif field.name == "password":
                    self.assertIn(f'{form.password(placeholder="Enter your password to confirm", class_="form-control")}', html)

                for error in field.errors:
                    self.assertIn(f'<span class="text-danger">{error}</span>', html)

    def test_no_session_user_profile_post(self):
        """Tests that user cannot make a post request when not logged in."""

        with self.client as c:

            data = {
                "username": "TestChangeUsername",
                "email": "test@test.com", 
                "image_url": "/static/images/default-pic.png",
                "header_image_url": "/static/images/warbler-hero.jpg", 
                "password": "testuser"
            }

            response = c.post("/users/profile", data=data, follow_redirects=True)
            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('Access unauthorized.'.encode(), response.data)
            self.assertIn('<h4>New to Warbler?</h4>', html)
            self.assertIn('<p>Sign up now to get your own personalized timeline!</p>', html)
            self.assertIn('<a href="/signup" class="btn btn-primary">Sign up</a>', html)

    def test_delete_user(self):
        """Tests deletion of user logged in and redirects to signup page. Have already tested signup page HTML."""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            response = c.post("/users/delete")

            self.assertEqual(response.status_code, 302)

    def test_no_session_delete_user(self):
        """Tests response to deletion of user when there is no user logged in."""

        with self.client as c:

            response = c.post("/users/delete", follow_redirects=True)
            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('Access unauthorized.'.encode(), response.data)
            self.assertIn('<h4>New to Warbler?</h4>', html)
            self.assertIn('<p>Sign up now to get your own personalized timeline!</p>', html)
            self.assertIn('<a href="/signup" class="btn btn-primary">Sign up</a>', html)

    def test_user_show_likes(self):
        """Tests request to show all likes of user."""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            response = c.get(f"/users/{self.testuser.id}/likes")
            html = response.get_data(as_text=True)

            self.testuser = User.query.get(self.testuser.id)

            self.assertEqual(response.status_code, 200) 
           
            for msg in self.testuser.likes:
                self.assertIn(f'<a href="/messages/{msg.id}" class="message-link">', html)
                self.assertIn(f'<a href="/users/{msg.user_id}">', html)
                self.assertIn(f'<img src="{msg.user.image_url}" alt="" class="timeline-image">', html)
                self.assertIn(f'<p>{msg.text}</p>', html)

    def test_no_session_show_likes(self):
        """Tests invalid request to show all likes of user when there is no logged in user."""

        with self.client as c:

            response = c.get(f"/users/{self.testuser.id}/likes", follow_redirects=True)
            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('Access unauthorized.'.encode(), response.data)
            self.assertIn('<h4>New to Warbler?</h4>', html)
            self.assertIn('<p>Sign up now to get your own personalized timeline!</p>', html)
            self.assertIn('<a href="/signup" class="btn btn-primary">Sign up</a>', html)

    def test_user_add_like(self):
        """Tests post request to add a message to likes for user. Redirects to likes page of user. Already tested get request of like page for user."""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            new_message = Message(text="MessageTest", user_id=8888)
            new_message.id = 3334
            
            db.session.add(new_message)
            db.session.commit()

            response = c.post(f"/messages/{new_message.id}/like")

            self.assertEqual(response.status_code, 302)

    def test_user_remove_like(self):
        """Tests post request to remove a liked message for user. Redirects to home page. Already tested home route for logged in user."""

        with self.client as c: 
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            new_message = Message(text="MessageTest", user_id=8888)
            new_message.id = 3334

            self.testuser = User.query.get(self.testuser.id)
            self.testuser.likes.append(new_message)

            db.session.add(new_message)
            db.session.commit()

            response = c.post(f"/messages/{new_message.id}/like")

            self.assertEqual(response.status_code, 302)

    def test_invalid_user_add_like(self):
        """Tests invalid post request when user that is logged in tries adding or removing a like on their own message."""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            response = c.post("/messages/2345/like", follow_redirects=True)
            html = response.get_data(as_text=True)

            messages = (Message
                .query
                .filter(Message.user_id == self.testuser.id)
                .order_by(Message.timestamp.desc())
                .limit(100)
                .all()
            )

            self.assertEqual(response.status_code, 200)
            self.assertIn('Action not allowed.'.encode(), response.data)

            for message in messages:
                self.assertIn(f'<a href="/users/{self.testuser.id}">@{self.testuser.username}</a>', html)
                self.assertIn(f'<p>{message.text}</p>', html)

    def test_no_session_user_add_like(self):
        """Tests invalid post request of user trying to add or unlike a message when not logged in."""

        with self.client as c:

            new_message = Message(text="MessageTest", user_id=8888)
            new_message.id = 3334
            
            db.session.add(new_message)
            db.session.commit()

            response = c.post(f"/messages/{new_message.id}/like", follow_redirects=True)
            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('Access unauthorized'.encode(), response.data)
            self.assertIn('<h4>New to Warbler?</h4>', html)
            self.assertIn('<p>Sign up now to get your own personalized timeline!</p>', html)
            self.assertIn('<a href="/signup" class="btn btn-primary">Sign up</a>', html)
