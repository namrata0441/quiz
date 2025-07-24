import sys
from PyQt5 import QtCore, QtGui, QtWidgets
import requests

# Import your UI classes from their respective files
from register_form import RegisterUi_Form
from dashboard_form import Ui_MainWindow  # This should be the UI setup class
from login_form import LoginUi_Form  # Correctly import LoginUi_Form from your login_form.py


# Removed: from profile_form import ProfileFormWindow # ProfileWidget is now nested in dashboard_form

class MainApplicationWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MindZap Application")
        self.setGeometry(100, 100, 800, 600)

        self.stacked_widget = QtWidgets.QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self.current_username = None  # To store the username (email) of the logged-in user

        self.init_pages()
        self.init_connections()
        self.show_login_page()  # Start with the login page

    def init_pages(self):
        """Initializes all UI pages and adds them to the stacked widget."""
        # Login Page
        self.login_page = LoginUi_Form()
        self.stacked_widget.addWidget(self.login_page)

        # Registration Page
        self.register_page = RegisterUi_Form()
        self.stacked_widget.addWidget(self.register_page)

        # Dashboard Page
        # Ui_MainWindow is a UI setup class, not a QWidget itself.
        # We need a QMainWindow instance to apply the UI to.
        self.dashboard_window = QtWidgets.QMainWindow()
        self.dashboard_ui = Ui_MainWindow()  # Instantiate the UI setup class
        self.dashboard_ui.setupUi(self.dashboard_window)  # Apply the UI to the QMainWindow
        self.stacked_widget.addWidget(self.dashboard_window)  # Add the QMainWindow to the stacked widget

        # Profile Page is now part of dashboard_ui.stackedWidget (at index 1)
        # Access it via self.dashboard_ui.page_7 (which is an instance of ProfileWidget)
        self.profile_page_widget = self.dashboard_ui.page_7  # Reference to the ProfileWidget instance

    def init_connections(self):
        """Sets up all signal-slot connections for navigation and data flow."""
        # Login Page Connections
        self.login_page.login_successful_signal.connect(self._handle_login_attempt)
        self.login_page.switch_to_register_signal.connect(self.show_register_page)

        # Registration Page Connections
        self.register_page.registration_successful_signal.connect(self.show_login_page)
        self.register_page.switch_to_login_signal.connect(self.show_login_page)

        # Dashboard Page Connections
        # The user_btn in dashboard_ui is already connected to switch to index 1 (Profile Page)
        # within dashboard_form.py itself.
        # We need to connect the ProfileWidget's signals to MainApplicationWindow.
        self.profile_page_widget.logout_requested.connect(self.show_login_page)
        self.profile_page_widget.profile_updated.connect(self._handle_profile_updated)

        # Connect the user_btn from the dashboard_ui to the show_profile_page method in MainApplicationWindow
        # This ensures that when the user clicks the profile icon, data is fetched.
        if hasattr(self.dashboard_ui, 'user_btn'):
            self.dashboard_ui.user_btn.clicked.connect(self.show_profile_page)
        else:
            print("Warning: 'user_btn' not found in dashboard_ui. Profile page navigation might not work.")

        # Search button on dashboard (already handled in dashboard_form.py to switch to page_6)
        # If you need to pass the search query to the search page, you'd do it here:
        # self.dashboard_ui.search_btn.clicked.connect(lambda: self.dashboard_ui.stackedWidget.setCurrentIndex(6))

        # CRITICAL FIX: Connect settings buttons to switch to the settings page (index 5)
        # Since these buttons are now checkable and auto-exclusive, connect their toggled signal.
        if hasattr(self.dashboard_ui, 'setting_1'):
            self.dashboard_ui.setting_1.toggled['bool'].connect(
                lambda checked: self.dashboard_ui.stackedWidget.setCurrentIndex(5) if checked else None)
        else:
            print("Warning: 'setting_1' button not found in dashboard_ui.")

        if hasattr(self.dashboard_ui, 'setting_2'):
            self.dashboard_ui.setting_2.toggled['bool'].connect(
                lambda checked: self.dashboard_ui.stackedWidget.setCurrentIndex(5) if checked else None)
        else:
            print("Warning: 'setting_2' button not found in dashboard_ui.")

    def _handle_login_attempt(self, username, password):
        """
        Handles the login attempt by making a request to the backend.
        This method is connected to login_page.login_successful_signal.
        """
        backend_url = "http://127.0.0.1:5000/login"
        login_data = {
            "username": username,  # This is the email
            "password": password
        }

        print(f"Frontend Debug (MainApp - Login): Sending data to backend: {login_data}")

        response = None  # Initialize response to None to prevent "might be referenced before assignment" error
        try:
            response = requests.post(backend_url, json=login_data)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

            response_data = response.json()
            print(f"Frontend Debug (MainApp - Login): Received response: {response_data}")

            if response.status_code == 200:  # HTTP 200 OK for successful login
                QtWidgets.QMessageBox.information(self, "Login Success",
                                                  response_data.get("message", "Login successful!"))
                self.login_page.clear_fields()  # Clear login fields on success
                self.current_username = response_data.get("username", username)  # Store username (email)
                self.show_dashboard_page(self.current_username)  # Pass username to dashboard
            else:
                QtWidgets.QMessageBox.warning(self, "Login Failed",
                                              response_data.get("message", "An unknown error occurred during login."))

        except requests.exceptions.ConnectionError:
            QtWidgets.QMessageBox.critical(self, "Connection Error",
                                           "Could not connect to the backend server. Please ensure Flask app is running.")
        except requests.exceptions.HTTPError as e:
            error_message = f"Backend returned an error: {e.response.status_code}"
            try:
                # Ensure response is not None before trying to parse JSON
                if response:
                    error_json = response.json()
                    error_message += f" - {error_json.get('message', response.text)}"
                else:
                    error_message += f" - No response received."
            except requests.exceptions.JSONDecodeError:
                if response:
                    error_message += f" - {response.text}"  # Fallback to raw text if not JSON
                else:
                    error_message += f" - No response received."
            QtWidgets.QMessageBox.critical(self, "Server Error", error_message)
        except requests.exceptions.JSONDecodeError as e:
            # This catches cases where the backend response is not valid JSON
            QtWidgets.QMessageBox.critical(self, "Response Error",
                                           f"Failed to parse server response as JSON. Error: {e}. Raw Response: '{response.text if response else 'No response'}'")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Unexpected Error", f"An unexpected error occurred during login: {e}")

    def _fetch_profile_data(self, username):
        """Fetches user profile data from the backend."""
        if not username:
            print("Error: No username available to fetch profile.")
            return None

        backend_url = f"http://127.0.0.1:5000/profile/{username}"
        response = None  # Initialize response to None to prevent "might be referenced before assignment" error
        try:
            response = requests.get(backend_url)
            response.raise_for_status()
            profile_data = response.json()
            print(f"Frontend Debug (MainApp - Profile Fetch): Fetched profile: {profile_data}")
            return profile_data
        except requests.exceptions.ConnectionError:
            QtWidgets.QMessageBox.critical(self, "Connection Error", "Could not connect to backend to fetch profile.")
        except requests.exceptions.HTTPError as e:
            error_message = f"Backend returned an error: {e.response.status_code}"
            try:
                # Ensure response is not None before trying to parse JSON
                if response:
                    error_json = response.json()
                    error_message += f" - {error_json.get('message', response.text)}"
                else:
                    error_message += f" - No response received."
            except requests.exceptions.JSONDecodeError:
                if response:
                    error_message += f" - {response.text}"  # Fallback to raw text if not JSON
                else:
                    error_message += f" - No response received."
            QtWidgets.QMessageBox.critical(self, "Server Error", error_message)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Unexpected Error",
                                           f"An unexpected error occurred fetching profile: {e}")
        return None

    def _handle_profile_updated(
            self):  # Removed 'updated_data' as parameter, ProfileWidget handles its own data loading after update.
        """
        Handles the signal emitted when profile data is updated in ProfileWidget.
        Re-fetches profile data to ensure dashboard and profile page are in sync
        if the username (email) was updated.
        """
        print("Frontend Debug (MainApp): Profile updated signal received.")
        if self.current_username:
            # Re-fetch profile data to ensure consistency, especially if email changed.
            updated_profile_data = self._fetch_profile_data(self.current_username)
            if updated_profile_data:
                # Update the profile_page_widget with the latest data
                self.profile_page_widget.load_profile_data(updated_profile_data)
                # Also ensure the dashboard's username display is updated if needed
                self.dashboard_ui.set_username_display(updated_profile_data.get('username', self.current_username))
                # Update the stored current_username in MainApplicationWindow if it changed
                self.current_username = updated_profile_data.get('username', self.current_username)
                self.setWindowTitle(f"MindZap - Dashboard ({self.current_username})")
            else:
                QtWidgets.QMessageBox.warning(self, "Profile Sync Error", "Could not re-fetch updated profile data.")

    def show_login_page(self):
        self.stacked_widget.setCurrentWidget(self.login_page)
        self.setWindowTitle("MindZap - Login")
        self.current_username = None  # Clear username on logout/return to login
        print("Switched to Login Page")

    def show_register_page(self):
        self.stacked_widget.setCurrentWidget(self.register_page)
        self.setWindowTitle("MindZap - Register")
        print("Switched to Register Page")

    def show_dashboard_page(self, username):
        # Ensure set_username_display exists and is called correctly.
        if hasattr(self.dashboard_ui, 'set_username_display'):
            self.dashboard_ui.set_username_display(username)  # Update username on dashboard
        else:
            print("Warning: 'set_username_display' method not found in dashboard_ui. Username might not display.")

        self.stacked_widget.setCurrentWidget(self.dashboard_window)
        self.setWindowTitle(f"MindZap - Dashboard ({username})")
        print(f"Switched to Dashboard Page for user: {username}")

    def show_profile_page(self):
        """
        This method is called when the user clicks the profile button on the dashboard.
        It fetches the profile data and loads it into the ProfileWidget.
        """
        if self.current_username:
            profile_data = self._fetch_profile_data(self.current_username)
            if profile_data:
                # Load data into the ProfileWidget instance (self.dashboard_ui.page_7)
                self.profile_page_widget.load_profile_data(profile_data)
                # Tell the dashboard's stackedWidget to show the profile page
                self.dashboard_ui.stackedWidget.setCurrentIndex(1)  # Index 1 is the Profile Page (self.page_7)
                self.setWindowTitle(f"MindZap - Profile ({self.current_username})")
                print(f"Switched to Profile Page for user: {self.current_username}")
            else:
                QtWidgets.QMessageBox.warning(self, "Profile Error", "Could not load profile data.")
        else:
            QtWidgets.QMessageBox.warning(self, "Profile Error", "No user logged in to view profile.")
            self.show_login_page()  # Redirect to login if no user is logged in


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    main_app = MainApplicationWindow()
    main_app.show()
    sys.exit(app.exec_())
